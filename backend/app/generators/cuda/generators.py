"""CUDA generator implementations — activated only when GENERATOR_BACKEND=cuda.

All GPU-heavy imports (torch, diffusers, transformers) are lazy so this module
can be imported on a CPU-only Mac without error.  Concrete model choices:

  Text → video:   3 local open-weight models, selected by `params.model` (see
                  `CudaVideoGenerator` below) — LTX-Video, CogVideoX-5B, Wan 2.1.
  Image → video:  SVD-XT     (stabilityai/stable-video-diffusion-img2vid-xt, fp16, ~7 GB)
  Text → image:   FLUX.1-dev (black-forest-labs/FLUX.1-dev, bfloat16, cpu-offload, ~10 GB)
  Text → music:   MusicGen   (facebook/musicgen-small, cuda, ~1 GB)

All pipelines are managed by the VRAM singleton (see vram.py) so at most one
diffusion model is resident at a time on the 16 GB box.

Model weights are downloaded to HF_HOME (default /models/hf) on first use, or
pre-fetched via scripts/download_gpu_models.sh.
"""

from __future__ import annotations

import io
import logging
import os
import tempfile
import wave

from app.generators.base import (
    GeneratedMedia,
    ImageGenerator,
    ImageGenParams,
    ImageToVideoGenerator,
    ImageToVideoParams,
    MusicGenerator,
    MusicGenParams,
    ProgressCallback,
    VideoGenerator,
    VideoGenParams,
    _noop_progress,
)
from app.generators.cuda.vram import acquire_pipeline
from app.generators.model_catalog import DEFAULT_MODEL_ID, get_model

logger = logging.getLogger(__name__)

_HF_HOME = os.environ.get("HF_HOME", "/models/hf")


def _causal_frame_count(
    duration_seconds: float, fps: int, *, min_frames: int = 9, temporal_compression: int = 4
) -> int:
    """Frame count satisfying the `(n - 1) % temporal_compression == 0`
    constraint shared by CogVideoX's and Wan's causal 3D VAEs — rounds up to
    the nearest valid count so the decoder's temporal downsampling divides
    the latent evenly. LTX-Video has no such constraint (see its own frame
    math above)."""
    target = max(min_frames, round(duration_seconds * fps))
    remainder = (target - 1) % temporal_compression
    if remainder:
        target += temporal_compression - remainder
    return target


# --------------------------------------------------------------------------- #
# Text → Video — local open-weight models, dispatched by `params.model`
# --------------------------------------------------------------------------- #

