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


# The engine primitives the video editor understands (see the AI Edit plan).
EditEngine = Literal[
    "segment-track",
    "inpaint-remove",
    "masked-v2v",
    "global-restyle",
    "enhance",
    "retime-camera",
    "text-ops",
]


@dataclass
class VideoEditParams:
    """A single non-destructive edit applied to one source clip.

    The source clip bytes and an optional mask (PNG, white = edit region) are
    passed in; the editor returns a new video. `engine` selects the primitive,
    `params` carries engine-specific knobs (strength, factor, …).
    """

    source: bytes
    source_content_type: str
    engine: EditEngine
    prompt: str = ""
    mask: bytes | None = None
    params: dict = field(default_factory=dict)
    # Identifies which catalog preset was applied (see frontend presets.ts).
    # Deterministic engines (retime, color grade, OCR) key their real,
    # non-generative recipes off this id; unmatched ids fall back to the
    # generic stand-in filter for that engine.
    preset_id: str | None = None


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


class VideoEditor(Generator):
    """Applies a single AI edit to a source clip (mask-aware).

    Mock implementation uses real FFmpeg transforms so before/after is visible
    on the Mac; the CUDA implementation swaps in real models on the GPU box.
    """

    @abstractmethod
    def edit(
        self,
        params: VideoEditParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia: ...


# --------------------------------------------------------------------------- #
# Object detection / tracking (P1 — segment-track)
# --------------------------------------------------------------------------- #
@dataclass
class DetectParams:
    """A single detection request against one frame of a clip.

    `mode="click"` asks "what's at this point?" (x, y normalized 0-1).
    `mode="text"` asks "find every X" and may return several candidates.
    """

    mode: Literal["click", "text"]
    x: float | None = None
    y: float | None = None
    query: str | None = None
    # The clip's source video bytes. Optional because the mock detector doesn't
    # need them; real backends (SAM 2 / GroundingDINO) require a frame to run on
    # and the detect route attaches these when a source asset is given.
    source: bytes | None = None


@dataclass
class DetectedObject:
    """A candidate object: a normalized (0-1) bounding box + label.

    Real backends additionally resolve a per-frame masklet for tracking
    across time; the mock backend returns a static box only.
    """

    label: str
    x: float
    y: float
    w: float
    h: float
    confidence: float = 1.0


class ObjectDetector(Generator):
    """Finds candidate objects to select for editing (click or text query).

    Mock implementation returns deterministic, plausible boxes so the
    click-to-select and "select all X" UX can be built and tested before
    Phase 9 swaps in real segmentation (SAM 2 + GroundingDINO).
    """

    @abstractmethod
    def detect(self, params: DetectParams) -> list[DetectedObject]: ...


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


# --------------------------------------------------------------------------- #
# Content safety (automated NSFW/violence screening on upload)
# --------------------------------------------------------------------------- #
@dataclass
class ContentSafetyResult:
    flagged: bool
    categories: list[str] = field(default_factory=list)
    confidence: float = 0.0


class ContentSafetyClassifier(Generator):
    """Screens an uploaded image at upload time. Mock implementation is a
    deterministic heuristic (see `MockContentSafetyClassifier`) so the
    auto-flagging pipeline — flag categories, auto-report creation, admin
    review — can be built and tested without a real model. The CUDA
    implementation swaps in a real NSFW classifier on the GPU box."""

    @abstractmethod
    def classify(self, image_bytes: bytes, content_type: str) -> ContentSafetyResult: ...


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
