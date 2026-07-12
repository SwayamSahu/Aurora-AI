from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.services.report_service import USER_REPORTABLE_TARGET_TYPES


class DmcaRequestCreate(BaseModel):
    claimant_name: str = Field(min_length=1, max_length=200)
    claimant_email: EmailStr
    target_type: str
    target_id: str
    work_description: str = Field(min_length=1, max_length=2000)
    good_faith_statement: bool
    signature: str = Field(min_length=1, max_length=200)

    @field_validator("target_type")
    @classmethod
    def target_type_is_valid(cls, value: str) -> str:
        if value not in USER_REPORTABLE_TARGET_TYPES:
            raise ValueError(
                f"target_type must be one of {sorted(USER_REPORTABLE_TARGET_TYPES)}."
            )
        return value

    @field_validator("good_faith_statement")
    @classmethod
    def must_affirm(cls, value: bool) -> bool:
        if not value:
            raise ValueError("The good-faith statement must be affirmed.")
        return value


class DmcaResolve(BaseModel):
    status: str
    resolution_note: str | None = Field(default=None, max_length=500)

    @field_validator("status")
    @classmethod
    def status_is_valid(cls, value: str) -> str:
        if value not in ("content_removed", "rejected"):
            raise ValueError("status must be 'content_removed' or 'rejected'.")
        return value


class DmcaResolvedBy(BaseModel):
    id: str
    email: str
    full_name: str | None


class DmcaRequestRead(BaseModel):
    id: str
    claimant_name: str
    claimant_email: str
    target_type: str
    target_id: str
    target_preview: dict | None
    work_description: str
    status: str
    resolution_note: str | None
    resolved_by: DmcaResolvedBy | None
    created_at: datetime


class DmcaListResponse(BaseModel):
    items: list[DmcaRequestRead]
    total: int
    next_offset: int | None = None
