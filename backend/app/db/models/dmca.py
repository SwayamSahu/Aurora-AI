"""Formal copyright takedown notices. Deliberately separate from the
generic `Report` model — DMCA notices are a legal instrument with their own
required fields (claimant identity, sworn good-faith statement, signature)
and don't require the claimant to have a platform account."""

from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class DmcaStatus(str, enum.Enum):
    OPEN = "open"
    CONTENT_REMOVED = "content_removed"
    REJECTED = "rejected"


class DmcaRequest(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "dmca_requests"

    claimant_name: Mapped[str] = mapped_column(String(200))
    claimant_email: Mapped[str] = mapped_column(String(320))
    target_type: Mapped[str] = mapped_column(String(40), index=True)
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    work_description: Mapped[str] = mapped_column(Text)
    # Required checkbox on the public form — a sworn statement of good-faith
    # belief and, under penalty of perjury, authority to act (17 U.S.C. 512(c)(3)).
    good_faith_statement: Mapped[bool] = mapped_column()
    signature: Mapped[str] = mapped_column(String(200))

    status: Mapped[DmcaStatus] = mapped_column(
        Enum(DmcaStatus), default=DmcaStatus.OPEN, index=True
    )
    resolved_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolution_note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    resolved_by: Mapped[User | None] = relationship()  # noqa: F821
