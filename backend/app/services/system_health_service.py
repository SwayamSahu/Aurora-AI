"""Admin system-health dashboard: liveness of the DB/Redis/storage
dependencies plus a handful of platform-scale counts. Each dependency check
is independent and never raises — a failed check reports `ok=False` with
the error message rather than 500ing the whole dashboard."""

from __future__ import annotations

import time

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import (
    BlogPost,
    BlogStatus,
    Job,
    JobStatus,
    Listing,
    ListingStatus,
    Order,
    Report,
    ReportStatus,
    User,
)


def _check_database(db: Session) -> dict:
    started = time.monotonic()
    try:
        db.execute(text("SELECT 1"))
        return {"ok": True, "latency_ms": round((time.monotonic() - started) * 1000, 1)}
    except Exception as exc:  # noqa: BLE001 — surfaced as a status field, not raised
        return {"ok": False, "error": str(exc)}


def _check_redis() -> dict:
    started = time.monotonic()
    try:
        import redis  # noqa: PLC0415

        client = redis.from_url(settings.redis_url, socket_connect_timeout=2)
        client.ping()
        return {"ok": True, "latency_ms": round((time.monotonic() - started) * 1000, 1)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def _check_storage() -> dict:
    started = time.monotonic()
    try:
        from app.storage import get_storage  # noqa: PLC0415

        get_storage()
        return {"ok": True, "latency_ms": round((time.monotonic() - started) * 1000, 1)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def get_system_health(db: Session) -> dict:
    since_recent_jobs = (
        db.scalar(
            select(func.count()).where(Job.status == JobStatus.FAILED)
        )
        or 0
    )
    total_jobs = db.scalar(select(func.count(Job.id))) or 0

    return {
        "database": _check_database(db),
        "redis": _check_redis(),
        "storage": _check_storage(),
        "counts": {
            "total_users": db.scalar(select(func.count(User.id))) or 0,
            "active_listings": db.scalar(
                select(func.count(Listing.id)).where(
                    Listing.status == ListingStatus.ACTIVE
                )
            )
            or 0,
            "published_posts": db.scalar(
                select(func.count(BlogPost.id)).where(
                    BlogPost.status == BlogStatus.PUBLISHED
                )
            )
            or 0,
            "total_orders": db.scalar(select(func.count(Order.id))) or 0,
            "open_reports": db.scalar(
                select(func.count(Report.id)).where(Report.status == ReportStatus.OPEN)
            )
            or 0,
            "failed_jobs": since_recent_jobs,
            "total_jobs": total_jobs,
        },
        "generator_backend": settings.generator_backend.value,
        "environment": settings.environment.value,
    }
