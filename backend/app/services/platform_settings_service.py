"""Runtime-editable platform settings, backed by the `platform_settings`
key/value table. Falls back to the static `config.py` default when a key
has never been set — lets the fee (and future knobs) be tuned from the
admin console without a redeploy."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import PlatformSetting

PLATFORM_FEE_KEY = "marketplace_platform_fee"


def _get(db: Session, key: str) -> PlatformSetting | None:
    return db.scalar(select(PlatformSetting).where(PlatformSetting.key == key))


def get_platform_fee(db: Session) -> float:
    row = _get(db, PLATFORM_FEE_KEY)
    if row is None:
        return settings.marketplace_platform_fee
    return float(row.value)


def set_platform_fee(db: Session, value: float) -> float:
    if not (0 <= value <= 1):
        raise ValueError("Platform fee must be between 0 and 1 (a fraction).")
    row = _get(db, PLATFORM_FEE_KEY)
    if row is None:
        row = PlatformSetting(key=PLATFORM_FEE_KEY, value=str(value))
        db.add(row)
    else:
        row.value = str(value)
    db.commit()
    return value
