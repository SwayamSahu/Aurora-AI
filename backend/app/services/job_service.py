"""Job persistence and queries, scoped to the owning user via the project."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Job, Project, TransactionType
from app.db.models.job import JobStatus, JobType
from app.services import wallet_service


def create(
    db: Session,
    project_id: str,
    job_type: JobType,
    params: dict,
    *,
    credits_charged: int = 0,
) -> Job:
    job = Job(
        project_id=project_id,
        type=job_type,
        status=JobStatus.QUEUED,
        progress=0.0,
        params=params or {},
        credits_charged=credits_charged,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def create_charged(
    db: Session,
    project_id: str,
    job_type: JobType,
    params: dict,
    *,
    owner_id: str,
    credit_cost: int,
    note: str,
) -> Job:
    """Debit the owner's wallet and create the job in a SINGLE transaction, so
    a charge can never persist without its job (and vice versa). Raises
    `InsufficientCreditsError` — before anything is written — if the balance
    can't cover `credit_cost`. `credit_cost == 0` skips the debit entirely,
    making this equivalent to `create`."""
    if credit_cost > 0:
        wallet = wallet_service.get_wallet_locked(db, owner_id)
        # No commit here — the debit and the job insert below land in one
        # commit, so a failure in between rolls back both.
        wallet_service.debit(
            db, wallet, credit_cost, TransactionType.GENERATION_SPEND, note=note
        )
    job = Job(
        project_id=project_id,
        type=job_type,
        status=JobStatus.QUEUED,
        progress=0.0,
        params=params or {},
        credits_charged=credit_cost,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def refund_credits(db: Session, job: Job) -> None:
    """Refunds `job.credits_charged` back to the owning project's wallet —
    called when a billed generation job fails — and zeroes it out so the
    same failure can't be refunded twice (e.g. a retry-triggered refund path
    running again). No-op if the job was never charged or the owning project
    no longer exists (deleting a project cascade-deletes its jobs, so a
    charged job can't reach that state through the normal flow)."""
    if job.credits_charged <= 0:
        return
    project = db.get(Project, job.project_id)
    if project is None:
        return
    wallet = wallet_service.get_wallet_locked(db, project.owner_id)
    wallet_service.credit(
        db,
        wallet,
        job.credits_charged,
        TransactionType.REFUND,
        note=f"Refund for failed generation job {job.id}",
    )
    job.credits_charged = 0
    db.commit()


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
