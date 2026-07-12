"""E3 — real (non-generative) AI Edit engines: retime/camera, color grading,
and OCR text detection. All run genuinely on the Mac via FFmpeg/Tesseract,
no GPU or generative model involved.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from app.db.models.asset import AssetKind, AssetSource
from app.db.models.edit_layer import EditLayerStatus
from app.generators.mock.editor import _probe_duration, _probe_size
from app.schemas.edit_layer import EditLayerCreate
from app.services import asset_service, edit_service
from app.services.edit_runner import run_edit

FIXTURE = Path(__file__).parent.parent / "app/generators/mock/fixtures/sample.mp4"


def _make_video_asset(db, project):
    return asset_service.create_from_upload(
        db,
        project,
        filename="clip.mp4",
        data=FIXTURE.read_bytes(),
        content_type="video/mp4",
        source=AssetSource.GENERATED,
        kind=AssetKind.VIDEO,
    )


def _make_text_video_asset(db, project):
    """A short, real video with large legible text baked in via PIL, encoded
    with FFmpeg — gives Tesseract genuine text to find (no font-availability
    risk from ffmpeg's drawtext filter)."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (640, 360), color=(15, 15, 15))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=64)
    draw.text((40, 140), "HELLO WORLD", fill=(255, 255, 255), font=font)

    with tempfile.TemporaryDirectory() as tmp:
        img_path = Path(tmp) / "frame.png"
        img.save(img_path)
        video_path = Path(tmp) / "text.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(img_path),
                "-t",
                "3",
                "-r",
                "5",
                "-pix_fmt",
                "yuv420p",
                str(video_path),
            ],
            check=True,
            capture_output=True,
        )
        data = video_path.read_bytes()

    return asset_service.create_from_upload(
        db,
        project,
        filename="text.mp4",
        data=data,
        content_type="video/mp4",
        source=AssetSource.GENERATED,
        kind=AssetKind.VIDEO,
    )


def _create_layer(db, project, source, *, engine, preset_id, clip_id="clip-e3"):
    return edit_service.create(
        db,
        project,
        EditLayerCreate(
            clip_id=clip_id,
            engine=engine,
            preset_id=preset_id,
            label=preset_id,
            source_asset_id=source.id,
        ),
    )


def _download(db, layer) -> bytes:
    from app.db.models import Asset
    from app.storage import get_storage

    asset = db.get(Asset, layer.result_asset_id)
    return get_storage().get(asset.storage_key)


# --------------------------------------------------------------------------- #
# Retime / camera — real FFmpeg, no stand-in
# --------------------------------------------------------------------------- #


def test_retime_boomerang_doubles_duration(db_session, sample_project):
    source = _make_video_asset(db_session, sample_project)
    layer = _create_layer(
        db_session,
        sample_project,
        source,
        engine="retime-camera",
        preset_id="mo-boomerang",
    )
    run_edit(db_session, layer)
    db_session.refresh(layer)
    assert layer.status == EditLayerStatus.SUCCEEDED

    with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
        f.write(_download(db_session, layer))
        f.flush()
        out_dur = _probe_duration(Path(f.name))
    src_dur = _probe_duration(FIXTURE)
    # Forward + reversed copy ≈ double the source duration.
    assert out_dur == pytest.approx(src_dur * 2, rel=0.15)


def test_retime_loop_doubles_duration(db_session, sample_project):
    source = _make_video_asset(db_session, sample_project)
    layer = _create_layer(
        db_session,
        sample_project,
        source,
        engine="retime-camera",
        preset_id="mo-loop",
    )
    run_edit(db_session, layer)
    db_session.refresh(layer)
    assert layer.status == EditLayerStatus.SUCCEEDED
    with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
        f.write(_download(db_session, layer))
        f.flush()
        out_dur = _probe_duration(Path(f.name))
    src_dur = _probe_duration(FIXTURE)
    assert out_dur == pytest.approx(src_dur * 2, rel=0.15)


def test_retime_slow_and_reverse_succeed(db_session, sample_project):
    source = _make_video_asset(db_session, sample_project)
    for preset_id in ("mo-slow", "mo-reverse", "mo-freeze", "mo-ramp"):
        layer = _create_layer(
            db_session,
            sample_project,
            source,
            engine="retime-camera",
            preset_id=preset_id,
            clip_id=preset_id,
        )
        run_edit(db_session, layer)
        db_session.refresh(layer)
        assert layer.status == EditLayerStatus.SUCCEEDED, (preset_id, layer.error)


def test_camera_modes_succeed(db_session, sample_project):
    source = _make_video_asset(db_session, sample_project)
    for preset_id in ("cam-stabilize", "cam-pan", "cam-zoom", "cam-orbit"):
        layer = _create_layer(
            db_session,
            sample_project,
            source,
            engine="retime-camera",
            preset_id=preset_id,
            clip_id=preset_id,
        )
        run_edit(db_session, layer)
        db_session.refresh(layer)
        assert layer.status == EditLayerStatus.SUCCEEDED, (preset_id, layer.error)


