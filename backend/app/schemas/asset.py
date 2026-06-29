from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.asset import AssetKind, AssetSource


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    name: str
    kind: AssetKind
    source: AssetSource
    content_type: str
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    created_at: datetime
    # Relative API path to stream the bytes; the client prefixes the API base.
    url: str = ""


class AssetUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
