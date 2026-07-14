"""Admin-editable overrides on top of the static video-model catalog.

The catalog itself (`app.generators.model_catalog.MODEL_CATALOG`) is code —
editing it means shipping a change. Two knobs an admin needs to tune without
a redeploy — whether a model is offered at all, and its credit price — are
instead stored in the generic `platform_settings` key/value table (the same
extensibility point the marketplace platform fee uses), keyed
`model_override:{model_id}`, value a small JSON blob `{"enabled": bool,
"credit_cost": int}`. A missing key means "use the catalog default."

Every route that resolves a model for a *live* decision (serving the picker,
validating a job, pricing a debit) should go through this module rather than
`model_catalog` directly, so admin overrides are always honored.
"""

from __future__ import annotations

import json
import logging
from dataclasses import replace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PlatformSetting
from app.generators.model_catalog import MODEL_CATALOG, ModelSpec, get_model

logger = logging.getLogger(__name__)

_OVERRIDE_PREFIX = "model_override:"


def _override_key(model_id: str) -> str:
    return f"{_OVERRIDE_PREFIX}{model_id}"


def _read_override(db: Session, model_id: str) -> dict | None:
    row = db.scalar(
        select(PlatformSetting).where(PlatformSetting.key == _override_key(model_id))
    )
    if row is None:
        return None
    try:
        return json.loads(row.value)
    except (ValueError, TypeError):
        # A corrupted override row degrades gracefully to catalog defaults, but
        # log it — silently ignoring means a model could e.g. silently re-enable
        # itself, with nothing pointing an operator at the bad row.
        logger.warning(
            "Ignoring corrupted model override for '%s' (key '%s'): %r",
            model_id,
            _override_key(model_id),
            row.value,
        )
        return None


def _apply_override(spec: ModelSpec, override: dict | None) -> ModelSpec:
    if not override:
        return spec
    patch = {}
    if "enabled" in override:
        patch["enabled"] = bool(override["enabled"])
    if "credit_cost" in override:
        patch["credit_cost"] = int(override["credit_cost"])
    return replace(spec, **patch) if patch else spec


def get_effective_model(db: Session, model_id: str) -> ModelSpec | None:
    """The model's catalog spec with any admin override applied. `None` if
    `model_id` isn't in the catalog at all (overrides can't invent models)."""
    spec = get_model(model_id)
    if spec is None:
        return None
    return _apply_override(spec, _read_override(db, model_id))


def list_effective_models(db: Session, *, enabled_only: bool = True) -> list[ModelSpec]:
    models = [_apply_override(m, _read_override(db, m.id)) for m in MODEL_CATALOG]
    if enabled_only:
        models = [m for m in models if m.enabled]
    return models


def is_overridden(db: Session, model_id: str) -> bool:
    return _read_override(db, model_id) is not None


def set_override(
    db: Session,
    model_id: str,
    *,
    enabled: bool | None = None,
    credit_cost: int | None = None,
) -> ModelSpec:
    """Set (or update) an admin override. Only the passed fields change —
    omitting one leaves its previous override (or the catalog default) intact.
    Raises `ValueError` if `model_id` isn't a real catalog entry."""
    if get_model(model_id) is None:
        raise ValueError(f"Unknown model '{model_id}'.")
    if credit_cost is not None and credit_cost <= 0:
        raise ValueError("credit_cost must be positive.")

    current = _read_override(db, model_id) or {}
    if enabled is not None:
        current["enabled"] = enabled
    if credit_cost is not None:
        current["credit_cost"] = credit_cost

    key = _override_key(model_id)
    row = db.scalar(select(PlatformSetting).where(PlatformSetting.key == key))
    value = json.dumps(current)
    if row is None:
        row = PlatformSetting(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    db.commit()

    return get_effective_model(db, model_id)  # type: ignore[return-value]


def clear_override(db: Session, model_id: str) -> ModelSpec | None:
    """Remove any admin override, reverting the model to its catalog default."""
    row = db.scalar(
        select(PlatformSetting).where(PlatformSetting.key == _override_key(model_id))
    )
    if row is not None:
        db.delete(row)
        db.commit()
    return get_effective_model(db, model_id)
