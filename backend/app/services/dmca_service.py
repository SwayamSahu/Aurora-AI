"""Formal DMCA takedown notices. `create_request` doesn't require an
account (real claimants often aren't platform users) but does validate the
target exists, reusing `report_service`'s target lookups. Resolving with
`content_removed` takes the target down the same way a moderator would
(unpublish/delist/hide) — reversible, not a hard delete, so a valid
counter-notice can still restore it."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import BlogStatus, DmcaRequest, DmcaStatus
from app.services import blog_service, listing_service, report_service


class InvalidTargetError(Exception):
    pass


def create_request(
    db: Session,
    *,
    claimant_name: str,
    claimant_email: str,
    target_type: str,
    target_id: str,
    work_description: str,
    good_faith_statement: bool,
    signature: str,
) -> DmcaRequest:
    if target_type not in report_service.USER_REPORTABLE_TARGET_TYPES:
        raise InvalidTargetError(f"Unknown target type: {target_type}")
    if report_service.get_target_preview(db, target_type, target_id) is None:
        raise InvalidTargetError("That content no longer exists.")
    if not good_faith_statement:
        raise InvalidTargetError("The good-faith statement must be affirmed.")

    request = DmcaRequest(
        claimant_name=claimant_name,
        claimant_email=claimant_email,
        target_type=target_type,
        target_id=target_id,
        work_description=work_description,
        good_faith_statement=good_faith_statement,
        signature=signature,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def list_requests(
    db: Session,
    *,
    status: DmcaStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[DmcaRequest], int]:
    stmt = select(DmcaRequest)
    if status is not None:
        stmt = stmt.where(DmcaRequest.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.options(selectinload(DmcaRequest.resolved_by))
        .order_by(DmcaRequest.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt)), total


def get_request(db: Session, request_id: str) -> DmcaRequest | None:
    return db.get(DmcaRequest, request_id)


def _take_down(db: Session, target_type: str, target_id: str) -> None:
    if target_type == "blog_post":
        post = blog_service.get_by_id(db, target_id)
        if post is not None and post.status == BlogStatus.PUBLISHED:
            post.status = BlogStatus.DRAFT
            db.commit()
    elif target_type == "blog_comment":
        comment = blog_service.get_comment(db, target_id)
        if comment is not None:
            blog_service.set_comment_hidden(db, comment, True)
    elif target_type == "listing":
        listing = listing_service.get_by_id(db, target_id)
        if listing is not None:
            listing_service.admin_delist(db, listing)
    elif target_type == "listing_comment":
        comment = listing_service.get_comment(db, target_id)
        if comment is not None:
            listing_service.set_comment_hidden(db, comment, True)


def resolve_request(
    db: Session,
    request: DmcaRequest,
    *,
    status: DmcaStatus,
    resolution_note: str | None,
    resolved_by_id: str,
) -> DmcaRequest:
    if status == DmcaStatus.CONTENT_REMOVED:
        _take_down(db, request.target_type, request.target_id)
    request.status = status
    request.resolution_note = resolution_note
    request.resolved_by_id = resolved_by_id
    db.commit()
    db.refresh(request)
    return request


def serialize(db: Session, request: DmcaRequest) -> dict:
    resolver = request.resolved_by
    return {
        "id": request.id,
        "claimant_name": request.claimant_name,
        "claimant_email": request.claimant_email,
        "target_type": request.target_type,
        "target_id": request.target_id,
        "target_preview": report_service.get_target_preview(
            db, request.target_type, request.target_id
        ),
        "work_description": request.work_description,
        "status": request.status.value,
        "resolution_note": request.resolution_note,
        "resolved_by": (
            {"id": resolver.id, "email": resolver.email, "full_name": resolver.full_name}
            if resolver
            else None
        ),
        "created_at": request.created_at,
    }
