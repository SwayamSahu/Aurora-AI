"""Timeline document persistence.

Each project has one current `TimelineVersion` whose `document` JSON holds the
non-destructive edit (tracks + clips referencing assets). Export (Phase 7)
compiles this document into an FFmpeg render plan.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import TimelineVersion


def default_document() -> dict:
    """A fresh timeline with the three standard tracks."""
    return {
        "version": 1,
        "tracks": [
            {"id": str(uuid.uuid4()), "type": "video", "name": "Video", "clips": []},
            {"id": str(uuid.uuid4()), "type": "text", "name": "Text", "clips": []},
            {"id": str(uuid.uuid4()), "type": "audio", "name": "Audio", "clips": []},
        ],
    }


def get_current(db: Session, project_id: str) -> TimelineVersion:
    """Return the project's current timeline, creating an empty one if needed."""
    tv = db.scalar(
        select(TimelineVersion).where(
            TimelineVersion.project_id == project_id,
            TimelineVersion.is_current.is_(True),
        )
    )
    if tv is None:
        tv = TimelineVersion(
            project_id=project_id,
            version=1,
            is_current=True,
            document=default_document(),
        )
        db.add(tv)
        db.commit()
        db.refresh(tv)
    return tv


def save(db: Session, project_id: str, document: dict) -> TimelineVersion:
    tv = get_current(db, project_id)
    tv.document = document
    # Keep the document's version counter in sync if provided.
    if isinstance(document, dict) and "version" in document:
        try:
            tv.version = int(document["version"])
        except (TypeError, ValueError):
            pass
    db.commit()
    db.refresh(tv)
    return tv
