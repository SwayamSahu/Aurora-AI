"""CUDA video editor — real models, activated only when GENERATOR_BACKEND=cuda.

Runs on the NVIDIA 16 GB box (Phase 9 / E5). Like the other CUDA generators,
every heavy import (torch, diffusers, realesrgan) is lazy, so this module is
importable on a CPU-only Mac without error and is exercised for real only on
the GPU box.

Engine → model mapping:
  inpaint-remove  → Stable Diffusion inpainting, per-frame, mask-guided
                    (removes the masked region and reconstructs the background)
  masked-v2v      → SD img2img per frame, prompt-guided, composited back
                    through the mask (replace/recolor/restyle the region)
  global-restyle  → SD img2img per frame, full-frame (style/relight the shot)
  enhance         → Real-ESRGAN per-frame upscale/restore

The per-frame SD baseline is a *runnable* real implementation. Temporal
coherence can be upgraded to Wan 2.1 VACE / AnimateDiff during Phase 9 tuning
without changing this contract or the frontend.

Non-generative engines need no GPU and are delegated to the shared FFmpeg /
Tesseract implementation (identical output on any backend):
  retime-camera            → FFmpeg (speed/reverse/loop/stabilize/pan/zoom/…)
  global-restyle GRADE_*   → FFmpeg color grade (lighting / time / season)
  text-ops  text-detect    → Tesseract OCR overlay
"""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from app.generators.base import (
    GeneratedMedia,
    ProgressCallback,
    VideoEditor,
    VideoEditParams,
    _noop_progress,
)
from app.generators.cuda.vram import acquire_pipeline
from app.generators.mock.editor import GRADE_RECIPES, MockVideoEditor

logger = logging.getLogger(__name__)

_HF_HOME = os.environ.get("HF_HOME", "/models/hf")

# Model choices tuned for the 16 GB card (SD-1.5 class keeps peak VRAM low).
_INPAINT_MODEL = "runwayml/stable-diffusion-inpainting"
_IMG2IMG_MODEL = "stabilityai/stable-diffusion-2-1"

# Cap frames per edit so a long clip can't run unbounded on a single card.
# Phase-9 tuning may raise this or window long clips with temporal overlap.
_MAX_FRAMES = 240

# Engines handled by real FFmpeg/OCR regardless of backend — delegated.
_DELEGATED_ENGINES = {"retime-camera", "segment-track"}


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "ffmpeg failed: " + proc.stderr.decode("utf-8", "replace")[-500:]
        )


