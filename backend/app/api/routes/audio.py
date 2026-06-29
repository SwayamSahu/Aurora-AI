"""Audio-related metadata endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.audio.voices import voices_for_engine
from app.core.config import settings

router = APIRouter(prefix="/audio", tags=["audio"])


class VoiceInfo(BaseModel):
    value: str
    label: str


class VoicesResponse(BaseModel):
    engine: str
    voices: list[VoiceInfo]


@router.get("/voices", response_model=VoicesResponse)
def list_voices(current_user: CurrentUser) -> VoicesResponse:
    """Return the voice list for the currently configured TTS engine.

    The frontend uses this to populate the voiceover voice dropdown so it
    always matches the server's actual engine — no hardcoded lists needed.
    """
    engine = settings.tts_engine.value
    raw = voices_for_engine(engine)
    return VoicesResponse(
        engine=engine,
        voices=[VoiceInfo(**v) for v in raw],
    )
