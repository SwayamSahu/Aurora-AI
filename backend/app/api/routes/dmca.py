"""Public DMCA takedown submission — no account required, since real
copyright claimants often aren't platform users."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.schemas.dmca import DmcaRequestCreate, DmcaRequestRead
from app.services import dmca_service

router = APIRouter(prefix="/dmca", tags=["dmca"])


@router.post("", response_model=DmcaRequestRead, status_code=201)
def submit_dmca_request(data: DmcaRequestCreate, db: DbSession) -> DmcaRequestRead:
    try:
        request = dmca_service.create_request(
            db,
            claimant_name=data.claimant_name,
            claimant_email=data.claimant_email,
            target_type=data.target_type,
            target_id=data.target_id,
            work_description=data.work_description,
            good_faith_statement=data.good_faith_statement,
            signature=data.signature,
        )
    except dmca_service.InvalidTargetError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return DmcaRequestRead(**dmca_service.serialize(db, request))
