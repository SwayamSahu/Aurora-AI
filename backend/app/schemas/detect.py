from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DetectRequest(BaseModel):
    mode: Literal["click", "text"]
    x: float | None = Field(default=None, ge=0, le=1)
    y: float | None = Field(default=None, ge=0, le=1)
    query: str | None = None
    # The clip's source asset — real (CUDA) detection runs on its first frame.
    # Optional: the mock detector ignores it.
    asset_id: str | None = None


class DetectedObjectRead(BaseModel):
    label: str
    x: float
    y: float
    w: float
    h: float
    confidence: float
