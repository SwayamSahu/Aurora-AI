"""DMCA takedown triage — moderator-gated like the general report queue.
Resolving with `content_removed` actually takes the content down
(unpublish/delist/hide); `rejected` just closes the request out."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession, ModeratorUser
from app.db.models import DmcaStatus
from app.schemas.dmca import DmcaListResponse, DmcaRequestRead, DmcaResolve
from app.services import audit_service, dmca_service

router = APIRouter(prefix="/admin/dmca", tags=["admin"])


@router.get("", response_model=DmcaListResponse)
def list_dmca_requests(
    moderator: ModeratorUser,
    db: DbSession,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DmcaListResponse:
    status_filter = DmcaStatus(status) if status else None
    requests, total = dmca_service.list_requests(
        db, status=status_filter, limit=limit, offset=offset
    )
    next_offset = offset + limit if offset + limit < total else None
    return DmcaListResponse(
        items=[DmcaRequestRead(**dmca_service.serialize(db, r)) for r in requests],
        total=total,
        next_offset=next_offset,
    )


@router.patch("/{request_id}", response_model=DmcaRequestRead)
def resolve_dmca_request(
    request_id: str, data: DmcaResolve, moderator: ModeratorUser, db: DbSession
) -> DmcaRequestRead:
    request = dmca_service.get_request(db, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="DMCA request not found.")

    request = dmca_service.resolve_request(
        db,
        request,
        status=DmcaStatus(data.status),
        resolution_note=data.resolution_note,
        resolved_by_id=moderator.id,
    )
    audit_service.record(
        db,
        actor_id=moderator.id,
        action=f"dmca.{data.status}",
        target_type="dmca_request",
        target_id=request.id,
        metadata={
            "target_type": request.target_type,
            "target_id": request.target_id,
            "resolution_note": data.resolution_note,
        },
    )
    return DmcaRequestRead(**dmca_service.serialize(db, request))
