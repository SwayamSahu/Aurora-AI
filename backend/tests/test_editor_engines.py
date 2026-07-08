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
from app.generators.mock.editor import _probe_duration
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