def _probe_fps(path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=r_frame_rate",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    try:
        num, den = proc.stdout.strip().split("/")
        return float(num) / float(den) if float(den) else 24.0
    except (ValueError, ZeroDivisionError):
        return 24.0


class CudaVideoEditor(VideoEditor):
    """Real AI editing on the GPU box; delegates non-generative engines."""

    name = "cuda-editor"

    def __init__(self) -> None:
        # The FFmpeg/OCR engines are backend-independent — reuse them.
        self._ffmpeg = MockVideoEditor()

    def edit(
        self,
        params: VideoEditParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        # Route non-generative work to the shared FFmpeg/OCR implementation.
        if params.engine in _DELEGATED_ENGINES:
            return self._ffmpeg.edit(params, progress)
        if params.engine == "text-ops":
            return self._ffmpeg.edit(params, progress)
        if params.engine == "global-restyle" and params.preset_id in GRADE_RECIPES:
            return self._ffmpeg.edit(params, progress)

        # Everything else is a real generative edit on the GPU.
        return self._generative_edit(params, progress)

    # ------------------------------------------------------------------ #
    # Real per-frame generative editing
    # ------------------------------------------------------------------ #
    def _generative_edit(
        self, params: VideoEditParams, progress: ProgressCallback
    ) -> GeneratedMedia:
        import torch  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415

        progress(0.05, "loading source")
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            src = d / "src.mp4"
            src.write_bytes(params.source)
            fps = _probe_fps(src)

            frames_dir = d / "frames"
            frames_dir.mkdir()
            _run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(src),
                    str(frames_dir / "f_%05d.png"),
                ]
            )
            frames = sorted(frames_dir.glob("f_*.png"))[:_MAX_FRAMES]
            if not frames:
                raise RuntimeError("No frames extracted from source clip.")

            mask_img = None
            if params.mask:
                mask_path = d / "mask.png"
                mask_path.write_bytes(params.mask)
                mask_img = Image.open(mask_path).convert("L")

            if params.engine == "enhance":
                self._enhance_frames(frames, progress)
            else:
                self._diffuse_frames(params, frames, mask_img, progress, torch, Image)

            out = d / "out.mp4"
            progress(0.9, "encoding")
            _run(
                [
                    "ffmpeg",
                    "-y",
                    "-framerate",
                    str(fps),
                    "-i",
                    str(frames_dir / "f_%05d.png"),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "slow",
                    "-crf",
                    "18",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    str(out),
                ]
            )
            data = out.read_bytes()

        progress(1.0, "done")
        return GeneratedMedia(
            kind="video",
            data=data,
            content_type="video/mp4",
            suggested_filename="edit.mp4",
            meta={
                "backend": self.name,
                "engine": params.engine,
                "preset_id": params.preset_id,
            },
        )

    def _diffuse_frames(self, params, frames, mask_img, progress, torch, Image) -> None:
        """SD inpaint (removal) or img2img (replace/restyle) per frame."""
        is_inpaint = params.engine == "inpaint-remove"
        prompt = params.prompt or ("clean background" if is_inpaint else "")
        negative = params.params.get("negative_prompt") or (
            "blurry, distorted, artifacts, low quality"
        )
        strength = float(params.params.get("strength", 0.75))

        def _loader():
            if is_inpaint:
                from diffusers import (  # noqa: PLC0415
                    StableDiffusionInpaintPipeline,
                )

                pipe = StableDiffusionInpaintPipeline.from_pretrained(
                    _INPAINT_MODEL, torch_dtype=torch.float16, cache_dir=_HF_HOME
                )
            else:
                from diffusers import (  # noqa: PLC0415
                    StableDiffusionImg2ImgPipeline,
                )

                pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                    _IMG2IMG_MODEL, torch_dtype=torch.float16, cache_dir=_HF_HOME
                )
            pipe.enable_model_cpu_offload()
            pipe.set_progress_bar_config(disable=True)
            return pipe

        pipe = acquire_pipeline(f"{self.name}:{params.engine}", _loader)
        generator = torch.Generator("cuda").manual_seed(
            int(params.params.get("seed", 0))
        )

        total = len(frames)
        for i, frame_path in enumerate(frames):
            image = Image.open(frame_path).convert("RGB")
            w, h = image.size
            if is_inpaint and mask_img is not None:
                result = pipe(
                    prompt=prompt,
                    negative_prompt=negative,
                    image=image,
                    mask_image=mask_img.resize((w, h)),
                    num_inference_steps=25,
                    generator=generator,
                ).images[0]
            else:
                edited = (
                    pipe(
                        prompt=prompt,
                        negative_prompt=negative,
                        image=image,
                        strength=strength,
                        num_inference_steps=25,
                        generator=generator,
                    )
                    .images[0]
                    .resize((w, h))
                )
                # Masked v2v: composite the edit back only inside the mask.
                if mask_img is not None:
                    result = Image.composite(edited, image, mask_img.resize((w, h)))
                else:
                    result = edited
            result.save(frame_path)
            progress(0.1 + 0.75 * (i + 1) / total, f"frame {i + 1}/{total}")

    def _enhance_frames(self, frames, progress) -> None:
        """Real-ESRGAN per-frame restoration/upscale."""
        import numpy as np  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415
        from realesrgan import RealESRGANer  # noqa: PLC0415

        def _loader():
            from basicsr.archs.rrdbnet_arch import RRDBNet  # noqa: PLC0415

            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=4,
            )
            return RealESRGANer(
                scale=4,
                model_path=os.path.join(_HF_HOME, "RealESRGAN_x4plus.pth"),
                model=model,
                half=True,
            )

        upscaler = acquire_pipeline(f"{self.name}:enhance", _loader)
        total = len(frames)
        for i, frame_path in enumerate(frames):
            image = np.array(Image.open(frame_path).convert("RGB"))
            output, _ = upscaler.enhance(image, outscale=2)
            Image.fromarray(output).save(frame_path)
            progress(0.1 + 0.75 * (i + 1) / total, f"frame {i + 1}/{total}")
