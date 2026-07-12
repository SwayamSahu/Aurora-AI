"""Revenue/analytics dashboard — admin-only financial reporting."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DbSession
from app.schemas.admin import RevenueSummary
from app.services import analytics_service

router = APIRouter(prefix="/admin/analytics", tags=["admin"])


@router.get("/revenue", response_model=RevenueSummary)
def get_revenue(
    admin: AdminUser,
    db: DbSession,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> RevenueSummary:
    return RevenueSummary(**analytics_service.get_revenue_summary(db, days=days))
