"""Per-engine voice catalogues.

Returned by GET /api/v1/audio/voices so the frontend always shows the voices
that actually work with the configured TTS engine.
"""

from __future__ import annotations

from app.core.config import TtsEngine

Voice = dict  # {value: str, label: str}


# Kokoro 82M voices (v1.0, American + British English).
# Full list: https://huggingface.co/hexgrad/Kokoro-82M
KOKORO_VOICES: list[Voice] = [
    # American English female
    {"value": "af_heart", "label": "Heart (US Female) ⭐ recommended"},
    {"value": "af_bella", "label": "Bella (US Female)"},
    {"value": "af_nicole", "label": "Nicole (US Female)"},
    {"value": "af_aoede", "label": "Aoede (US Female)"},
    {"value": "af_kore", "label": "Kore (US Female)"},
    {"value": "af_sarah", "label": "Sarah (US Female)"},
    {"value": "af_sky", "label": "Sky (US Female)"},
    # American English male
    {"value": "am_adam", "label": "Adam (US Male)"},
    {"value": "am_echo", "label": "Echo (US Male)"},
    {"value": "am_eric", "label": "Eric (US Male)"},
    {"value": "am_fenrir", "label": "Fenrir (US Male)"},
    {"value": "am_liam", "label": "Liam (US Male)"},
    {"value": "am_michael", "label": "Michael (US Male)"},
    {"value": "am_onyx", "label": "Onyx (US Male)"},
    {"value": "am_puck", "label": "Puck (US Male)"},
    # British English female
    {"value": "bf_alice", "label": "Alice (UK Female)"},
    {"value": "bf_emma", "label": "Emma (UK Female)"},
    {"value": "bf_isabella", "label": "Isabella (UK Female)"},
    {"value": "bf_lily", "label": "Lily (UK Female)"},
    # British English male
    {"value": "bm_daniel", "label": "Daniel (UK Male)"},
    {"value": "bm_fable", "label": "Fable (UK Male)"},
    {"value": "bm_george", "label": "George (UK Male)"},
    {"value": "bm_lewis", "label": "Lewis (UK Male)"},
]

# macOS `say` voices (common built-in; user may have more installed).
SAY_VOICES: list[Voice] = [
    {"value": "default", "label": "Default (System)"},
    {"value": "Samantha", "label": "Samantha (US Female)"},
    {"value": "Alex", "label": "Alex (US Male)"},
    {"value": "Daniel", "label": "Daniel (UK Male)"},
    {"value": "Karen", "label": "Karen (AU Female)"},
    {"value": "Moira", "label": "Moira (IE Female)"},
    {"value": "Rishi", "label": "Rishi (IN Male)"},
]

# Linux espeak-ng voices.
ESPEAK_VOICES: list[Voice] = [
    {"value": "default", "label": "Default"},
    {"value": "en", "label": "English"},
    {"value": "en-us", "label": "English (US)"},
    {"value": "en-gb", "label": "English (UK)"},
    {"value": "en+f3", "label": "English Female"},
    {"value": "en+m3", "label": "English Male"},
]

MOCK_VOICES: list[Voice] = [
    {"value": "default", "label": "Default (mock)"},
]


def voices_for_engine(engine_name: str) -> list[Voice]:
    """Return the voice list for the given engine name string."""
    e = engine_name.lower()
    if e == TtsEngine.KOKORO:
        return KOKORO_VOICES
    if e == TtsEngine.SAY:
        return SAY_VOICES
    if e == TtsEngine.ESPEAK:
        return ESPEAK_VOICES
    if e == TtsEngine.AUTO:
        import platform
        import shutil

        if platform.system() == "Darwin" and shutil.which("say"):
            return SAY_VOICES
        if shutil.which("espeak-ng"):
            return ESPEAK_VOICES
    return MOCK_VOICES
