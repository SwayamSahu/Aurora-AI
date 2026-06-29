from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.db.models.job import JobType
from app.schemas.export import ExportRequest
from app.schemas.job import JobRead
from app.services import job_service, project_service

router = APIRouter(tags=["export"])


def _dispatch_export(db: DbSession, job) -> None:
    if settings.celery_task_always_eager:
        from app.media.export_runner import run_export  # noqa: PLC0415
        run_export(db, job)
        db.refresh(job)
    else:
        from app.workers.export_tasks import run_export_job  # noqa: PLC0415
        result = run_export_job.delay(job.id)
        job.task_id = result.id
        db.commit()
        db.refresh(job)


def _to_read(db: DbSession, job) -> JobRead:
    from app.api.routes.jobs import _to_read as jobs_to_read  # noqa: PLC0415
    return jobs_to_read(db, job)


@router.post("/projects/{project_id}/export", response_model=JobRead, status_code=201)
def start_export(
    project_id: str,
    data: ExportRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> JobRead:
    """Compile the project timeline into a final MP4.

    Runs the full FFmpeg render pipeline (clips + captions + audio + fades)
    and stores the result as a derived video asset in the project library.
    """
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    job = job_service.create(
        db,
        project_id,
        JobType.EXPORT,
        data.model_dump(),
    )
    _dispatch_export(db, job)
    return _to_read(db, job)
