from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDMixin


class UserRole(str, enum.Enum):
    """Three-tier access. `moderator` can moderate content (posts, listings,
    comments); `admin` is a superset that also covers finance (refunds,
    wallet adjustments, plan/fee changes) and user management."""

    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Set by GDPR erasure (self-service or admin-triggered) — PII scrubbed,
    # row kept so CASCADE-linked orders/listings/comments survive intact.
    # See `gdpr_service.anonymize_user`.
    erased_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER, index=True
    )

    # Persisted user preferences (generation defaults, etc.).
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)

    projects: Mapped[list[Project]] = relationship(  # noqa: F821
        back_populates="owner", cascade="all, delete-orphan"
    )

    @property
    def is_moderator(self) -> bool:
        """True for moderators AND admins — admin is a superset of moderator."""
        return self.role in (UserRole.MODERATOR, UserRole.ADMIN)

    @hybrid_property
    def is_superuser(self) -> bool:
        """Back-compat: `role == admin`. Kept as a settable hybrid so the
        many existing `user.is_superuser = True/False` call sites (and the
        `UserRead` schema) keep working unchanged after the role migration."""
        return self.role == UserRole.ADMIN

    @is_superuser.setter  # type: ignore[no-redef]
    def is_superuser(self, value: bool) -> None:
        self.role = UserRole.ADMIN if value else UserRole.USER

    @is_superuser.expression  # type: ignore[no-redef]
    def is_superuser(cls):  # noqa: N805
        return cls.role == UserRole.ADMIN
