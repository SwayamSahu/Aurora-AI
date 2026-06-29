"""Celery task for export jobs."""

from __future__ import annotations

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.media.export_runner import run_export


@celery_app.task(name="aurora.run_export_job")
def run_export_job(job_id: str) -> str:
    from app.db.models import Job  # noqa: PLC0415

    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return "missing"
        run_export(db, job)
        return job.status.value
    finally:
        db.close()
