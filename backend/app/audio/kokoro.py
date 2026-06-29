"""Kokoro 82M TTS — torch-based, best quality.

Requires: pip install -r requirements/tts-kokoro.txt
Weights:  auto-downloaded from HF (~327 MB) on first call.
          Set HF_HOME env var to control cache location.

Engine is held in an lru_cache singleton so the model loads once and stays
warm across multiple TTS jobs.
"""

from __future__ import annotations

import io
import logging
import wave
from functools import lru_cache

import numpy as np

from app.core.config import settings
from app.generators.base import (
    GeneratedMedia,
    ProgressCallback,
    VoiceGenerator,
    VoiceGenParams,
    _noop_progress,
)

logger = logging.getLogger(__name__)


def is_kokoro_available() -> bool:
    """True only when the kokoro package (torch-based) is importable."""
    try:
        import kokoro  # noqa: F401
        return True
    except ImportError:
        return False


@lru_cache(maxsize=1)
def _get_pipeline(lang_code: str):
    """Cached KPipeline singleton — model loads once per process."""
    from kokoro import KPipeline  # noqa: PLC0415

    logger.info("Loading Kokoro pipeline (lang=%s) — first call only.", lang_code)
    return KPipeline(lang_code=lang_code)


def _samples_to_wav(samples: np.ndarray, sample_rate: int = 24000) -> bytes:
    """Convert float32 audio samples to WAV bytes (16-bit PCM)."""
    pcm = (samples * 32767).clip(-32768, 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)  # 16-bit
        w.setframerate(sample_rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


def _duration_from_wav(data: bytes) -> float | None:
    try:
        buf = io.BytesIO(data)
        with wave.open(buf, "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:  # noqa: BLE001
        return None


class KokoroVoiceGenerator(VoiceGenerator):
    """Kokoro 82M (torch, full fp32) — highest quality CPU TTS."""

    name = "kokoro"
    SAMPLE_RATE = 24000

    def generate(
        self,
        params: VoiceGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        voice_id = (
            params.voice
            if params.voice and params.voice != "default"
            else settings.kokoro_default_voice
        )
        speed = float(params.speed or 1.0)

        progress(0.1, "loading model")
        pipeline = _get_pipeline(settings.kokoro_lang)

        progress(0.3, "synthesizing")
        chunks: list[np.ndarray] = []
        for _, _, audio in pipeline(params.text, voice=voice_id, speed=speed):
            if audio is not None:
                chunks.append(audio)

        if not chunks:
            raise RuntimeError("Kokoro produced no audio for the given text.")

        progress(0.9, "encoding")
        combined = np.concatenate(chunks)
        wav_bytes = _samples_to_wav(combined, self.SAMPLE_RATE)

        progress(1.0, "done")
        return GeneratedMedia(
            kind="audio",
            data=wav_bytes,
            content_type="audio/wav",
            suggested_filename="voiceover_kokoro.wav",
            duration_seconds=_duration_from_wav(wav_bytes),
            meta={
                "backend": self.name,
                "voice": voice_id,
                "lang": settings.kokoro_lang,
                "speed": speed,
            },
        )
