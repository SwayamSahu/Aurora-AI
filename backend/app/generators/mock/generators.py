"""Concrete mock generators backed by fixture media."""

from __future__ import annotations

import time
from pathlib import Path

from app.generators.base import (
    GeneratedMedia,
    ImageGenerator,
    ImageGenParams,
    ImageToVideoGenerator,
    ImageToVideoParams,
    MusicGenerator,
    MusicGenParams,
    ProgressCallback,
    Transcriber,
    TranscriptionResult,
    TranscriptSegment,
    VideoGenerator,
    VideoGenParams,
    VoiceGenerator,
    VoiceGenParams,
    _noop_progress,
    segments_to_srt,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def _simulate(progress: ProgressCallback, steps: int = 4, delay: float = 0.0) -> None:
    """Emit incremental progress so the UI/queue path is exercised.

    `delay` is 0 in tests (fast) and can be raised in dev for a realistic feel.
    """
    for i in range(1, steps + 1):
        if delay:
            time.sleep(delay)
        progress(i / steps, f"step {i}/{steps}")


class MockVideoGenerator(VideoGenerator):
    name = "mock-video"

    def __init__(self, step_delay: float = 0.0) -> None:
        self._delay = step_delay

    def generate(
        self,
        params: VideoGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        _simulate(progress, delay=self._delay)
        return GeneratedMedia(
            kind="video",
            data=_load("sample.mp4"),
            content_type="video/mp4",
            suggested_filename="generated.mp4",
            duration_seconds=params.duration_seconds,
            width=params.width,
            height=params.height,
            meta={"backend": self.name, "prompt": params.prompt},
        )


class MockImageToVideoGenerator(ImageToVideoGenerator):
    name = "mock-image-to-video"

    def __init__(self, step_delay: float = 0.0) -> None:
        self._delay = step_delay

    def generate(
        self,
        params: ImageToVideoParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        _simulate(progress, delay=self._delay)
        return GeneratedMedia(
            kind="video",
            data=_load("sample.mp4"),
            content_type="video/mp4",
            suggested_filename="animated.mp4",
            duration_seconds=params.duration_seconds,
            meta={"backend": self.name},
        )


class MockImageGenerator(ImageGenerator):
    name = "mock-image"

    def __init__(self, step_delay: float = 0.0) -> None:
        self._delay = step_delay

    def generate(
        self,
        params: ImageGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        _simulate(progress, delay=self._delay)
        return GeneratedMedia(
            kind="image",
            data=_load("sample.png"),
            content_type="image/png",
            suggested_filename="generated.png",
            width=params.width,
            height=params.height,
            meta={"backend": self.name, "prompt": params.prompt},
        )


class MockVoiceGenerator(VoiceGenerator):
    name = "mock-voice"

    def generate(
        self,
        params: VoiceGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        progress(1.0, "done")
        return GeneratedMedia(
            kind="audio",
            data=_load("sample.wav"),
            content_type="audio/wav",
            suggested_filename="voiceover.wav",
            duration_seconds=3.0,
            meta={"backend": self.name, "voice": params.voice},
        )


class MockMusicGenerator(MusicGenerator):
    name = "mock-music"

    def generate(
        self,
        params: MusicGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        progress(1.0, "done")
        return GeneratedMedia(
            kind="audio",
            data=_load("sample.wav"),
            content_type="audio/wav",
            suggested_filename="music.wav",
            duration_seconds=params.duration_seconds,
            meta={"backend": self.name},
        )


class MockTranscriber(Transcriber):
    name = "mock-transcriber"

    def transcribe(
        self,
        data: bytes,
        content_type: str,
        progress: ProgressCallback = _noop_progress,
    ) -> TranscriptionResult:
        progress(1.0, "done")
        segments = [
            TranscriptSegment(0.0, 2.0, "This is a mock subtitle track."),
            TranscriptSegment(2.0, 4.0, "Real captions use Whisper in Phase 6."),
        ]
        return TranscriptionResult(
            segments=segments, srt=segments_to_srt(segments), language="en"
        )
