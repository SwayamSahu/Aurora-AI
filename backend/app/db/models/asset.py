from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDMixin


class AssetKind(str, enum.Enum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    SUBTITLES = "subtitles"


class AssetSource(str, enum.Enum):
    GENERATED = "generated"
    UPLOADED = "uploaded"
    DERIVED = "derived"  # e.g. transcription/export output


class Asset(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "assets"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[AssetKind] = mapped_column(Enum(AssetKind))
    source: Mapped[AssetSource] = mapped_column(Enum(AssetSource))

    # Object-storage key in MinIO (never the bytes themselves).
    storage_key: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(120))

    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Automated content-safety scan — same mechanism as BlogMedia/ListingMedia
    # uploads (see `content_safety_service`), extended to generated output.
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_categories: Mapped[list] = mapped_column(JSON, default=list)

    project: Mapped["Project"] = relationship(back_populates="assets")  # noqa: F821
