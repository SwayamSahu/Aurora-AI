from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ClipKind = Literal["video", "image", "audio", "text"]
TrackType = Literal["video", "text", "audio"]


class TimelineClip(BaseModel):
    # Permissive: the editor may attach extra UI fields we don't need to model.
    model_config = ConfigDict(extra="allow")

    id: str
    kind: ClipKind
    asset_id: str | None = None
    # Position on the timeline and length, in seconds.
    start: float = 0.0
    duration: float = 1.0
    # In-point within the source media (for trimming), in seconds.
    trim_start: float = 0.0
    # Transition applied at the start of this clip (when adjacent to the previous).
    # Matches FFmpeg xfade transition names: "fade", "dissolve", "wipeleft",
    # "wiperight", "slideleft", "slideright", etc.  None / "none" = hard cut.
    transition_in: str | None = None
    # Text-clip fields.
    text: str | None = None
    style: dict = Field(default_factory=dict)


class TimelineTrack(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    type: TrackType
    name: str
    clips: list[TimelineClip] = Field(default_factory=list)
    muted: bool = False


class TimelineDocument(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: int = 1
    tracks: list[TimelineTrack] = Field(default_factory=list)


class TimelineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    version: int
    document: TimelineDocument
    updated_at: datetime
