"""Append-only admin action log. Every privileged mutation (by a moderator
or admin, acting on something that isn't their own) records one row here.
Rows are never edited or deleted — there is no update/delete path in
`audit_service` and no route exposes one."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDMixin


class AdminAction(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "admin_actions"

    # The actor is SET NULL (not CASCADE) on user deletion so the historical
    # record of what happened survives even if the admin account is removed.
    actor_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Dotted verb, e.g. "listing.delist", "wallet.adjust", "post.delete".
    action: Mapped[str] = mapped_column(String(80), index=True)
    target_type: Mapped[str] = mapped_column(String(40), index=True)
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # Free-form context: amounts, before/after values, reason, etc.
    action_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    actor: Mapped[User | None] = relationship()  # noqa: F821
