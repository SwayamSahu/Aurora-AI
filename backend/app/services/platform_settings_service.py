"""Runtime-editable platform settings, backed by the `platform_settings`
key/value table. Falls back to the static `config.py` default when a key
has never been set — lets the fee (and future knobs) be tuned from the
admin console without a redeploy.

The `get_value`/`upsert_value`/`delete_value`/`get_values_by_prefix` helpers
below are the generic read/write API for this table — any service storing a
runtime-editable setting here (e.g. `model_service`'s per-model admin
overrides) should go through them rather than querying `PlatformSetting`
directly, so the upsert-or-create logic lives in exactly one place."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import PlatformSetting

PLATFORM_FEE_KEY = "marketplace_platform_fee"


def _get(db: Session, key: str) -> PlatformSetting | None:
    return db.scalar(select(PlatformSetting).where(PlatformSetting.key == key))


def get_value(db: Session, key: str) -> str | None:
    """Raw string value for `key`, or `None` if it's never been set. Callers
    with a domain-specific default (see `get_platform_fee`) wrap this."""
    row = _get(db, key)
    return row.value if row is not None else None


def get_values_by_prefix(db: Session, prefix: str) -> dict[str, str]:
    """Every key→value pair whose key starts with `prefix`, in ONE query —
    for batch reads that would otherwise be an N+1 (e.g. all model-override
    rows, one per catalog model)."""
    rows = db.scalars(
        select(PlatformSetting).where(PlatformSetting.key.startswith(prefix))
    ).all()
    return {row.key: row.value for row in rows}


def upsert_value(db: Session, key: str, value: str) -> None:
    """Create or update a `platform_settings` row. Does not commit — caller
    owns the transaction boundary (mirrors `wallet_service.credit`/`debit`)."""
    row = _get(db, key)
    if row is None:
        db.add(PlatformSetting(key=key, value=value))
    else:
        row.value = value


def delete_value(db: Session, key: str) -> None:
    """Remove a `platform_settings` row if present. Does not commit."""
    row = _get(db, key)
    if row is not None:
        db.delete(row)


def get_platform_fee(db: Session) -> float:
    value = get_value(db, PLATFORM_FEE_KEY)
    return float(value) if value is not None else settings.marketplace_platform_fee


def set_platform_fee(db: Session, value: float) -> float:
    if not (0 <= value <= 1):
        raise ValueError("Platform fee must be between 0 and 1 (a fraction).")
    upsert_value(db, PLATFORM_FEE_KEY, str(value))
    db.commit()
    return value
