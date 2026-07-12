"""Mock content-safety classifier — a deterministic heuristic (not a real
model) so the auto-flagging pipeline is fully testable on the Mac. Real
uploads are always safe; a test can force a flag by including the marker
bytes below, which no genuine image file would ever contain by accident."""

from __future__ import annotations

from app.generators.base import ContentSafetyClassifier, ContentSafetyResult

# Test-only trigger — an admin/test can force a flagged classification by
# uploading bytes containing this marker, without needing a real model.
FORCE_FLAG_MARKER = b"__AURORA_MOCK_NSFW_TEST__"


class MockContentSafetyClassifier(ContentSafetyClassifier):
    name = "mock"

    def classify(self, image_bytes: bytes, content_type: str) -> ContentSafetyResult:
        if FORCE_FLAG_MARKER in image_bytes:
            return ContentSafetyResult(
                flagged=True, categories=["nsfw"], confidence=0.97
            )
        return ContentSafetyResult(flagged=False, categories=[], confidence=0.01)
