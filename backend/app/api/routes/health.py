from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe + backend introspection."""
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=__version__,
        environment=settings.environment.value,
        generator_backend=settings.generator_backend.value,
    )
