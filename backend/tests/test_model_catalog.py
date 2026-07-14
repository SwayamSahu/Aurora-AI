"""Video-generation model catalog: invariants + capability clamping."""

from __future__ import annotations

import pytest

from app.generators.model_catalog import (
    DEFAULT_MODEL_ID,
    MODEL_CATALOG,
    clamp_video_params,
    get_model,
    list_models,
)


def test_ids_are_unique():
    ids = [m.id for m in MODEL_CATALOG]
    assert len(set(ids)) == len(ids)


def test_default_model_exists_and_is_enabled():
    spec = get_model(DEFAULT_MODEL_ID)
    assert spec is not None
    assert spec.enabled


def test_get_model_unknown_and_none():
    assert get_model("does-not-exist") is None
    assert get_model(None) is None
    assert get_model("") is None


def test_every_spec_has_a_sane_capability_envelope():
    for m in MODEL_CATALOG:
        assert m.kind in {"local", "api"}
        assert 1 <= m.min_duration <= m.default_duration <= m.max_duration
        assert m.max_width > 0 and m.max_height > 0
        assert m.resolution in {"720p", "1080p", "4K"}
        assert m.credit_cost > 0


def test_local_models_are_priced_below_api_models():
    # Local models only cost us electricity; hosted API models cost real
    # provider fees per call and must be priced meaningfully higher.
    local_max = max(m.credit_cost for m in MODEL_CATALOG if m.kind == "local")
    api_min = min(m.credit_cost for m in MODEL_CATALOG if m.kind == "api")
    assert local_max < api_min


def test_list_models_returns_only_enabled():
    for m in list_models():
        assert m.enabled


def test_screenshot_models_are_present():
    # The models the product spec asked for must all be selectable.
    expected = {
        "seedance-2.0",
        "seedance-2.0-mini",
        "seedance-2.0-fast",
        "gemini-omni-flash",
        "kling-3.0",
        "kling-3.0-turbo",
        "kling-3.0-motion",
        "happyhorse",
        "grok-imagine",
        "grok-imagine-1.5",
        "veo-3.1-lite",
        "wan-2.7",
    }
    ids = {m.id for m in MODEL_CATALOG}
    assert expected <= ids


def test_clamp_duration_into_range():
    spec = get_model("kling-3.0")  # 3–15s
    assert spec is not None
    # Below min → clamped up.
    dur, _, _ = clamp_video_params(spec, 1.0, 100, 100)
    assert dur == spec.min_duration
    # Above max → clamped down.
    dur, _, _ = clamp_video_params(spec, 60.0, 100, 100)
    assert dur == spec.max_duration
    # In range → unchanged.
    dur, _, _ = clamp_video_params(spec, 5.0, 100, 100)
    assert dur == 5.0


def test_clamp_dimensions_to_tier():
    spec = get_model("grok-imagine")  # 720p → 1280x720
    assert spec is not None
    # An oversized request is capped at the tier.
    _, w, h = clamp_video_params(spec, 4.0, 9999, 9999)
    assert w == spec.max_width == 1280
    assert h == spec.max_height == 720
    # A small request passes through untouched.
    _, w, h = clamp_video_params(spec, 4.0, 640, 360)
    assert (w, h) == (640, 360)


@pytest.mark.parametrize("model", [m.id for m in MODEL_CATALOG])
def test_default_duration_is_within_its_own_range(model):
    spec = get_model(model)
    assert spec is not None
    assert spec.min_duration <= spec.default_duration <= spec.max_duration
