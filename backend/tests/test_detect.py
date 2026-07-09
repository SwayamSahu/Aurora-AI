"""E4 — mock object detection (click-to-select / "select all X").

Real segmentation (SAM 2 + GroundingDINO) is Phase 9 work; this proves the
mock backend returns deterministic, well-formed boxes so the UX can be built
and tested now.
"""

from __future__ import annotations

import pytest

from app.generators.base import DetectParams
from app.generators.mock.detector import MockObjectDetector


def _in_bounds(obj) -> bool:
    return (
        0.0 <= obj.x <= 1.0
        and 0.0 <= obj.y <= 1.0
        and 0.0 < obj.w <= 1.0
        and 0.0 < obj.h <= 1.0
        and obj.x + obj.w <= 1.0 + 1e-9
        and obj.y + obj.h <= 1.0 + 1e-9
    )


def test_click_returns_one_box_centered_on_point():
    detector = MockObjectDetector()
    boxes = detector.detect(DetectParams(mode="click", x=0.5, y=0.5))
    assert len(boxes) == 1
    assert _in_bounds(boxes[0])
    cx = boxes[0].x + boxes[0].w / 2
    cy = boxes[0].y + boxes[0].h / 2
    assert cx == pytest.approx(0.5, abs=1e-6)
    assert cy == pytest.approx(0.5, abs=1e-6)


def test_click_near_edges_stays_in_bounds():
    detector = MockObjectDetector()
    for x, y in [(0.0, 0.0), (1.0, 1.0), (0.0, 1.0), (1.0, 0.0)]:
        boxes = detector.detect(DetectParams(mode="click", x=x, y=y))
        assert _in_bounds(boxes[0])


def test_text_query_returns_multiple_labeled_candidates():
    detector = MockObjectDetector()
    boxes = detector.detect(DetectParams(mode="text", query="car"))
    assert len(boxes) >= 2
    for b in boxes:
        assert _in_bounds(b)
        assert "car" in b.label.lower()
        assert 0.0 < b.confidence <= 1.0


def test_text_query_is_deterministic():
    detector = MockObjectDetector()
    a = detector.detect(DetectParams(mode="text", query="dog"))
    b = detector.detect(DetectParams(mode="text", query="dog"))
    assert [(x.label, x.x, x.y, x.w, x.h) for x in a] == [
        (x.label, x.x, x.y, x.w, x.h) for x in b
    ]


def test_different_queries_yield_different_layouts():
    detector = MockObjectDetector()
    cars = detector.detect(DetectParams(mode="text", query="car"))
    dogs = detector.detect(DetectParams(mode="text", query="dog"))
    positions_differ = any(
        (c.x, c.y) != (d.x, d.y) for c, d in zip(cars, dogs, strict=False)
    )
    assert positions_differ
