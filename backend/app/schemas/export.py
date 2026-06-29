from __future__ import annotations

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    width: int = Field(default=1280, ge=128, le=3840)
    height: int = Field(default=720, ge=72, le=2160)
    fps: int = Field(default=24, ge=1, le=60)
    crf: int = Field(default=23, ge=0, le=51)
    fade_duration: float = Field(default=0.5, ge=0.0, le=3.0)
