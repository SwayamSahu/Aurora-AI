"""Report triage queue — open to moderators and admins, matching the rest
of content moderation (see `ModeratorUser` in `app.api.deps`)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession, ModeratorUser
from app.db.models import ReportStatus
from app.schemas.report import ReportListResponse, ReportRead, ReportResolve
from app.services import audit_service, report_service

router = APIRouter(prefix="/admin/reports", tags=["admin"])


@router.get("", response_model=ReportListResponse)
def list_reports(
    moderator: ModeratorUser,
    db: DbSession,
    status: Annotated[str | None, Query()] = None,
    target_type: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ReportListResponse:
    status_filter = ReportStatus(status) if status else None
    reports, total = report_service.list_reports(
        db, status=status_filter, target_type=target_type, limit=limit, offset=offset
    )
    next_offset = offset + limit if offset + limit < total else None
    return ReportListResponse(
        items=[ReportRead(**report_service.serialize(db, r)) for r in reports],
        total=total,
        next_offset=next_offset,
    )


@router.patch("/{report_id}", response_model=ReportRead)
def resolve_report(
    report_id: str, data: ReportResolve, moderator: ModeratorUser, db: DbSession
) -> ReportRead:
    report = report_service.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    report = report_service.resolve_report(
        db,
        report,
        status=ReportStatus(data.status),
        resolution_note=data.resolution_note,
        resolved_by_id=moderator.id,
    )
    audit_service.record(
        db,
        actor_id=moderator.id,
        action=f"report.{data.status}",
        target_type="report",
        target_id=report.id,
        metadata={
            "reported_target_type": report.target_type,
            "reported_target_id": report.target_id,
            "resolution_note": data.resolution_note,
        },
    )
    return ReportRead(**report_service.serialize(db, report))
