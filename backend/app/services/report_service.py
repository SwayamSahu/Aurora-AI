"""Content reports: any user can flag a blog post/comment or marketplace
listing/comment; moderators triage them in the admin console. Targets are
looked up live (via the owning service) rather than duplicated here, so a
report's preview always reflects the target's current state — and reports
against deleted content still list, just with no preview."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Report, ReportReason, ReportStatus
from app.services import blog_service, listing_service

TARGET_TYPES = frozenset(
    {
        "blog_post",
        "blog_comment",
        "blog_media",
        "listing",
        "listing_comment",
        "listing_media",
    }
)
# Media targets only exist for the automated content-safety scan (a raw
# upload has no title/body a human reporter could reference) — excluded
# from the user-facing report form's allowed set.
USER_REPORTABLE_TARGET_TYPES = TARGET_TYPES - {"blog_media", "listing_media"}


class InvalidTargetError(Exception):
    pass


class DuplicateReportError(Exception):
    pass


def _target_exists(db: Session, target_type: str, target_id: str) -> bool:
    if target_type == "blog_post":
        return blog_service.get_by_id(db, target_id) is not None
    if target_type == "blog_comment":
        return blog_service.get_comment(db, target_id) is not None
    if target_type == "blog_media":
        return blog_service.get_media(db, target_id) is not None
    if target_type == "listing":
        return listing_service.get_by_id(db, target_id) is not None
    if target_type == "listing_comment":
        return listing_service.get_comment(db, target_id) is not None
    if target_type == "listing_media":
        return listing_service.get_media(db, target_id) is not None
    return False


def get_target_preview(db: Session, target_type: str, target_id: str) -> dict | None:
    """A short human-readable summary of the reported content, for the
    admin queue — `None` if the target no longer exists."""
    if target_type == "blog_post":
        post = blog_service.get_by_id(db, target_id)
        return {"title": post.title, "deleted": False} if post else None
    if target_type == "blog_comment":
        comment = blog_service.get_comment(db, target_id)
        return {"title": comment.body[:80], "deleted": False} if comment else None
    if target_type == "blog_media":
        media = blog_service.get_media(db, target_id)
        return {"title": f"Uploaded image ({media.content_type})", "deleted": False} if media else None
    if target_type == "listing":
        listing = listing_service.get_by_id(db, target_id)
        return {"title": listing.title, "deleted": False} if listing else None
    if target_type == "listing_comment":
        comment = listing_service.get_comment(db, target_id)
        return {"title": comment.body[:80], "deleted": False} if comment else None
    if target_type == "listing_media":
        media = listing_service.get_media(db, target_id)
        return {"title": f"Uploaded image ({media.content_type})", "deleted": False} if media else None
    return None


def create_report(
    db: Session,
    *,
    reporter_id: str | None,
    target_type: str,
    target_id: str,
    reason: ReportReason,
    note: str | None,
) -> Report:
    """`reporter_id=None` records a system-generated report (the automated
    content-safety scan) — same queue, same triage flow, just no human
    reporter to credit."""
    if target_type not in TARGET_TYPES:
        raise InvalidTargetError(f"Unknown target type: {target_type}")
    if not _target_exists(db, target_type, target_id):
        raise InvalidTargetError("That content no longer exists.")

    if reporter_id is not None:
        existing = db.scalar(
            select(Report).where(
                Report.reporter_id == reporter_id,
                Report.target_type == target_type,
                Report.target_id == target_id,
                Report.status == ReportStatus.OPEN,
            )
        )
        if existing is not None:
            raise DuplicateReportError("You've already reported this.")

    report = Report(
        reporter_id=reporter_id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        note=note,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_reports(
    db: Session,
    *,
    status: ReportStatus | None = None,
    target_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Report], int]:
    stmt = select(Report)
    if status is not None:
        stmt = stmt.where(Report.status == status)
    if target_type is not None:
        stmt = stmt.where(Report.target_type == target_type)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.options(selectinload(Report.reporter))
        .order_by(Report.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = list(db.scalars(stmt))
    return items, total


def get_report(db: Session, report_id: str) -> Report | None:
    return db.get(Report, report_id)


def resolve_report(
    db: Session,
    report: Report,
    *,
    status: ReportStatus,
    resolution_note: str | None,
    resolved_by_id: str,
) -> Report:
    report.status = status
    report.resolution_note = resolution_note
    report.resolved_by_id = resolved_by_id
    report.resolved_at = datetime.now(UTC)
    db.commit()
    db.refresh(report)
    return report


def serialize(db: Session, report: Report) -> dict:
    """Plain-dict view for `ReportRead` — looks up the reporter and a live
    target preview so routes don't have to."""
    preview = get_target_preview(db, report.target_type, report.target_id)
    reporter = report.reporter
    return {
        "id": report.id,
        "reporter": (
            {"id": reporter.id, "email": reporter.email, "full_name": reporter.full_name}
            if reporter
            else None
        ),
        "target_type": report.target_type,
        "target_id": report.target_id,
        "target_preview": preview,
        "reason": report.reason.value,
        "note": report.note,
        "status": report.status.value,
        "resolution_note": report.resolution_note,
        "resolved_at": report.resolved_at,
        "created_at": report.created_at,
    }
