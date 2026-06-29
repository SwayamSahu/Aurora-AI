"""Real, CPU-only speech-to-text via faster-whisper.

Produces timed segments for auto-subtitles. Runs on CPU on both the Mac and the
deploy box. The model is loaded once and cached; it downloads on first use.
"""

from __future__ import annotations

import tempfile
from functools import lru_cache

from app.core.config import settings
from app.generators.base import (
    ProgressCallback,
    Transcriber,
    TranscriptionResult,
    TranscriptSegment,
    _noop_progress,
    segments_to_srt,
)


@lru_cache
def _load_model(name: str):
    from faster_whisper import WhisperModel  # noqa: PLC0415

    # int8 keeps memory + CPU cost low for short clips.
    return WhisperModel(name, device="cpu", compute_type="int8")


class WhisperTranscriber(Transcriber):
    name = "whisper"

    def transcribe(
        self,
        data: bytes,
        content_type: str,
        progress: ProgressCallback = _noop_progress,
    ) -> TranscriptionResult:
        progress(0.1, "loading model")
        model = _load_model(settings.whisper_model)

        suffix = ".mp4" if "video" in content_type else ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix) as f:
            f.write(data)
            f.flush()
            progress(0.3, "transcribing")
            segments_iter, info = model.transcribe(f.name, vad_filter=True)
            segments = [
                TranscriptSegment(start=s.start, end=s.end, text=s.text.strip())
                for s in segments_iter
            ]

        progress(1.0, "done")
        return TranscriptionResult(
            segments=segments,
            srt=segments_to_srt(segments),
            language=getattr(info, "language", None),
        )


def resolve_transcriber() -> Transcriber | None:
    try:
        import faster_whisper  # noqa: F401,PLC0415
    except ImportError:
        return None
    return WhisperTranscriber()
