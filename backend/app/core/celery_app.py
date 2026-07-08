"""Celery application skeleton.

Task modules (generation, media, transcribe) are registered from Phase 3
onwards. Phase 0 only establishes the broker/result wiring.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "aurora",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.generation_tasks",
        "app.workers.export_tasks",
        "app.workers.edit_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # One GPU job at a time per worker — important on a single 16GB card.
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    # Synchronous in-process execution for Mac dev / tests (no broker needed).
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
)
