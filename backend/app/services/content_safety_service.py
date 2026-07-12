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
    db: Session, media, *, image_bytes: bytes, target_type: str
) -> None:
    """Classifies `image_bytes` and, if flagged, sets `media.is_flagged` /
    `flag_categories` and opens a system report against it. `media` is a
    freshly-created `BlogMedia`/`ListingMedia` row (already committed, so it
    has an id) — mutated and committed again here only if flagged."""
    result = get_content_safety_classifier().classify(image_bytes, media.content_type)
    if not result.flagged:
        return

    media.is_flagged = True
    media.flag_categories = result.categories
    db.commit()

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
