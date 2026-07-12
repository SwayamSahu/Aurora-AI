"""Content reporting: any authenticated user can flag a blog post/comment
or marketplace listing/comment for moderator review."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession
from app.db.models import ReportReason
from app.schemas.report import ReportCreate, ReportRead
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportRead, status_code=201)
def create_report(
    data: ReportCreate, current_user: CurrentUser, db: DbSession
) -> ReportRead:
    try:
        report = report_service.create_report(
            db,
            reporter_id=current_user.id,
            target_type=data.target_type,
            target_id=data.target_id,
            reason=ReportReason(data.reason),
            note=data.note,
        )
    except report_service.InvalidTargetError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except report_service.DuplicateReportError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return ReportRead(**report_service.serialize(db, report))
