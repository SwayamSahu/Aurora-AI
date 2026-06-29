"""The generator contract.

Every GPU-dependent capability hides behind one of these abstract interfaces.
The application code (API routes, Celery tasks) depends ONLY on these
abstractions — never on a concrete model. That is what lets the entire
platform be built and tested on the Mac with `MockGenerator`s, and switched
to real CUDA models on the NVIDIA box via a single env var.

Progress is reported through an optional callback so the job queue can stream
updates over WebSocket regardless of which backend is running.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal, Protocol

MediaKind = Literal["video", "image", "audio", "subtitles"]


class ProgressCallback(Protocol):
    def __call__(self, fraction: float, message: str | None = None) -> None: ...


def _noop_progress(fraction: float, message: str | None = None) -> None:
    """Default progress sink used when a caller does not provide one."""


@dataclass
class GeneratedMedia:
    """The result of any generation call: raw bytes plus metadata.

    Bytes are returned (not a path) so the caller decides where to persist
    them — typically uploaded to MinIO by the worker.
    """

    kind: MediaKind
    data: bytes
    content_type: str
    suggested_filename: str
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    meta: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Parameter objects
# --------------------------------------------------------------------------- #
@dataclass
class VideoGenParams:
    prompt: str
    negative_prompt: str | None = None
    duration_seconds: float = 4.0
    width: int = 768
    height: int = 512
    fps: int = 24
    seed: int | None = None
    model: str | None = None  # backend-specific model id, None = backend default


@dataclass
class ImageToVideoParams:
    image: bytes
    prompt: str | None = None
    duration_seconds: float = 4.0
    fps: int = 24
    seed: int | None = None
    model: str | None = None


@dataclass
class ImageGenParams:
    prompt: str
    negative_prompt: str | None = None
    width: int = 1024
    height: int = 1024
    seed: int | None = None
    model: str | None = None


@dataclass
class VoiceGenParams:
    text: str
    voice: str = "default"
    speed: float = 1.0


@dataclass
class MusicGenParams:
    prompt: str
    duration_seconds: float = 10.0


# --------------------------------------------------------------------------- #
# Interfaces
# --------------------------------------------------------------------------- #
class Generator(ABC):  # noqa: B024  (shared base; subclasses add abstract methods)
    """Common base for every generator implementation."""

    #: human-readable backend id, e.g. "mock", "ltx-video"
    name: str = "base"

    def healthcheck(self) -> bool:
        """Return True if the backend is ready to serve requests."""
        return True


class VideoGenerator(Generator):
    @abstractmethod
    def generate(
        self,
        params: VideoGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia: ...


class ImageToVideoGenerator(Generator):
    @abstractmethod
    def generate(
        self,
        params: ImageToVideoParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia: ...


class ImageGenerator(Generator):
    @abstractmethod
    def generate(
        self,
        params: ImageGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia: ...


class VoiceGenerator(Generator):
    @abstractmethod
    def generate(
        self,
        params: VoiceGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia: ...


class MusicGenerator(Generator):
    @abstractmethod
    def generate(
        self,
        params: MusicGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia: ...


# --------------------------------------------------------------------------- #
# Transcription (speech-to-text for auto-subtitles)
# --------------------------------------------------------------------------- #
@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    segments: list[TranscriptSegment]
    srt: str
    language: str | None = None


class Transcriber(Generator):
    @abstractmethod
    def transcribe(
        self,
        data: bytes,
        content_type: str,
        progress: ProgressCallback = _noop_progress,
    ) -> TranscriptionResult: ...


def segments_to_srt(segments: list[TranscriptSegment]) -> str:
    """Render transcript segments as an SRT subtitle document."""

    def ts(seconds: float) -> str:
        ms = int(round(seconds * 1000))
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines: list[str] = []
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{ts(seg.start)} --> {ts(seg.end)}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines)
