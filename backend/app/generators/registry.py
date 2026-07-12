"""Generator registry — resolves the configured backend to concrete instances.

This is the ONE place the backend is chosen. Application code calls
`get_video_generator()` etc. and never imports a concrete implementation.

- mock   → Mac development & tests (Phases 0–8)
- cuda    → real models on the NVIDIA box (Phase 9)
- remote  → delegate to a remote worker (optional)
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import AudioBackend, GeneratorBackend, settings
from app.generators.base import (
    ContentSafetyClassifier,
    ImageGenerator,
    ImageToVideoGenerator,
    MusicGenerator,
    ObjectDetector,
    Transcriber,
    VideoEditor,
    VideoGenerator,
    VoiceGenerator,
)
from app.generators.mock import (
    MockContentSafetyClassifier,
    MockImageGenerator,
    MockImageToVideoGenerator,
    MockMusicGenerator,
    MockObjectDetector,
    MockTranscriber,
    MockVideoEditor,
    MockVideoGenerator,
    MockVoiceGenerator,
)


def _cuda_not_ready(what: str):
    raise NotImplementedError(
        f"CUDA {what} generator is implemented in Phase 9 on the NVIDIA box. "
        f"Set GENERATOR_BACKEND=mock for Mac development."
    )


@lru_cache
def get_video_generator() -> VideoGenerator:
    backend = settings.generator_backend
    if backend == GeneratorBackend.MOCK:
        return MockVideoGenerator()
    if backend == GeneratorBackend.CUDA:
        from app.generators.cuda import CudaVideoGenerator  # noqa: PLC0415

        return CudaVideoGenerator()
    _cuda_not_ready("video")


@lru_cache
def get_image_to_video_generator() -> ImageToVideoGenerator:
    backend = settings.generator_backend
    if backend == GeneratorBackend.MOCK:
        return MockImageToVideoGenerator()
    if backend == GeneratorBackend.CUDA:
        from app.generators.cuda import CudaImageToVideoGenerator  # noqa: PLC0415

        return CudaImageToVideoGenerator()
    _cuda_not_ready("image-to-video")


@lru_cache
def get_image_generator() -> ImageGenerator:
    backend = settings.generator_backend
    if backend == GeneratorBackend.MOCK:
        return MockImageGenerator()
    if backend == GeneratorBackend.CUDA:
        from app.generators.cuda import CudaImageGenerator  # noqa: PLC0415

        return CudaImageGenerator()
    _cuda_not_ready("image")


@lru_cache
def get_voice_generator() -> VoiceGenerator:
    # TTS is CPU-real on both Mac (`say`) and Linux (`espeak-ng`).
    if settings.audio_backend == AudioBackend.REAL:
        from app.audio.tts import resolve_voice_generator  # noqa: PLC0415

        real = resolve_voice_generator()
        if real is not None:
            return real
    return MockVoiceGenerator()


@lru_cache
def get_transcriber() -> Transcriber:
    # Whisper is CPU-real; falls back to mock if faster-whisper isn't installed.
    if settings.audio_backend == AudioBackend.REAL:
        from app.audio.transcribe import resolve_transcriber  # noqa: PLC0415

        real = resolve_transcriber()
        if real is not None:
            return real
    return MockTranscriber()


@lru_cache
def get_video_editor() -> VideoEditor:
    backend = settings.generator_backend
    if backend == GeneratorBackend.MOCK:
        return MockVideoEditor()
    if backend == GeneratorBackend.CUDA:
        from app.generators.cuda import CudaVideoEditor  # noqa: PLC0415

        return CudaVideoEditor()
    _cuda_not_ready("video editor")


@lru_cache
def get_object_detector() -> ObjectDetector:
    backend = settings.generator_backend
    if backend == GeneratorBackend.MOCK:
        return MockObjectDetector()
    if backend == GeneratorBackend.CUDA:
        from app.generators.cuda import CudaObjectDetector  # noqa: PLC0415

        return CudaObjectDetector()
    _cuda_not_ready("object detector")


@lru_cache
def get_music_generator() -> MusicGenerator:
    # Music generation (MusicGen) is GPU-bound — real impl arrives in Phase 9.
    if settings.generator_backend == GeneratorBackend.MOCK:
        return MockMusicGenerator()
    from app.generators.cuda import CudaMusicGenerator  # noqa: PLC0415

    return CudaMusicGenerator()


@lru_cache
def get_content_safety_classifier() -> ContentSafetyClassifier:
    # A real NSFW/violence classifier is GPU-bound — real impl arrives in
    # Phase 9. The mock heuristic is what runs on every upload today.
    if settings.generator_backend == GeneratorBackend.MOCK:
        return MockContentSafetyClassifier()
    _cuda_not_ready("content safety classifier")
