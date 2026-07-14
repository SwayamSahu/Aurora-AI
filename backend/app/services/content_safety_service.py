"""Wires the content-safety classifier (see `app.generators`) into the
upload path: classify, persist the flag on the media row, and — if
flagged — open a system-generated report so it lands in the same
moderator queue as user reports."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import ReportReason
from app.generators.registry import get_content_safety_classifier
from app.services import report_service

_CATEGORY_TO_REASON = {
    "nsfw": ReportReason.INAPPROPRIATE,
    "violence": ReportReason.INAPPROPRIATE,
}


def scan_and_flag(
    db: Session,
    media,
    *,
    image_bytes: bytes,
    target_type: str,
    content_type: str | None = None,
) -> None:
    """Classifies `image_bytes` and, if flagged, sets `media.is_flagged` /
    `flag_categories` and opens a system report against it. `media` is a
    freshly-created `BlogMedia`/`ListingMedia`/`Asset` row (already
    committed, so it has an id) — mutated and committed again here only if
    flagged.

    `content_type` describes `image_bytes` itself and defaults to
    `media.content_type` — pass it explicitly when they differ, e.g. a video
    asset's `content_type` is "video/mp4" but `image_bytes` here is a PNG
    frame extracted from it for classification."""
    result = get_content_safety_classifier().classify(
        image_bytes, content_type or media.content_type
    )
    if not result.flagged:
        return

    # Open the moderation report BEFORE persisting the flag. If report creation
    # fails, we'd rather the asset end up neither flagged nor reported (the scan
    # is simply retryable/skipped) than flagged-but-invisible — a flag with no
    # queue entry would silently read as "already reviewed".
    reason = _CATEGORY_TO_REASON.get(
        result.categories[0] if result.categories else "", ReportReason.INAPPROPRIATE
    )
    report_service.create_report(
        db,
        reporter_id=None,
        target_type=target_type,
        target_id=media.id,
        reason=reason,
        note=f"Auto-flagged by content safety scan ({', '.join(result.categories)}, "
        f"confidence {result.confidence:.2f}).",
    )

    media.is_flagged = True
    media.flag_categories = result.categories
    db.commit()
