from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.job import JobStatus, JobType
from app.schemas.asset import AssetRead


class JobCreate(BaseModel):
    type: JobType
    params: dict = Field(default_factory=dict)


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    type: JobType
    status: JobStatus
    progress: float
    params: dict
    error: str | None = None
    result_asset_id: str | None = None
    created_at: datetime
    updated_at: datetime
    # Populated when the job produced an asset.
    result_asset: AssetRead | None = None


class JobProgressEvent(BaseModel):
    """Shape streamed over the job-progress WebSocket."""

    id: str
    status: JobStatus
    progress: float
    error: str | None = None
    result_asset_id: str | None = None
