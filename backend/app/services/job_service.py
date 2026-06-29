"""Job persistence and queries, scoped to the owning user via the project."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Job, Project
from app.db.models.job import JobStatus, JobType


def create(
    db: Session, project_id: str, job_type: JobType, params: dict
) -> Job:
    job = Job(
        project_id=project_id,
        type=job_type,
        status=JobStatus.QUEUED,
        progress=0.0,
        params=params or {},
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_for_owner(db: Session, owner_id: str, job_id: str) -> Job | None:
    return db.scalar(
        select(Job)
        .join(Project, Project.id == Job.project_id)
        .where(Job.id == job_id, Project.owner_id == owner_id)
    )


def list_for_owner(
    db: Session,
    owner_id: str,
    *,
    project_id: str | None = None,
    status: JobStatus | None = None,
    limit: int = 100,
) -> list[Job]:
    stmt = (
        select(Job)
        .join(Project, Project.id == Job.project_id)
        .where(Project.owner_id == owner_id)
    )
    if project_id is not None:
        stmt = stmt.where(Job.project_id == project_id)
    if status is not None:
        stmt = stmt.where(Job.status == status)
    stmt = stmt.order_by(Job.created_at.desc()).limit(limit)
    return list(db.scalars(stmt).all())


def set_progress(
    db: Session,
    job: Job,
    progress: float,
    *,
    status: JobStatus | None = None,
) -> None:
    job.progress = max(0.0, min(1.0, progress))
    if status is not None:
        job.status = status
    db.commit()


def mark_failed(db: Session, job: Job, error: str) -> None:
    job.status = JobStatus.FAILED
    job.error = error[:2000]
    db.commit()


def mark_succeeded(db: Session, job: Job, result_asset_id: str) -> None:
    job.status = JobStatus.SUCCEEDED
    job.progress = 1.0
    job.result_asset_id = result_asset_id
    job.error = None
    db.commit()
