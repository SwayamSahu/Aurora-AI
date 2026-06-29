"""Real, CPU-only text-to-speech.

Supports multiple engines selectable via TTS_ENGINE in the environment:
  auto    → macOS `say` if on Darwin, else `espeak-ng` if available (default)
  say     → force macOS `say`
  espeak  → force Linux/macOS `espeak-ng`
  kokoro  → Kokoro 82M (torch, best quality; needs pip install -r requirements/tts-kokoro.txt)
  mock    → always return fixture audio (useful in dev, no engine required)

Graceful degradation: if the requested engine is unavailable, the function
falls back (kokoro → say/espeak → mock) and logs a warning. The pipeline never
hard-fails on a missing TTS engine.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import tempfile
import wave

from app.core.config import TtsEngine, settings
from app.generators.base import (
    GeneratedMedia,
    ProgressCallback,
    VoiceGenerator,
    VoiceGenParams,
    _noop_progress,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _wav_duration(data: bytes) -> float | None:
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            f.write(data)
            f.flush()
            with wave.open(f.name) as w:
                return w.getnframes() / float(w.getframerate())
    except Exception:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------- #
# Engines
# --------------------------------------------------------------------------- #

class SayVoiceGenerator(VoiceGenerator):
    """macOS `say`."""

    name = "tts-say"

    def generate(
        self,
        params: VoiceGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        progress(0.2, "synthesizing")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        try:
            cmd = ["say", "--data-format=LEI16@22050", "-o", path]
            if params.voice and params.voice != "default":
                cmd += ["-v", params.voice]
            if params.speed and params.speed != 1.0:
                cmd += ["-r", str(int(175 * params.speed))]
            cmd.append(params.text)
            subprocess.run(cmd, check=True, capture_output=True)
            data = open(path, "rb").read()  # noqa: WPS515
        finally:
            if os.path.exists(path):
                os.remove(path)
        progress(1.0, "done")
        return GeneratedMedia(
            kind="audio",
            data=data,
            content_type="audio/wav",
            suggested_filename="voiceover.wav",
            duration_seconds=_wav_duration(data),
            meta={"backend": self.name, "voice": params.voice},
        )


class EspeakVoiceGenerator(VoiceGenerator):
    """Linux/macOS `espeak-ng`."""

    name = "tts-espeak"

    def generate(
        self,
        params: VoiceGenParams,
        progress: ProgressCallback = _noop_progress,
    ) -> GeneratedMedia:
        progress(0.2, "synthesizing")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        try:
            cmd = [
                "espeak-ng", "-w", path,
                "-s", str(int(175 * (params.speed or 1.0))),
            ]
            if params.voice and params.voice != "default":
                cmd += ["-v", params.voice]
            cmd.append(params.text)
            subprocess.run(cmd, check=True, capture_output=True)
            data = open(path, "rb").read()  # noqa: WPS515
        finally:
            if os.path.exists(path):
                os.remove(path)
        progress(1.0, "done")
        return GeneratedMedia(
            kind="audio",
            data=data,
            content_type="audio/wav",
            suggested_filename="voiceover.wav",
            duration_seconds=_wav_duration(data),
            meta={"backend": self.name, "voice": params.voice},
        )


# --------------------------------------------------------------------------- #
# Resolution
# --------------------------------------------------------------------------- #

def _auto_generator() -> VoiceGenerator | None:
    """Platform-based fallback: say on macOS, espeak-ng on Linux."""
    if platform.system() == "Darwin" and shutil.which("say"):
        return SayVoiceGenerator()
    if shutil.which("espeak-ng"):
        return EspeakVoiceGenerator()
    return None


def resolve_voice_generator() -> VoiceGenerator | None:
    """Return the best available TTS generator, honouring TTS_ENGINE.

    Falls back gracefully rather than raising if the requested engine is
    unavailable (e.g. Kokoro deps not installed).  Returns None only when
    nothing is available, in which case the registry uses MockVoiceGenerator.
    """
    engine = settings.tts_engine

    # --- Explicit mock ---
    if engine == TtsEngine.MOCK:
        return None  # registry will use MockVoiceGenerator

    # --- Kokoro (best quality, torch-based) ---
    if engine == TtsEngine.KOKORO:
        from app.audio.kokoro import (  # noqa: PLC0415
            KokoroVoiceGenerator,
            is_kokoro_available,
        )
        if is_kokoro_available():
            return KokoroVoiceGenerator()
        logger.warning(
            "TTS_ENGINE=kokoro requested but the 'kokoro' package is not installed. "
            "Run: pip install -r requirements/tts-kokoro.txt  "
            "Falling back to platform TTS (say / espeak-ng)."
        )
        return _auto_generator()

    # --- Explicit say ---
    if engine == TtsEngine.SAY:
        if shutil.which("say"):
            return SayVoiceGenerator()
        logger.warning("TTS_ENGINE=say requested but `say` not found. Falling back.")
        return _auto_generator()

    # --- Explicit espeak ---
    if engine == TtsEngine.ESPEAK:
        if shutil.which("espeak-ng"):
            return EspeakVoiceGenerator()
        logger.warning("TTS_ENGINE=espeak requested but `espeak-ng` not found. Falling back.")
        return _auto_generator()

    # --- Auto (default) ---
    return _auto_generator()
