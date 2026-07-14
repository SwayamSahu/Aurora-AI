from __future__ import annotations

import enum

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDMixin


class JobType(str, enum.Enum):
    GENERATE_VIDEO = "generate_video"
    IMAGE_TO_VIDEO = "image_to_video"
    GENERATE_IMAGE = "generate_image"
    TTS = "tts"
    TRANSCRIBE = "transcribe"
    MUSIC = "music"
    EXPORT = "export"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "jobs"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[JobType] = mapped_column(Enum(JobType))
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.QUEUED, index=True
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)

    # Generation parameters and free-form metadata.
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Credits debited from the owner's wallet at submit time (0 for job types
    # that aren't billed, e.g. no model was named). Snapshotted here — rather
    # than recomputed from the model catalog — so a refund on failure is
    # always exact even if the model's price changes afterward.
    credits_charged: Mapped[int] = mapped_column(Integer, default=0)

    # Celery task id, for cancellation / lookup.
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Resulting asset, if the job produced one.
    result_asset_id: Mapped[str | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )

    project: Mapped["Project"] = relationship(back_populates="jobs")  # noqa: F821
