"""Admin console: video-model catalog management. An admin can disable a
model (e.g. a provider outage) or re-price it without a redeploy — see
`app.services.model_service` for how the override is stored and merged with
the static catalog."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import AdminUser, DbSession
from app.generators.model_catalog import ModelSpec
from app.schemas.generation import AdminModelRead, AdminModelUpdate
from app.services import audit_service, model_service

router = APIRouter(prefix="/admin/models", tags=["admin"])


def _to_read(spec: ModelSpec, *, is_overridden: bool) -> AdminModelRead:
    return AdminModelRead(
        id=spec.id,
        label=spec.label,
        provider=spec.provider,
        kind=spec.kind,
        resolution=spec.resolution,
        max_width=spec.max_width,
        max_height=spec.max_height,
        min_duration=spec.min_duration,
        max_duration=spec.max_duration,
        default_duration=spec.default_duration,
        supports_i2v=spec.supports_i2v,
        badges=spec.badges,
        credit_cost=spec.credit_cost,
        enabled=spec.enabled,
        is_overridden=is_overridden,
    )


@router.get("", response_model=list[AdminModelRead])
def list_models(admin: AdminUser, db: DbSession) -> list[AdminModelRead]:
    """Every catalog model (including disabled ones), with its effective
    price/availability and whether an admin override is currently applied."""
    return [
        _to_read(spec, is_overridden=model_service.is_overridden(db, spec.id))
        for spec in model_service.list_effective_models(db, enabled_only=False)
    ]


@router.patch("/{model_id}", response_model=AdminModelRead)
def update_model(
    model_id: str, data: AdminModelUpdate, admin: AdminUser, db: DbSession
) -> AdminModelRead:
    try:
        spec = model_service.set_override(
            db, model_id, enabled=data.enabled, credit_cost=data.credit_cost
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    audit_service.record(
        db,
        actor_id=admin.id,
        action="model.override_update",
        target_type="video_model",
        target_id=model_id,
        metadata={"enabled": spec.enabled, "credit_cost": spec.credit_cost},
    )
    return _to_read(spec, is_overridden=True)


@router.delete("/{model_id}/override", response_model=AdminModelRead)
def clear_model_override(model_id: str, admin: AdminUser, db: DbSession) -> AdminModelRead:
    """Reverts a model to its catalog defaults, discarding any admin override."""
    spec = model_service.clear_override(db, model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Unknown model '{model_id}'.")

    audit_service.record(
        db,
        actor_id=admin.id,
        action="model.override_clear",
        target_type="video_model",
        target_id=model_id,
    )
    return _to_read(spec, is_overridden=False)
