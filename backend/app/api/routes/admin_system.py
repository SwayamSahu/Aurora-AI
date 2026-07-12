"""Admin system-health dashboard — admin-only, since it surfaces
infrastructure details (DB/Redis latency, storage backend)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.services import system_health_service

router = APIRouter(prefix="/admin/system", tags=["admin"])


@router.get("/health")
def get_system_health(admin: AdminUser, db: DbSession) -> dict:
    return system_health_service.get_system_health(db)
