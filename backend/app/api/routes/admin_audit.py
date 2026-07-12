"""Audit log viewer — spans all admin/moderator actions (blog + marketplace).
Admin-only, since the log itself is sensitive; read-only, since the log is
append-only (no edit/delete anywhere)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DbSession
from app.schemas.audit import AdminActionRead, AuditLogResponse
from app.services import audit_service

router = APIRouter(prefix="/admin/audit", tags=["admin"])


@router.get("", response_model=AuditLogResponse)
def list_audit_log(
    admin: AdminUser,
    db: DbSession,
    actor_id: Annotated[str | None, Query()] = None,
    action: Annotated[str | None, Query()] = None,
    target_type: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AuditLogResponse:
    items, total = audit_service.list_actions(
        db,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        limit=limit,
        offset=offset,
    )
    next_offset = offset + limit if offset + limit < total else None
    return AuditLogResponse(
        items=[AdminActionRead.model_validate(a) for a in items],
        total=total,
        next_offset=next_offset,
    )
