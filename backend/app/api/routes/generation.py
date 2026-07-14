from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.generation import VideoModelSpec
from app.services import model_service

router = APIRouter(tags=["generation"])


@router.get("/generation/models", response_model=list[VideoModelSpec])
def list_video_models(db: DbSession) -> list[VideoModelSpec]:
    """The catalog of selectable video-generation models for the Studio,
    with any admin overrides (enable/disable, price) applied."""
    return [
        VideoModelSpec(
            id=m.id,
            label=m.label,
            provider=m.provider,
            kind=m.kind,
            resolution=m.resolution,
            max_width=m.max_width,
            max_height=m.max_height,
            min_duration=m.min_duration,
            max_duration=m.max_duration,
            default_duration=m.default_duration,
            supports_i2v=m.supports_i2v,
            badges=m.badges,
            credit_cost=m.credit_cost,
        )
        for m in model_service.list_effective_models(db)
    ]
