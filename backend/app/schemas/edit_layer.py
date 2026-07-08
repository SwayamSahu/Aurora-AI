from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.edit_layer import EditLayerStatus
from app.schemas.asset import AssetRead


class EditLayerCreate(BaseModel):
    clip_id: str
    engine: str
    preset_id: str | None = None
    label: str = ""
    prompt: str = ""
    params: dict = Field(default_factory=dict)
    source_asset_id: str | None = None
    # PNG mask as a data URL or base64 string (white = edit region).
    mask_base64: str | None = None


class EditLayerUpdate(BaseModel):
    enabled: bool | None = None
    position: int | None = None
    prompt: str | None = None


class EditLayerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    clip_id: str
    engine: str
    preset_id: str | None
    label: str
    prompt: str
    params: dict
    status: EditLayerStatus
    progress: float
    error: str | None
    position: int
    enabled: bool
    result_asset_id: str | None
    # Hydrated so the compare slider can show the result immediately.
    result_asset: AssetRead | None = None
