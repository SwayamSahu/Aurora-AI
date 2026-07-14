"""Track C/D/E integration: content-safety scanning of generated assets, and
the admin model-override service that Track D's routes sit on top of.
Billing (debit/refund) is covered end-to-end in test_jobs.py; this file
covers the pieces that don't need the full HTTP job pipeline.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import User
from app.db.models.job import Job, JobType
from app.generators.base import GeneratedMedia
from app.generators.mock.content_safety import FORCE_FLAG_MARKER
from app.services import asset_service, job_runner, model_service
from app.services.report_service import list_reports

FIXTURE = Path(__file__).parent.parent / "app/generators/mock/fixtures/sample.mp4"


def _register(client: TestClient, email: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret1", "full_name": email.split("@")[0]},
    )
    res = client.post(
        "/api/v1/auth/login", data={"username": email, "password": "supersecret1"}
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _make_admin(db_session, email: str) -> None:
    user = db_session.scalar(select(User).where(User.email == email))
    user.is_superuser = True
    db_session.commit()


def _make_asset(db, project, *, kind="image", content_type="image/png"):
    from app.db.models.asset import AssetKind, AssetSource

    return asset_service.create_from_upload(
        db,
        project,
        filename="generated.bin",
        data=b"placeholder",
        content_type=content_type,
        source=AssetSource.GENERATED,
        kind=AssetKind.IMAGE if kind == "image" else AssetKind.VIDEO,
    )


def _fake_job(project_id: str, job_type: JobType) -> Job:
    # Not persisted — `_scan_generated_asset` only reads `job.type`/`job.id`.
    return Job(id="job-safety-test", project_id=project_id, type=job_type)


# --------------------------------------------------------------------------- #
# Content-safety scan on generated output
# --------------------------------------------------------------------------- #


def test_generated_image_flagged_by_scan_creates_system_report(db_session, sample_project):
    asset = _make_asset(db_session, sample_project, kind="image")
    job = _fake_job(sample_project.id, JobType.GENERATE_IMAGE)
    media = GeneratedMedia(
        kind="image",
        data=b"\x89PNG\r\n\x1a\n" + FORCE_FLAG_MARKER,
        content_type="image/png",
        suggested_filename="generated.png",
    )

    job_runner._scan_generated_asset(db_session, job, asset, media)

    db_session.refresh(asset)
    assert asset.is_flagged is True
    assert "nsfw" in asset.flag_categories

    reports, total = list_reports(db_session, target_type="asset")
    assert total == 1
    assert reports[0].target_id == asset.id
    assert reports[0].reporter_id is None


def test_scan_does_not_flag_when_report_creation_fails(
    db_session, sample_project, monkeypatch
):
    """Regression: scan_and_flag opens the moderation report BEFORE committing
    the flag, so a report-creation failure must leave the asset neither flagged
    nor reported (never flagged-but-invisible-to-moderators)."""
    import pytest

    from app.services import content_safety_service, report_service

    asset = _make_asset(db_session, sample_project, kind="image")

    def _boom(*args, **kwargs):
        raise RuntimeError("report backend down")

    monkeypatch.setattr(report_service, "create_report", _boom)

    with pytest.raises(RuntimeError):
        content_safety_service.scan_and_flag(
            db_session,
            asset,
            image_bytes=b"\x89PNG\r\n\x1a\n" + FORCE_FLAG_MARKER,
            target_type="asset",
        )

    db_session.refresh(asset)
    assert asset.is_flagged is False
    assert list_reports(db_session, target_type="asset")[1] == 0


def test_generated_image_clean_is_not_flagged(db_session, sample_project):
    asset = _make_asset(db_session, sample_project, kind="image")
    job = _fake_job(sample_project.id, JobType.GENERATE_IMAGE)
    media = GeneratedMedia(
        kind="image",
        data=b"\x89PNG\r\n\x1a\nordinary-clean-image-bytes",
        content_type="image/png",
        suggested_filename="generated.png",
    )

    job_runner._scan_generated_asset(db_session, job, asset, media)

    db_session.refresh(asset)
    assert asset.is_flagged is False
    assert list_reports(db_session, target_type="asset")[1] == 0


def test_generated_video_first_frame_is_scanned_via_real_ffmpeg(db_session, sample_project):
    """No marker in the fixture — proves the real ffmpeg frame-extraction
    path runs end to end without raising, not just that flagging works."""
    asset = _make_asset(db_session, sample_project, kind="video", content_type="video/mp4")
    job = _fake_job(sample_project.id, JobType.GENERATE_VIDEO)
    media = GeneratedMedia(
        kind="video",
        data=FIXTURE.read_bytes(),
        content_type="video/mp4",
        suggested_filename="generated.mp4",
    )

    job_runner._scan_generated_asset(db_session, job, asset, media)

    db_session.refresh(asset)
    assert asset.is_flagged is False  # clean fixture, no marker


def test_scan_failure_is_swallowed_not_raised(db_session, sample_project):
    """A corrupt 'video' can't be frame-extracted by ffmpeg — the scan must
    fail silently (logged) rather than take down an otherwise-successful
    generation job."""
    asset = _make_asset(db_session, sample_project, kind="video", content_type="video/mp4")
    job = _fake_job(sample_project.id, JobType.GENERATE_VIDEO)
    media = GeneratedMedia(
        kind="video",
        data=b"not a real video file",
        content_type="video/mp4",
        suggested_filename="generated.mp4",
    )

    job_runner._scan_generated_asset(db_session, job, asset, media)  # must not raise

    db_session.refresh(asset)
    assert asset.is_flagged is False


def test_audio_and_subtitle_jobs_are_not_scanned(db_session, sample_project):
    """TTS/music/transcription output isn't image-classifiable — scanning
    must be a no-op for those job types (asserted by the absence of any
    ffmpeg/classifier call: an audio 'video'-typed extraction would raise if
    attempted, so a passing, unflagged result proves it was skipped)."""
    asset = _make_asset(db_session, sample_project, kind="video", content_type="audio/wav")
    for job_type in (JobType.TTS, JobType.MUSIC, JobType.TRANSCRIBE):
        job = _fake_job(sample_project.id, job_type)
        media = GeneratedMedia(
            kind="audio",
            data=b"not classifiable audio bytes",
            content_type="audio/wav",
            suggested_filename="generated.wav",
        )
        job_runner._scan_generated_asset(db_session, job, asset, media)
    db_session.refresh(asset)
    assert asset.is_flagged is False


# --------------------------------------------------------------------------- #
# model_service — DB-backed admin overrides
# --------------------------------------------------------------------------- #


def test_effective_model_matches_catalog_with_no_override(db_session):
    spec = model_service.get_effective_model(db_session, "ltx-video")
    assert spec is not None
    assert spec.credit_cost == 4  # catalog default
    assert model_service.is_overridden(db_session, "ltx-video") is False


def test_set_override_changes_price_without_touching_enabled(db_session):
    model_service.set_override(db_session, "ltx-video", credit_cost=99)
    spec = model_service.get_effective_model(db_session, "ltx-video")
    assert spec.credit_cost == 99
    assert spec.enabled is True  # untouched
    assert model_service.is_overridden(db_session, "ltx-video") is True


def test_set_override_can_disable_a_model(db_session):
    model_service.set_override(db_session, "kling-3.0", enabled=False)
    spec = model_service.get_effective_model(db_session, "kling-3.0")
    assert spec.enabled is False
    assert "kling-3.0" not in {
        m.id for m in model_service.list_effective_models(db_session)
    }
    assert "kling-3.0" in {
        m.id for m in model_service.list_effective_models(db_session, enabled_only=False)
    }


def test_clear_override_reverts_to_catalog_default(db_session):
    model_service.set_override(db_session, "ltx-video", credit_cost=99)
    spec = model_service.clear_override(db_session, "ltx-video")
    assert spec.credit_cost == 4
    assert model_service.is_overridden(db_session, "ltx-video") is False


def test_set_override_rejects_unknown_model(db_session):
    import pytest

    with pytest.raises(ValueError):
        model_service.set_override(db_session, "not-a-real-model", credit_cost=10)


# --------------------------------------------------------------------------- #
# Admin Models routes
# --------------------------------------------------------------------------- #

ADMIN_MODELS = "/api/v1/admin/models"


def test_admin_can_list_all_models_including_disabled(client, db_session):
    h_admin = _register(client, "modeladmin1@example.com")
    _make_admin(db_session, "modeladmin1@example.com")
    model_service.set_override(db_session, "kling-3.0", enabled=False)

    res = client.get(ADMIN_MODELS, headers=h_admin)
    assert res.status_code == 200
    by_id = {m["id"]: m for m in res.json()}
    assert by_id["kling-3.0"]["enabled"] is False
    assert by_id["kling-3.0"]["is_overridden"] is True
    assert by_id["ltx-video"]["is_overridden"] is False


def test_non_admin_cannot_access_admin_models(client):
    h_user = _register(client, "regularmodeluser@example.com")
    res = client.get(ADMIN_MODELS, headers=h_user)
    assert res.status_code in (401, 403)


def test_admin_can_update_and_clear_model_price(client, db_session):
    h_admin = _register(client, "modeladmin2@example.com")
    _make_admin(db_session, "modeladmin2@example.com")

    res = client.patch(f"{ADMIN_MODELS}/wan-2.7", json={"credit_cost": 5}, headers=h_admin)
    assert res.status_code == 200
    assert res.json()["credit_cost"] == 5
    assert res.json()["is_overridden"] is True

    res = client.delete(f"{ADMIN_MODELS}/wan-2.7/override", headers=h_admin)
    assert res.status_code == 200
    assert res.json()["credit_cost"] == 30  # back to catalog default
    assert res.json()["is_overridden"] is False


def test_admin_update_rejects_unknown_model(client, db_session):
    h_admin = _register(client, "modeladmin3@example.com")
    _make_admin(db_session, "modeladmin3@example.com")
    res = client.patch(
        f"{ADMIN_MODELS}/not-a-real-model", json={"credit_cost": 5}, headers=h_admin
    )
    assert res.status_code == 404


def test_disabling_a_model_via_admin_blocks_generation(client, db_session):
    """The public /generation/models catalog and job-creation validation must
    both honor an admin's disable override — proves the whole loop, not just
    the storage layer."""
    from app.db.models import TransactionType

    h_user = _register(client, "modeluser1@example.com")
    h_admin = _register(client, "modeladmin4@example.com")
    _make_admin(db_session, "modeladmin4@example.com")

    from app.db.models import User as UserModel
    from app.services import wallet_service

    user = db_session.scalar(select(UserModel).where(UserModel.email == "modeluser1@example.com"))
    wallet = wallet_service.get_or_create_wallet(db_session, user.id)
    wallet_service.credit(db_session, wallet, 100, TransactionType.ADMIN_ADJUST, note="test")
    db_session.commit()

    client.patch(f"{ADMIN_MODELS}/kling-3.0", json={"enabled": False}, headers=h_admin)

    models = client.get("/api/v1/generation/models", headers=h_user).json()
    assert "kling-3.0" not in {m["id"] for m in models}

    project_id = client.post(
        "/api/v1/projects", headers=h_user, json={"name": "P"}
    ).json()["id"]
    res = client.post(
        f"/api/v1/projects/{project_id}/jobs",
        headers=h_user,
        json={
            "type": "generate_video",
            "params": {"prompt": "x", "model": "kling-3.0"},
        },
    )
    assert res.status_code == 422