class CudaVideoGenerator(VideoGenerator):
    """Routes a generation request to one of Aurora's local, open-weight
    video models (see `app.generators.model_catalog` for the full roster,
    including hosted models this generator does not serve).

    `params.model` selects the pipeline:
      - "ltx-video"    → Lightricks/LTX-Video      (bfloat16, ~6 GB VRAM)
      - "cogvideox-5b" → THUDM/CogVideoX-5b         (bfloat16, ~12 GB VRAM)
      - "wan-2.1"      → Wan-AI/Wan2.1-T2V-1.3B     (bfloat16, ~8 GB VRAM)
    Omitting `model` falls back to the catalog default (LTX-Video). Any other
    model id in the catalog is a hosted API model with no local weights —
    that integration (provider adapters) isn't built yet, so it raises a
    clear `NotImplementedError` rather than silently running the wrong model.
    """

    name = "cuda-video"

    def generate(
        self,
        params: VideoGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        model_id = params.model or DEFAULT_MODEL_ID
        if model_id == "ltx-video":
            return self._generate_ltx(params, progress)
        if model_id == "cogvideox-5b":
            return self._generate_cogvideox(params, progress)
        if model_id == "wan-2.1":
            return self._generate_wan(params, progress)

        spec = get_model(model_id)
        if spec is not None and spec.kind == "api":
            raise NotImplementedError(
                f"'{model_id}' ({spec.provider}) is a hosted API model — provider "
                "integration is not implemented yet. Local models available today: "
                "ltx-video, cogvideox-5b, wan-2.1."
            )
        raise ValueError(f"Unknown video model '{model_id}'.")

    # -- LTX-Video ----------------------------------------------------------- #
    _LTX_MODEL_ID = "Lightricks/LTX-Video"

    def _generate_ltx(
        self, params: VideoGenParams, progress: ProgressCallback
    ) -> GeneratedMedia:
        import torch  # noqa: PLC0415
        from diffusers import LTXPipeline  # noqa: PLC0415

        def _loader():
            pipe = LTXPipeline.from_pretrained(
                self._LTX_MODEL_ID,
                torch_dtype=torch.bfloat16,
                cache_dir=_HF_HOME,
            )
            pipe.enable_model_cpu_offload()
            return pipe

        pipe = acquire_pipeline("ltx-video", _loader)
        progress(0.1, "model ready")

        num_frames = max(9, int(params.duration_seconds * params.fps))
        generator = torch.Generator("cuda").manual_seed(params.seed or 0)

        result = pipe(
            prompt=params.prompt,
            negative_prompt=params.negative_prompt or (
                "worst quality, inconsistent motion, blurry, jitter, distorted"
            ),
            width=params.width,
            height=params.height,
            num_frames=num_frames,
            num_inference_steps=30,
            guidance_scale=3.0,
            generator=generator,
        )
        progress(0.85, "encoding")
        data = self._export_frames(result.frames[0], fps=params.fps)

        progress(1.0, "done")
        return GeneratedMedia(
            kind="video",
            data=data,
            content_type="video/mp4",
            suggested_filename="generated.mp4",
            duration_seconds=params.duration_seconds,
            width=params.width,
            height=params.height,
            meta={"backend": self.name, "model": "ltx-video", "model_repo": self._LTX_MODEL_ID},
        )

    # -- CogVideoX-5B ---------------------------------------------------------#
    _COGVIDEOX_MODEL_ID = "THUDM/CogVideoX-5b"
    _COGVIDEOX_FPS = 8  # the checkpoint's trained cadence — see docstring below.

    def _generate_cogvideox(
        self, params: VideoGenParams, progress: ProgressCallback
    ) -> GeneratedMedia:
        """CogVideoX-5b is trained at 8 fps with a causal 3D VAE that requires
        `(num_frames - 1) % 4 == 0` — we encode at its native fps rather than
        the caller's requested fps so motion speed matches what the model was
        actually trained on (matching the SVD-XT generator's `_NATIVE_FPS`
        pattern above)."""
        import torch  # noqa: PLC0415
        from diffusers import CogVideoXPipeline  # noqa: PLC0415

        def _loader():
            pipe = CogVideoXPipeline.from_pretrained(
                self._COGVIDEOX_MODEL_ID,
                torch_dtype=torch.bfloat16,
                cache_dir=_HF_HOME,
            )
            pipe.enable_model_cpu_offload()
            pipe.vae.enable_tiling()
            return pipe

        pipe = acquire_pipeline("cogvideox-5b", _loader)
        progress(0.1, "model ready")

        num_frames = _causal_frame_count(params.duration_seconds, self._COGVIDEOX_FPS)
        generator = torch.Generator("cuda").manual_seed(params.seed or 0)

        # CogVideoX-5b renders at its own trained resolution (480x720); it does
        # not honor an arbitrary requested width/height the way LTX/Wan do, so
        # we don't pass params.width/height here and instead report the actual
        # produced frame size on the result (keeping asset metadata truthful).
        result = pipe(
            prompt=params.prompt,
            negative_prompt=params.negative_prompt,
            num_videos_per_prompt=1,
            num_inference_steps=50,
            num_frames=num_frames,
            guidance_scale=6.0,
            generator=generator,
        )
        progress(0.85, "encoding")
        frames = result.frames[0]
        data = self._export_frames(frames, fps=self._COGVIDEOX_FPS)
        actual_width, actual_height = frames[0].size  # PIL (width, height)

        progress(1.0, "done")
        return GeneratedMedia(
            kind="video",
            data=data,
            content_type="video/mp4",
            suggested_filename="generated.mp4",
            duration_seconds=num_frames / self._COGVIDEOX_FPS,
            width=actual_width,
            height=actual_height,
            meta={
                "backend": self.name,
                "model": "cogvideox-5b",
                "model_repo": self._COGVIDEOX_MODEL_ID,
            },
        )

    # -- Wan 2.1 --------------------------------------------------------------#
    _WAN_MODEL_ID = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
    _WAN_FPS = 16  # the checkpoint's trained cadence.

    def _generate_wan(
        self, params: VideoGenParams, progress: ProgressCallback
    ) -> GeneratedMedia:
        """Wan 2.1's diffusers VAE (`AutoencoderKLWan`) is loaded in float32
        per the model card's guidance (its causal temporal decoder is
        numerically unstable in fp16/bf16), while the transformer backbone
        runs in bf16. Shares the same `(num_frames - 1) % 4 == 0` causal-VAE
        constraint as CogVideoX."""
        import torch  # noqa: PLC0415
        from diffusers import AutoencoderKLWan, WanPipeline  # noqa: PLC0415

        def _loader():
            vae = AutoencoderKLWan.from_pretrained(
                self._WAN_MODEL_ID,
                subfolder="vae",
                torch_dtype=torch.float32,
                cache_dir=_HF_HOME,
            )
            pipe = WanPipeline.from_pretrained(
                self._WAN_MODEL_ID,
                vae=vae,
                torch_dtype=torch.bfloat16,
                cache_dir=_HF_HOME,
            )
            pipe.enable_model_cpu_offload()
            return pipe

        pipe = acquire_pipeline("wan-2.1", _loader)
        progress(0.1, "model ready")

        num_frames = _causal_frame_count(params.duration_seconds, self._WAN_FPS)
        generator = torch.Generator("cuda").manual_seed(params.seed or 0)

        result = pipe(
            prompt=params.prompt,
            negative_prompt=params.negative_prompt or (
                "bright colors, overexposed, static, blurred details, subtitles, "
                "worst quality, low quality"
            ),
            width=params.width,
            height=params.height,
            num_frames=num_frames,
            guidance_scale=5.0,
            generator=generator,
        )
        progress(0.85, "encoding")
        data = self._export_frames(result.frames[0], fps=self._WAN_FPS)

        progress(1.0, "done")
        return GeneratedMedia(
            kind="video",
            data=data,
            content_type="video/mp4",
            suggested_filename="generated.mp4",
            duration_seconds=num_frames / self._WAN_FPS,
            width=params.width,
            height=params.height,
            meta={"backend": self.name, "model": "wan-2.1", "model_repo": self._WAN_MODEL_ID},
        )

    @staticmethod
    def _export_frames(frames, *, fps: int) -> bytes:
        from diffusers.utils import export_to_video  # noqa: PLC0415

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            path = f.name
        try:
            export_to_video(frames, path, fps=fps)
            return open(path, "rb").read()  # noqa: WPS515
        finally:
            if os.path.exists(path):
                os.remove(path)


# --------------------------------------------------------------------------- #
# Image → Video (Stable Video Diffusion XT)
# --------------------------------------------------------------------------- #

class CudaImageToVideoGenerator(ImageToVideoGenerator):
    """SVD-XT — image-to-video, 25 frames @ 1024 × 576, fp16."""

    name = "svd-xt"
    _MODEL_ID = "stabilityai/stable-video-diffusion-img2vid-xt"
    # SVD natively produces 25 frames; we take the first N for the requested duration.
    _NATIVE_FPS = 7

    def generate(
        self,
        params: ImageToVideoParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        import torch  # noqa: PLC0415
        from diffusers import StableVideoDiffusionPipeline  # noqa: PLC0415
        from diffusers.utils import export_to_video  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415

        def _loader():
            pipe = StableVideoDiffusionPipeline.from_pretrained(
                self._MODEL_ID,
                torch_dtype=torch.float16,
                variant="fp16",
                cache_dir=_HF_HOME,
            )
            pipe.enable_model_cpu_offload()
            return pipe

        pipe = acquire_pipeline(self.name, _loader)
        progress(0.1, "model ready")

        pil_image = Image.open(io.BytesIO(params.image)).convert("RGB").resize((1024, 576))
        generator = torch.Generator("cuda").manual_seed(params.seed or 42)

        result = pipe(
            image=pil_image,
            num_frames=25,
            decode_chunk_size=8,
            generator=generator,
            motion_bucket_id=127,
            noise_aug_strength=0.02,
        )
        progress(0.85, "encoding")

        frames = result.frames[0]
        if params.duration_seconds:
            target_frames = max(1, int(params.duration_seconds * self._NATIVE_FPS))
            frames = frames[:target_frames]

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            path = f.name
        try:
            export_to_video(frames, path, fps=params.fps)
            data = open(path, "rb").read()  # noqa: WPS515
        finally:
            if os.path.exists(path):
                os.remove(path)

        progress(1.0, "done")
        return GeneratedMedia(
            kind="video",
            data=data,
            content_type="video/mp4",
            suggested_filename="animated.mp4",
            duration_seconds=params.duration_seconds,
            meta={"backend": self.name, "model": self._MODEL_ID},
        )


# --------------------------------------------------------------------------- #
# Text → Image (FLUX.1-dev)
# --------------------------------------------------------------------------- #

class CudaImageGenerator(ImageGenerator):
    """FLUX.1-dev — state-of-the-art text-to-image, bfloat16 with CPU offload."""

    name = "flux-dev"
    _MODEL_ID = "black-forest-labs/FLUX.1-dev"

    def generate(
        self,
        params: ImageGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        import torch  # noqa: PLC0415
        from diffusers import FluxPipeline  # noqa: PLC0415

        def _loader():
            pipe = FluxPipeline.from_pretrained(
                self._MODEL_ID,
                torch_dtype=torch.bfloat16,
                cache_dir=_HF_HOME,
            )
            # Sequential offload keeps peak VRAM under 16 GB for FLUX.1-dev.
            pipe.enable_sequential_cpu_offload()
            return pipe

        pipe = acquire_pipeline(self.name, _loader)
        progress(0.1, "model ready")

        generator = torch.Generator("cpu").manual_seed(params.seed or 0)

        result = pipe(
            prompt=params.prompt,
            negative_prompt=params.negative_prompt,
            width=params.width,
            height=params.height,
            num_inference_steps=28,
            guidance_scale=3.5,
            generator=generator,
        )
        progress(0.85, "encoding")

        buf = io.BytesIO()
        result.images[0].save(buf, format="PNG")

        progress(1.0, "done")
        return GeneratedMedia(
            kind="image",
            data=buf.getvalue(),
            content_type="image/png",
            suggested_filename="generated.png",
            width=params.width,
            height=params.height,
            meta={"backend": self.name, "model": self._MODEL_ID},
        )


# --------------------------------------------------------------------------- #
# Text → Music (MusicGen-small)
# --------------------------------------------------------------------------- #

class CudaMusicGenerator(MusicGenerator):
    """MusicGen-small — text-conditioned music generation via HuggingFace Transformers."""

    name = "musicgen"
    _MODEL_ID = "facebook/musicgen-small"

    def generate(
        self,
        params: MusicGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        import numpy as np  # noqa: PLC0415
        import torch  # noqa: PLC0415
        from transformers import (  # noqa: PLC0415
            AutoProcessor,
            MusicgenForConditionalGeneration,
        )

        def _loader():
            processor = AutoProcessor.from_pretrained(self._MODEL_ID, cache_dir=_HF_HOME)
            model = MusicgenForConditionalGeneration.from_pretrained(
                self._MODEL_ID, cache_dir=_HF_HOME
            ).to("cuda")
            return (processor, model)

        processor, model = acquire_pipeline(self.name, _loader)
        progress(0.1, "model ready")

        inputs = processor(
            text=[params.prompt], padding=True, return_tensors="pt"
        ).to("cuda")

        sr = model.config.audio_encoder.sampling_rate
        frame_rate = model.config.audio_encoder.frame_rate
        max_tokens = int(params.duration_seconds * frame_rate)

        with torch.no_grad():
            audio_values = model.generate(**inputs, max_new_tokens=max_tokens)

        progress(0.8, "encoding")

        audio_np = audio_values[0, 0].cpu().numpy()
        audio_int16 = (np.clip(audio_np, -1.0, 1.0) * 32767).astype(np.int16)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(audio_int16.tobytes())

        progress(1.0, "done")
        return GeneratedMedia(
            kind="audio",
            data=buf.getvalue(),
            content_type="audio/wav",
            suggested_filename="music.wav",
            duration_seconds=params.duration_seconds,
            meta={"backend": self.name, "model": self._MODEL_ID},
        )
