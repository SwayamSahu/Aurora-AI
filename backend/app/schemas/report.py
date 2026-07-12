from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.services.report_service import TARGET_TYPES


class ReportCreate(BaseModel):
    target_type: str
    target_id: str
    reason: str
    note: str | None = Field(default=None, max_length=500)

    @field_validator("target_type")
    @classmethod
    def target_type_is_valid(cls, value: str) -> str:
        if value not in TARGET_TYPES:
            raise ValueError(f"target_type must be one of {sorted(TARGET_TYPES)}.")
        return value

    @field_validator("reason")
    @classmethod
    def reason_is_valid(cls, value: str) -> str:
        allowed = {"spam", "abuse", "inappropriate", "copyright", "other"}
        if value not in allowed:
            raise ValueError(f"reason must be one of {sorted(allowed)}.")
        return value


class ReportResolve(BaseModel):
    status: str
    resolution_note: str | None = Field(default=None, max_length=500)

    @field_validator("status")
    @classmethod
    def status_is_valid(cls, value: str) -> str:
        if value not in ("resolved", "dismissed"):
            raise ValueError("status must be 'resolved' or 'dismissed'.")
        return value


class ReportReporter(BaseModel):
    id: str
    email: str
    full_name: str | None


class ReportTargetPreview(BaseModel):
    title: str
    deleted: bool = False


class ReportRead(BaseModel):
    id: str
    reporter: ReportReporter | None
    target_type: str
    target_id: str
    target_preview: ReportTargetPreview | None
    reason: str
    note: str | None
    status: str
    resolution_note: str | None
    resolved_at: datetime | None
    created_at: datetime


class ReportListResponse(BaseModel):
    items: list[ReportRead]
    total: int
    next_offset: int | None = None
