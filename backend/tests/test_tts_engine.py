"""TTS engine resolution and /audio/voices endpoint.

All tests run without Kokoro or any real TTS binary — engine availability is
monkeypatched so the suite stays fast and dependency-free.
"""

from __future__ import annotations

from unittest.mock import patch

from app.audio.tts import (
    EspeakVoiceGenerator,
    SayVoiceGenerator,
    resolve_voice_generator,
)
from app.audio.voices import ESPEAK_VOICES, KOKORO_VOICES, SAY_VOICES, voices_for_engine
from app.core.config import TtsEngine

# ── Helpers ──────────────────────────────────────────────────────────────────

def _with_engine(engine: TtsEngine):
    """Context manager: temporarily set TTS_ENGINE without touching the registry cache."""
    from app.core.config import settings
    old = settings.tts_engine
    settings.tts_engine = engine

    class _CM:
        def __enter__(self):
            return None

        def __exit__(self, *_):
            settings.tts_engine = old

    return _CM()


# ── Engine resolution ─────────────────────────────────────────────────────────

class TestResolveVoiceGenerator:
    def test_auto_darwin_say(self):
        with _with_engine(TtsEngine.AUTO):
            with patch("platform.system", return_value="Darwin"), \
                 patch("shutil.which", side_effect=lambda cmd: "/usr/bin/say" if cmd == "say" else None):
                gen = resolve_voice_generator()
        assert isinstance(gen, SayVoiceGenerator)

    def test_auto_linux_espeak(self):
        with _with_engine(TtsEngine.AUTO):
            with patch("platform.system", return_value="Linux"), \
                 patch("shutil.which", side_effect=lambda cmd: "/usr/bin/espeak-ng" if cmd == "espeak-ng" else None):
                gen = resolve_voice_generator()
        assert isinstance(gen, EspeakVoiceGenerator)

    def test_auto_nothing_available_returns_none(self):
        with _with_engine(TtsEngine.AUTO):
            with patch("platform.system", return_value="Linux"), \
                 patch("shutil.which", return_value=None):
                gen = resolve_voice_generator()
        assert gen is None

    def test_explicit_say(self):
        with _with_engine(TtsEngine.SAY):
            with patch("shutil.which", side_effect=lambda cmd: "/usr/bin/say" if cmd == "say" else None):
                gen = resolve_voice_generator()
        assert isinstance(gen, SayVoiceGenerator)

    def test_explicit_say_not_found_falls_back(self):
        with _with_engine(TtsEngine.SAY):
            with patch("shutil.which", return_value=None), \
                 patch("platform.system", return_value="Linux"):
                gen = resolve_voice_generator()
        assert gen is None  # auto fallback also finds nothing

    def test_explicit_espeak(self):
        with _with_engine(TtsEngine.ESPEAK):
            with patch("shutil.which", side_effect=lambda cmd: "/usr/bin/espeak-ng" if cmd == "espeak-ng" else None):
                gen = resolve_voice_generator()
        assert isinstance(gen, EspeakVoiceGenerator)

    def test_kokoro_available(self):
        from app.audio.kokoro import KokoroVoiceGenerator
        with _with_engine(TtsEngine.KOKORO):
            # Patch inside the kokoro module where the symbols live at import time.
            with patch("app.audio.kokoro.is_kokoro_available", return_value=True):
                # Also need to bypass the actual __init__ of KokoroVoiceGenerator.
                with patch.object(KokoroVoiceGenerator, "__init__", return_value=None):
                    gen = resolve_voice_generator()
        assert gen.__class__.__name__ == "KokoroVoiceGenerator"

    def test_kokoro_not_installed_falls_back_to_auto(self):
        with _with_engine(TtsEngine.KOKORO):
            with patch("app.audio.kokoro.is_kokoro_available", return_value=False), \
                 patch("platform.system", return_value="Darwin"), \
                 patch("shutil.which", side_effect=lambda cmd: "/usr/bin/say" if cmd == "say" else None):
                gen = resolve_voice_generator()
        # Fell back to say (auto)
        assert isinstance(gen, SayVoiceGenerator)

    def test_mock_engine_returns_none(self):
        with _with_engine(TtsEngine.MOCK):
            gen = resolve_voice_generator()
        assert gen is None


# ── Voice catalogue ───────────────────────────────────────────────────────────

class TestVoicesCatalogue:
    def test_kokoro_voices(self):
        voices = voices_for_engine("kokoro")
        assert voices == KOKORO_VOICES
        assert any(v["value"] == "af_heart" for v in voices)

    def test_say_voices(self):
        voices = voices_for_engine("say")
        assert voices == SAY_VOICES

    def test_espeak_voices(self):
        voices = voices_for_engine("espeak")
        assert voices == ESPEAK_VOICES

    def test_all_voices_have_value_and_label(self):
        for engine in ("kokoro", "say", "espeak"):
            for v in voices_for_engine(engine):
                assert "value" in v and "label" in v, f"Missing fields in {engine} voice: {v}"


# ── /audio/voices endpoint ────────────────────────────────────────────────────

class TestVoicesEndpoint:
    def test_voices_endpoint_requires_auth(self, client):
        res = client.get("/api/v1/audio/voices")
        assert res.status_code == 401

    def test_voices_endpoint_returns_engine_and_list(self, client, auth_headers):
        res = client.get("/api/v1/audio/voices", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert "engine" in body
        assert isinstance(body["voices"], list)
        assert len(body["voices"]) > 0
        first = body["voices"][0]
        assert "value" in first and "label" in first

    def test_voices_endpoint_kokoro_returns_kokoro_list(self, client, auth_headers):
        from app.core.config import settings
        old = settings.tts_engine
        settings.tts_engine = TtsEngine.KOKORO
        try:
            res = client.get("/api/v1/audio/voices", headers=auth_headers)
            assert res.status_code == 200
            body = res.json()
            assert body["engine"] == "kokoro"
            values = [v["value"] for v in body["voices"]]
            assert "af_heart" in values
            assert "am_michael" in values
        finally:
            settings.tts_engine = old
