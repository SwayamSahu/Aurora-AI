from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDMixin


class TimelineVersion(UUIDMixin, TimestampMixin, Base):
    """A non-destructive editor document.

    The `document` JSON holds tracks, clips, effects and asset references.
    Export compiles this document into an FFmpeg render plan (Phase 7).
    """

    __tablename__ = "timeline_versions"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    document: Mapped[dict] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship(  # noqa: F821
        back_populates="timeline_versions"
    )