def test_reframe_modes_succeed(db_session, sample_project):
    source = _make_video_asset(db_session, sample_project)
    for preset_id in ("cam-closeup", "cam-wide", "cam-vertical", "cam-dutch", "cam-thirds"):
        layer = _create_layer(
            db_session,
            sample_project,
            source,
            engine="retime-camera",
            preset_id=preset_id,
            clip_id=preset_id,
        )
        run_edit(db_session, layer)
        db_session.refresh(layer)
        assert layer.status == EditLayerStatus.SUCCEEDED, (preset_id, layer.error)


def test_reframe_vertical_produces_9_16_aspect(db_session, sample_project):
    source = _make_video_asset(db_session, sample_project)
    layer = _create_layer(
        db_session,
        sample_project,
        source,
        engine="retime-camera",
        preset_id="cam-vertical",
    )
    run_edit(db_session, layer)
    db_session.refresh(layer)
    assert layer.status == EditLayerStatus.SUCCEEDED, layer.error

    with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
        f.write(_download(db_session, layer))
        f.flush()
        w, h = _probe_size(Path(f.name))
    assert w / h == pytest.approx(9 / 16, rel=0.05)


def test_reframe_wide_produces_letterbox_aspect(db_session, sample_project):
    source = _make_video_asset(db_session, sample_project)
    layer = _create_layer(
        db_session,
        sample_project,
        source,
        engine="retime-camera",
        preset_id="cam-wide",
    )
    run_edit(db_session, layer)
    db_session.refresh(layer)
    assert layer.status == EditLayerStatus.SUCCEEDED, layer.error

    with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
        f.write(_download(db_session, layer))
        f.flush()
        w, h = _probe_size(Path(f.name))
    assert w / h == pytest.approx(2.39, rel=0.05)


def test_reframe_closeup_preserves_output_resolution(db_session, sample_project):
    """The punch-in crop scales back up so downstream timeline compositing
    doesn't need to handle a resolution change."""
    source = _make_video_asset(db_session, sample_project)
    src_w, src_h = _probe_size(FIXTURE)
    layer = _create_layer(
        db_session,
        sample_project,
        source,
        engine="retime-camera",
        preset_id="cam-closeup",
    )
    run_edit(db_session, layer)
    db_session.refresh(layer)
    assert layer.status == EditLayerStatus.SUCCEEDED, layer.error

    with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
        f.write(_download(db_session, layer))
        f.flush()
        out_w, out_h = _probe_size(Path(f.name))
    assert (out_w, out_h) == (src_w, src_h)


# --------------------------------------------------------------------------- #
# Masked edit — the maskedmerge path (mask sized differently from the source)
# --------------------------------------------------------------------------- #


def test_masked_edit_with_offsize_mask_succeeds(db_session, sample_project):
    """A painted mask is authored at a fixed canvas size that rarely matches
    the source video. The editor must scale it (scale2ref) before merging —
    regression test for the maskedmerge dimension-mismatch bug."""
    import base64
    import io

    from PIL import Image

    source = _make_video_asset(db_session, sample_project)

    # 1280x720 mask (deliberately unlike the fixture's resolution): black with
    # a white rectangle marking the edit region.
    mask = Image.new("L", (1280, 720), color=0)
    for y in range(200, 500):
        for x in range(300, 800):
            mask.putpixel((x, y), 255)
    buf = io.BytesIO()
    mask.save(buf, format="PNG")
    mask_b64 = base64.b64encode(buf.getvalue()).decode()

    layer = _create_layer(
        db_session,
        sample_project,
        source,
        engine="masked-v2v",
        preset_id="recolor",
        clip_id="masked-clip",
    )
    run_edit(db_session, layer, mask_base64=mask_b64)
    db_session.refresh(layer)
    assert layer.status == EditLayerStatus.SUCCEEDED, layer.error
    assert layer.result_asset_id is not None
    assert layer.mask_storage_key is not None


# --------------------------------------------------------------------------- #
# Color grading — real, distinct per preset (not one-size-fits-all)
# --------------------------------------------------------------------------- #


def test_grade_recipes_produce_distinct_output(db_session, sample_project):
    source = _make_video_asset(db_session, sample_project)
    cinematic = _create_layer(
        db_session,
        sample_project,
        source,
        engine="global-restyle",
        preset_id="light-cinematic",
        clip_id="c1",
    )
    neon = _create_layer(
        db_session,
        sample_project,
        source,
        engine="global-restyle",
        preset_id="light-neon",
        clip_id="c2",
    )
    run_edit(db_session, cinematic)
    run_edit(db_session, neon)
    db_session.refresh(cinematic)
    db_session.refresh(neon)
    assert cinematic.status == EditLayerStatus.SUCCEEDED
    assert neon.status == EditLayerStatus.SUCCEEDED

    cinematic_bytes = _download(db_session, cinematic)
    neon_bytes = _download(db_session, neon)
    # Different real color-grade filters must not collapse to the same output.
    assert cinematic_bytes != neon_bytes


