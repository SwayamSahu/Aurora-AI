from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditActor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str | None = None
    email: str


class AdminActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor: AuditActor | None
    action: str
    target_type: str
    target_id: str | None
    action_metadata: dict
    created_at: datetime


class AuditLogResponse(BaseModel):
    items: list[AdminActionRead]
    total: int
    next_offset: int | None = None
