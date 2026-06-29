"""CUDA generator implementations — activated only when GENERATOR_BACKEND=cuda.

All GPU-heavy imports (torch, diffusers, transformers) are lazy so this module
can be imported on a CPU-only Mac without error.  Concrete model choices:

  Text → video:   LTX-Video  (Lightricks/LTX-Video, bfloat16, ~6 GB VRAM)
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

logger = logging.getLogger(__name__)

_HF_HOME = os.environ.get("HF_HOME", "/models/hf")


# --------------------------------------------------------------------------- #
# Text → Video (LTX-Video)
# --------------------------------------------------------------------------- #

class CudaVideoGenerator(VideoGenerator):
    """LTX-Video — text-to-video, up to 8 s @ 768 × 512, bfloat16."""

    name = "ltx-video"
    _MODEL_ID = "Lightricks/LTX-Video"

    def generate(
        self,
        params: VideoGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        import torch  # noqa: PLC0415
        from diffusers import LTXPipeline  # noqa: PLC0415
        from diffusers.utils import export_to_video  # noqa: PLC0415

        def _loader():
            pipe = LTXPipeline.from_pretrained(
                self._MODEL_ID,
                torch_dtype=torch.bfloat16,
                cache_dir=_HF_HOME,
            )
            pipe.enable_model_cpu_offload()
            return pipe

        pipe = acquire_pipeline(self.name, _loader)
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

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            path = f.name
        try:
            export_to_video(result.frames[0], path, fps=params.fps)
            data = open(path, "rb").read()  # noqa: WPS515
        finally:
            if os.path.exists(path):
                os.remove(path)

        progress(1.0, "done")
        return GeneratedMedia(
            kind="video",
            data=data,
            content_type="video/mp4",
            suggested_filename="generated.mp4",
            duration_seconds=params.duration_seconds,
            width=params.width,
            height=params.height,
            meta={"backend": self.name, "model": self._MODEL_ID},
        )


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
