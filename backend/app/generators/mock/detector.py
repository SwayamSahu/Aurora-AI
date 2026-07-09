"""Mock object detector — deterministic, plausible boxes (no GPU).

Real object detection/segmentation (GroundingDINO + SAM 2) is Phase 9 work.
This mock lets the click-to-select and "select all X" UX be built and fully
exercised now: same input always yields the same boxes, so the interaction
is stable to develop and test against.
"""

from __future__ import annotations

import hashlib

from app.generators.base import DetectedObject, DetectParams, ObjectDetector

# Click mode: a single "subject-sized" box centered on the click point.
_CLICK_W = 0.20
_CLICK_H = 0.30

# Text mode: how many candidates a "select all X" query returns.
_TEXT_CANDIDATES = 3


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _seeded_unit(seed: str, salt: str) -> float:
    """A deterministic pseudo-random float in [0, 1) from a string seed."""
    digest = hashlib.sha256(f"{seed}:{salt}".encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


class MockObjectDetector(ObjectDetector):
    name = "mock-detector"

    def detect(self, params: DetectParams) -> list[DetectedObject]:
        if params.mode == "click":
            return self._detect_click(params)
        return self._detect_text(params)

    def _detect_click(self, params: DetectParams) -> list[DetectedObject]:
        cx = _clamp(params.x if params.x is not None else 0.5)
        cy = _clamp(params.y if params.y is not None else 0.5)
        x = _clamp(cx - _CLICK_W / 2, 0.0, 1.0 - _CLICK_W)
        y = _clamp(cy - _CLICK_H / 2, 0.0, 1.0 - _CLICK_H)
        return [
            DetectedObject(
                label="Selection", x=x, y=y, w=_CLICK_W, h=_CLICK_H, confidence=1.0
            )
        ]

    def _detect_text(self, params: DetectParams) -> list[DetectedObject]:
        query = (params.query or "object").strip() or "object"
        label = query.title()
        results: list[DetectedObject] = []
        for i in range(_TEXT_CANDIDATES):
            salt = f"box{i}"
            w = 0.16 + 0.10 * _seeded_unit(query, f"{salt}-w")
            h = 0.16 + 0.10 * _seeded_unit(query, f"{salt}-h")
            x = _clamp(_seeded_unit(query, f"{salt}-x"), 0.0, 1.0 - w)
            y = _clamp(_seeded_unit(query, f"{salt}-y"), 0.0, 1.0 - h)
            confidence = 0.68 + 0.28 * _seeded_unit(query, f"{salt}-conf")
            results.append(
                DetectedObject(
                    label=f"{label} {i + 1}",
                    x=x,
                    y=y,
                    w=w,
                    h=h,
                    confidence=round(confidence, 2),
                )
            )
        return results
