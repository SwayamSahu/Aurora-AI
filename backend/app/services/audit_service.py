"""Append-only admin audit log. `record()` writes one durable row per
privileged action; there is deliberately no update or delete function."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import AdminAction


def record(
    db: Session,
    *,
    actor_id: str,
    action: str,
    target_type: str,
    target_id: str | None = None,
    metadata: dict | None = None,
) -> AdminAction:
    """Write an audit entry and commit it immediately, so the record is
    durable independently of the action it describes (which has typically
    already committed by the time this is called)."""
    entry = AdminAction(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        action_metadata=metadata or {},
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_actions(
    db: Session,
    *,
    actor_id: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AdminAction], int]:
    stmt = select(AdminAction).options(selectinload(AdminAction.actor))
    if actor_id:
        stmt = stmt.where(AdminAction.actor_id == actor_id)
    if action:
        stmt = stmt.where(AdminAction.action == action)
    if target_type:
        stmt = stmt.where(AdminAction.target_type == target_type)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = list(
        db.scalars(
            stmt.order_by(AdminAction.created_at.desc()).limit(limit).offset(offset)
        )
    )
    return items, total