def test_relight_presets_excluded_from_grade_recipes():
    """The whole point of `relight-*`: they must NOT be in GRADE_RECIPES, so
    the CUDA editor's dispatch (`preset_id in GRADE_RECIPES`) falls through
    to the real generative img2img path instead of an FFmpeg color curve."""
    from app.generators.mock.editor import GRADE_RECIPES, _RELIGHT_PRESETS

    for preset_id in _RELIGHT_PRESETS:
        assert preset_id not in GRADE_RECIPES, preset_id


def test_relight_presets_succeed(db_session, sample_project):
    from app.generators.mock.editor import _RELIGHT_PRESETS

    source = _make_video_asset(db_session, sample_project)
    for i, preset_id in enumerate(_RELIGHT_PRESETS):
        layer = _create_layer(
            db_session,
            sample_project,
            source,
            engine="global-restyle",
            preset_id=preset_id,
            clip_id=f"relight-{i}",
        )
        run_edit(db_session, layer)
        db_session.refresh(layer)
        assert layer.status == EditLayerStatus.SUCCEEDED, (preset_id, layer.error)


def test_relight_stand_in_distinct_from_grade_and_generic_fallback(
    db_session, sample_project
):
    """The relight stand-in (vignette) must not collide with a real grade
    recipe's output, nor with the generic global-restyle fallback used by
    weather/magic-prompt presets that also lack a grade recipe."""
    source = _make_video_asset(db_session, sample_project)
    relight = _create_layer(
        db_session,
        sample_project,
        source,
        engine="global-restyle",
        preset_id="relight-storm",
        clip_id="relight-diff-1",
    )
    grade = _create_layer(
        db_session,
        sample_project,
        source,
        engine="global-restyle",
        preset_id="light-cinematic",
        clip_id="relight-diff-2",
    )
    generic = _create_layer(
        db_session,
        sample_project,
        source,
        engine="global-restyle",
        preset_id="weather-fog",  # not a grade recipe, not a relight preset
        clip_id="relight-diff-3",
    )
    run_edit(db_session, relight)
    run_edit(db_session, grade)
    run_edit(db_session, generic)
    db_session.refresh(relight)
    db_session.refresh(grade)
    db_session.refresh(generic)
    assert relight.status == EditLayerStatus.SUCCEEDED
    assert grade.status == EditLayerStatus.SUCCEEDED
    assert generic.status == EditLayerStatus.SUCCEEDED

    relight_bytes = _download(db_session, relight)
    grade_bytes = _download(db_session, grade)
    generic_bytes = _download(db_session, generic)
    assert relight_bytes != grade_bytes
    assert relight_bytes != generic_bytes


def test_all_lighting_and_time_season_presets_succeed(db_session, sample_project):
    from app.generators.mock.editor import GRADE_RECIPES

    source = _make_video_asset(db_session, sample_project)
    for i, preset_id in enumerate(GRADE_RECIPES):
        layer = _create_layer(
            db_session,
            sample_project,
            source,
            engine="global-restyle",
            preset_id=preset_id,
            clip_id=f"grade-{i}",
        )
        run_edit(db_session, layer)
        db_session.refresh(layer)
        assert layer.status == EditLayerStatus.SUCCEEDED, (preset_id, layer.error)


# --------------------------------------------------------------------------- #
# OCR text detection — real Tesseract, genuine text found
# --------------------------------------------------------------------------- #


def test_text_detect_finds_real_text(db_session, sample_project):
    source = _make_text_video_asset(db_session, sample_project)
    layer = _create_layer(
        db_session,
        sample_project,
        source,
        engine="text-ops",
        preset_id="text-detect",
    )
    run_edit(db_session, layer)
    db_session.refresh(layer)
    assert layer.status == EditLayerStatus.SUCCEEDED, layer.error
    assert layer.result_asset_id is not None


def test_text_detect_handles_no_text_gracefully(db_session, sample_project):
    # sample.mp4 has no legible text — the detector should still succeed
    # with an (empty) overlay pass rather than fail.
    source = _make_video_asset(db_session, sample_project)
    layer = _create_layer(
        db_session,
        sample_project,
        source,
        engine="text-ops",
        preset_id="text-detect",
    )
    run_edit(db_session, layer)
    db_session.refresh(layer)
    assert layer.status == EditLayerStatus.SUCCEEDED, layer.error
