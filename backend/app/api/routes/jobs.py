from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.db.models import Asset, Job
from app.db.models.job import JobStatus, JobType
from app.schemas.asset import AssetRead
from app.schemas.job import JobCreate, JobRead
from app.services import (
    asset_service,
    job_runner,
    job_service,
    model_service,
    project_service,
)
from app.services.marketplace_errors import InsufficientCreditsError

router = APIRouter(tags=["jobs"])

SUPPORTED_TYPES = {
    JobType.GENERATE_VIDEO,
    JobType.GENERATE_IMAGE,
    JobType.TTS,
    JobType.TRANSCRIBE,
    JobType.MUSIC,
}

# Required param per job type.
REQUIRED_PARAM = {
    JobType.GENERATE_VIDEO: "prompt",
    JobType.GENERATE_IMAGE: "prompt",
    JobType.MUSIC: "prompt",
    JobType.TTS: "text",
    JobType.TRANSCRIBE: "asset_id",
}


def _to_read(db: DbSession, job: Job) -> JobRead:
    data = JobRead.model_validate(job)
    if job.result_asset_id:
        asset = db.get(Asset, job.result_asset_id)
        if asset is not None:
            ar = AssetRead.model_validate(asset)
            ar.url = asset_service.content_url(asset.id)
            data.result_asset = ar
    return data


def _dispatch(db: DbSession, job: Job) -> None:
    """Run inline (eager/dev/tests) or enqueue on Celery (worker)."""
    if settings.celery_task_always_eager:
        job_runner.run_generation(db, job)
        db.refresh(job)
    else:
        from app.workers.generation_tasks import run_generation_job

        result = run_generation_job.delay(job.id)
        job.task_id = result.id
        db.commit()
        db.refresh(job)


def _price_video_model(db: DbSession, params: dict) -> tuple[str | None, int]:
    """Validates a named video model (exists, enabled) and returns
    `(model_id, credit_cost)`. Omitting `model` is allowed — the generator
    uses its own default and the request is unmetered (cost 0)."""
    model_id = (params or {}).get("model")
    if not model_id:
        return None, 0
    spec = model_service.get_effective_model(db, model_id)
    if spec is None or not spec.enabled:
        raise HTTPException(
            status_code=422, detail=f"Unknown or unavailable model '{model_id}'."
        )
    return model_id, spec.credit_cost


def _create_and_charge(
    db: DbSession, project_id: str, owner_id: str, job_type: JobType, params: dict
) -> Job:
    """Validates + prices a named video model, then debits the owner's wallet
    and creates the job atomically (the charge and the job row share one
    transaction — see `job_service.create_charged`, so the wallet can never be
    debited without a job to refund against). Raises 402 if the wallet can't
    cover it — nothing is written in that case."""
    credit_cost = 0
    note = ""
    if job_type == JobType.GENERATE_VIDEO:
        model_id, credit_cost = _price_video_model(db, params)
        note = f"Video generation with {model_id}"
    try:
        return job_service.create_charged(
            db,
            project_id,
            job_type,
            params,
            owner_id=owner_id,
            credit_cost=credit_cost,
            note=note,
        )
    except InsufficientCreditsError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc


@router.post("/projects/{project_id}/jobs", response_model=JobRead, status_code=201)
def create_job(
    project_id: str,
    data: JobCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> JobRead:
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    if data.type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Job type '{data.type.value}' is not available yet.",
        )
    required = REQUIRED_PARAM[data.type]
    if not (data.params or {}).get(required):
        raise HTTPException(
            status_code=422, detail=f"'{required}' is required for this job."
        )

    job = _create_and_charge(db, project_id, current_user.id, data.type, data.params)
    _dispatch(db, job)
    return _to_read(db, job)


@router.get("/jobs", response_model=list[JobRead])
def list_jobs(
    current_user: CurrentUser,
    db: DbSession,
    project_id: Annotated[str | None, Query()] = None,
    status: Annotated[JobStatus | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[JobRead]:
    jobs = job_service.list_for_owner(
        db, current_user.id, project_id=project_id, status=status, limit=limit
    )
    return [_to_read(db, j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: str, current_user: CurrentUser, db: DbSession) -> JobRead:
    job = job_service.get_for_owner(db, current_user.id, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return _to_read(db, job)


@router.post("/jobs/{job_id}/retry", response_model=JobRead, status_code=201)
def retry_job(job_id: str, current_user: CurrentUser, db: DbSession) -> JobRead:
    old = job_service.get_for_owner(db, current_user.id, job_id)
    if old is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    # Create a fresh job with the same params (keeps history of the failure).
    # Billed the same as a first attempt — a retry is a real new generation.
    job = _create_and_charge(
        db, old.project_id, current_user.id, old.type, old.params
    )
    _dispatch(db, job)
    return _to_read(db, job)


@router.post("/jobs/{job_id}/cancel", response_model=JobRead)
def cancel_job(job_id: str, current_user: CurrentUser, db: DbSession) -> JobRead:
    job = job_service.get_for_owner(db, current_user.id, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status in {JobStatus.SUCCEEDED, JobStatus.FAILED}:
        raise HTTPException(status_code=409, detail="Job already finished.")
    # Best-effort revoke for queued Celery tasks.
    if job.task_id and not settings.celery_task_always_eager:
        from app.core.celery_app import celery_app

        celery_app.control.revoke(job.task_id, terminate=False)
    job_service.set_progress(db, job, job.progress, status=JobStatus.CANCELLED)
    return _to_read(db, job)
