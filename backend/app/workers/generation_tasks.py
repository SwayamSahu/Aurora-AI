"""Celery tasks for generation jobs.

The task opens its own DB session (worker process) and delegates to the pure
`run_generation` orchestrator. Inline/eager execution (dev/tests) calls
`run_generation` directly with the request session instead — see the jobs API.
"""

from __future__ import annotations

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.services import job_runner


@celery_app.task(name="aurora.run_generation_job")
def run_generation_job(job_id: str) -> str:
    from app.db.models import Job  # local import to avoid circulars at load

    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return "missing"
        job_runner.run_generation(db, job)
        return job.status.value
    finally:
        db.close()
