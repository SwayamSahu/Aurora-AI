"""AI Edit layer flow — runs on the Mac with the mock editor (real FFmpeg)."""

from __future__ import annotations

from app.db.models.asset import AssetKind, AssetSource
from app.db.models.edit_layer import EditLayerStatus
from app.services import asset_service, edit_service
from app.services.edit_runner import run_edit


def _make_video_asset(db, project):
    # A tiny real MP4 from the mock fixture keeps FFmpeg exercised for real.
    from pathlib import Path

    fixture = Path(__file__).parent.parent / "app/generators/mock/fixtures/sample.mp4"
    return asset_service.create_from_upload(
        db,
        project,
        filename="clip.mp4",
        data=fixture.read_bytes(),
        content_type="video/mp4",
        source=AssetSource.GENERATED,
        kind=AssetKind.VIDEO,
    )


def _create_layer(
    db, project, source, engine="masked-v2v", clip_id="clip-1", preset_id=None
):
    from app.schemas.edit_layer import EditLayerCreate

    return edit_service.create(
        db,
        project,
        EditLayerCreate(
            clip_id=clip_id,
            engine=engine,
            preset_id=preset_id,
            label="Test",
            prompt="make it yellow",
            source_asset_id=source.id,
        ),
    )


def test_edit_layer_runs_and_produces_asset(db_session, sample_project):
    source = _make_video_asset(db_session, sample_project)
    layer = _create_layer(db_session, sample_project, source)
    assert layer.status == EditLayerStatus.QUEUED

    run_edit(db_session, layer)
    db_session.refresh(layer)

    assert layer.status == EditLayerStatus.SUCCEEDED
    assert layer.result_asset_id is not None
    assert layer.result_asset_id != source.id  # a NEW asset — non-destructive
    assert layer.progress == 1.0


def test_custom_params_persist_and_run(db_session, sample_project):
    """`swap-precise` sends a lower diffusion strength via `params` — the mock
    editor ignores it (real strength only matters on the CUDA generative
    path) but the value must round-trip through creation and survive a run."""
    from app.schemas.edit_layer import EditLayerCreate

    source = _make_video_asset(db_session, sample_project)
    layer = edit_service.create(
        db_session,
        sample_project,
        EditLayerCreate(
            clip_id="clip-precise",
            engine="masked-v2v",
            preset_id="swap-precise",
            label="Precise object swap",
            prompt="a red bicycle",
            params={"strength": 0.55},
            source_asset_id=source.id,
        ),
    )
    assert layer.params == {"strength": 0.55}

    run_edit(db_session, layer)
    db_session.refresh(layer)
    assert layer.status == EditLayerStatus.SUCCEEDED
    assert layer.params == {"strength": 0.55}


def test_missing_source_fails_gracefully(db_session, sample_project):
    from app.schemas.edit_layer import EditLayerCreate

    layer = edit_service.create(
        db_session,
        sample_project,
        EditLayerCreate(clip_id="c1", engine="masked-v2v", source_asset_id="nope"),
    )
    run_edit(db_session, layer)
    db_session.refresh(layer)
    assert layer.status == EditLayerStatus.FAILED
    assert layer.error


def test_layers_stack_and_order_by_position(db_session, sample_project):
    source = _make_video_asset(db_session, sample_project)
    a = _create_layer(db_session, sample_project, source, clip_id="clip-x")
    b = _create_layer(db_session, sample_project, source, clip_id="clip-x")
    assert a.position == 0
    assert b.position == 1
    layers = edit_service.list_for_clip(db_session, sample_project.id, "clip-x")
    assert [x.id for x in layers] == [a.id, b.id]


def test_top_result_asset_id_picks_top_enabled_succeeded(db_session, sample_project):
    source = _make_video_asset(db_session, sample_project)
    a = _create_layer(db_session, sample_project, source, clip_id="clip-y")
    run_edit(db_session, a)
    # A second, disabled layer should be ignored by the export substitution.
    b = _create_layer(db_session, sample_project, source, clip_id="clip-y")
    run_edit(db_session, b)
    from app.schemas.edit_layer import EditLayerUpdate

    edit_service.update(db_session, b, EditLayerUpdate(enabled=False))

    top = edit_service.top_result_asset_id(db_session, sample_project.id, "clip-y")
    db_session.refresh(a)
    assert top == a.result_asset_id  # b disabled → falls back to a
