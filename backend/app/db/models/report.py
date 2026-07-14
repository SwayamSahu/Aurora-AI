"""User-submitted content reports (spam/abuse/etc.), reviewed by moderators.
Reports point at arbitrary content by `(target_type, target_id)` rather than
a foreign key, mirroring `AdminAction` — the target can be a blog post,
blog comment, listing, or listing comment, and may later be deleted while
the report itself stays for the record."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class ReportReason(str, enum.Enum):
    SPAM = "spam"
    ABUSE = "abuse"
    INAPPROPRIATE = "inappropriate"
    COPYRIGHT = "copyright"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Report(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    reporter_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_type: Mapped[str] = mapped_column(String(40), index=True)
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    reason: Mapped[ReportReason] = mapped_column(Enum(ReportReason))
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), default=ReportStatus.OPEN, index=True
    )
    resolved_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolution_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    reporter: Mapped[User | None] = relationship(foreign_keys=[reporter_id])  # noqa: F821
    resolved_by: Mapped[User | None] = relationship(foreign_keys=[resolved_by_id])  # noqa: F821
