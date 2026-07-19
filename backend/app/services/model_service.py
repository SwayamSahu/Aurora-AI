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

from sqlalchemy.orm import Session

from app.generators.model_catalog import MODEL_CATALOG, ModelSpec, get_model
from app.services import platform_settings_service as settings_store

logger = logging.getLogger(__name__)

_OVERRIDE_PREFIX = "model_override:"


def _override_key(model_id: str) -> str:
    return f"{_OVERRIDE_PREFIX}{model_id}"


def _parse_override(model_id: str, key: str, raw_value: str) -> dict | None:
    try:
        return json.loads(raw_value)
    except (ValueError, TypeError):
        # A corrupted override row degrades gracefully to catalog defaults, but
        # log it — silently ignoring means a model could e.g. silently re-enable
        # itself, with nothing pointing an operator at the bad row.
        logger.warning(
            "Ignoring corrupted model override for '%s' (key '%s'): %r",
            model_id,
            key,
            raw_value,
        )
        return None


def _read_override(db: Session, model_id: str) -> dict | None:
    key = _override_key(model_id)
    raw_value = settings_store.get_value(db, key)
    if raw_value is None:
        return None
    return _parse_override(model_id, key, raw_value)


def _read_all_overrides(db: Session) -> dict[str, dict]:
    """Every model override, in ONE query — used by `list_effective_models`
    to avoid an N+1 (one query per catalog model)."""
    raw = settings_store.get_values_by_prefix(db, _OVERRIDE_PREFIX)
    result: dict[str, dict] = {}
    for key, raw_value in raw.items():
        model_id = key.removeprefix(_OVERRIDE_PREFIX)
        override = _parse_override(model_id, key, raw_value)
        if override is not None:
            result[model_id] = override
    return result


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
    overrides = _read_all_overrides(db)
    models = [_apply_override(m, overrides.get(m.id)) for m in MODEL_CATALOG]
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

    settings_store.upsert_value(db, _override_key(model_id), json.dumps(current))
    db.commit()

    return get_effective_model(db, model_id)  # type: ignore[return-value]


def clear_override(db: Session, model_id: str) -> ModelSpec | None:
    """Remove any admin override, reverting the model to its catalog default."""
    settings_store.delete_value(db, _override_key(model_id))
    db.commit()
    return get_effective_model(db, model_id)
