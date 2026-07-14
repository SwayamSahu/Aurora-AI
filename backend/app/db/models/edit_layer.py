from __future__ import annotations

import enum

from sqlalchemy import (
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDMixin


class EditLayerStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class EditLayer(UUIDMixin, TimestampMixin, Base):
    """A single non-destructive AI edit attached to a timeline clip.

    Clips live inside the timeline JSON (not their own table), so `clip_id` is
    a plain string referencing a clip id within the project's timeline document.
    The original asset is never modified; each layer's `result_asset_id` is a
    new derived asset.
    """

    __tablename__ = "edit_layers"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    clip_id: Mapped[str] = mapped_column(String(64), index=True)

    # What to do.
    engine: Mapped[str] = mapped_column(String(40))
    preset_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    label: Mapped[str] = mapped_column(String(160), default="")
    prompt: Mapped[str] = mapped_column(Text, default="")
    params: Mapped[dict] = mapped_column(JSON, default=dict)

    # Inputs / outputs (MinIO-backed).
    mask_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_asset_id: Mapped[str | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )
    result_asset_id: Mapped[str | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )

    # Lifecycle.
    status: Mapped[EditLayerStatus] = mapped_column(
        Enum(EditLayerStatus), default=EditLayerStatus.QUEUED, index=True
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stacking + visibility on the clip.
    position: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    project: Mapped[Project] = relationship()  # noqa: F821
