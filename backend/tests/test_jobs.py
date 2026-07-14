"""Generation jobs: the mock generator wired through the async job pipeline.

Runs in eager mode (inline), so a created job is terminal by the time the
response returns — proving the full generate→asset loop on the Mac.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

P = "/api/v1/projects"
J = "/api/v1/jobs"


def _project(client: TestClient, headers) -> str:
    return client.post(P, headers=headers, json={"name": "Gen"}).json()["id"]


def _fund_wallet(db_session, credits: int, email: str = "alice@example.com") -> None:
    """Grants `credits` to the `auth_headers` fixture's user — named-model
    generation debits the wallet, so billing tests need a funded balance."""
    from sqlalchemy import select

    from app.db.models import TransactionType, User
    from app.services import wallet_service

    user = db_session.scalar(select(User).where(User.email == email))
    wallet = wallet_service.get_or_create_wallet(db_session, user.id)
    wallet_service.credit(
        db_session, wallet, credits, TransactionType.ADMIN_ADJUST, note="test funding"
    )
    db_session.commit()


def _create_video_job(client, headers, pid, prompt="a cat surfing"):
    return client.post(
        f"{P}/{pid}/jobs",
        headers=headers,
        json={
            "type": "generate_video",
            "params": {"prompt": prompt, "duration_seconds": 4},
        },
    )


def test_create_video_job_succeeds_and_produces_asset(client, auth_headers):
    pid = _project(client, auth_headers)
    res = _create_video_job(client, auth_headers, pid)
    assert res.status_code == 201
    job = res.json()
    assert job["type"] == "generate_video"
    assert job["status"] == "succeeded"
    assert job["progress"] == 1.0
    assert job["result_asset"] is not None
    assert job["result_asset"]["kind"] == "video"
    assert job["result_asset"]["source"] == "generated"

    # Generated asset shows up in the project library.
    assets = client.get(f"{P}/{pid}/assets", headers=auth_headers).json()
    assert len(assets) == 1
    assert assets[0]["id"] == job["result_asset"]["id"]


def test_create_image_job(client, auth_headers):
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={"type": "generate_image", "params": {"prompt": "a sunset"}},
    )
    assert res.status_code == 201
    assert res.json()["status"] == "succeeded"
    assert res.json()["result_asset"]["kind"] == "image"


def test_job_requires_prompt(client, auth_headers):
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={"type": "generate_video", "params": {}},
    )
    assert res.status_code == 422


def test_unsupported_job_type_rejected(client, auth_headers):
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={"type": "export", "params": {"prompt": "x"}},
    )
    assert res.status_code == 422


def test_list_and_get_jobs(client, auth_headers):
    pid = _project(client, auth_headers)
    _create_video_job(client, auth_headers, pid)
    _create_video_job(client, auth_headers, pid)

    all_jobs = client.get(J, headers=auth_headers).json()
    assert len(all_jobs) == 2

    succeeded = client.get(f"{J}?status=succeeded", headers=auth_headers).json()
    assert len(succeeded) == 2

    filtered = client.get(f"{J}?project_id={pid}", headers=auth_headers).json()
    assert len(filtered) == 2

    one = client.get(f"{J}/{all_jobs[0]['id']}", headers=auth_headers)
    assert one.status_code == 200


def test_retry_job_creates_new_job(client, auth_headers):
    pid = _project(client, auth_headers)
    job = _create_video_job(client, auth_headers, pid).json()
    retry = client.post(f"{J}/{job['id']}/retry", headers=auth_headers)
    assert retry.status_code == 201
    assert retry.json()["id"] != job["id"]
    assert len(client.get(J, headers=auth_headers).json()) == 2


def test_jobs_owner_isolation(client, auth_headers):
    pid = _project(client, auth_headers)
    job = _create_video_job(client, auth_headers, pid).json()

    client.post(
        "/api/v1/auth/register",
        json={"email": "intruder@example.com", "password": "passwordxyz"},
    )
    other = {
        "Authorization": "Bearer "
        + client.post(
            "/api/v1/auth/login",
            data={"username": "intruder@example.com", "password": "passwordxyz"},
        ).json()["access_token"]
    }
    assert client.get(f"{J}/{job['id']}", headers=other).status_code == 404
    assert client.get(J, headers=other).json() == []


def test_websocket_streams_terminal_state(client, auth_headers):
    pid = _project(client, auth_headers)
    job = _create_video_job(client, auth_headers, pid).json()
    token = auth_headers["Authorization"].split(" ", 1)[1]

    with client.websocket_connect(
        f"/api/v1/ws/jobs/{job['id']}?token={token}"
    ) as ws:
        event = ws.receive_json()
        assert event["id"] == job["id"]
        assert event["status"] == "succeeded"
        assert event["progress"] == 1.0


def test_websocket_rejects_missing_token(client, auth_headers):
    pid = _project(client, auth_headers)
    job = _create_video_job(client, auth_headers, pid).json()
    import pytest
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/api/v1/ws/jobs/{job['id']}") as ws:
            ws.receive_json()


# --------------------------------------------------------------------------- #
# Multi-model video generation
# --------------------------------------------------------------------------- #
MODELS = "/api/v1/generation/models"


def test_model_catalog_endpoint_lists_models(client, auth_headers):
    res = client.get(MODELS, headers=auth_headers)
    assert res.status_code == 200
    models = res.json()
    ids = {m["id"] for m in models}
    # A local default plus the requested hosted models are all selectable.
    assert "ltx-video" in ids
    assert {"kling-3.0", "veo-3.1-lite", "seedance-2.0", "wan-2.7"} <= ids
    # Each entry carries the capability envelope the picker needs.
    kling = next(m for m in models if m["id"] == "kling-3.0")
    assert kling["min_duration"] == 3 and kling["max_duration"] == 15
    assert kling["resolution"] == "4K"
    assert "provider" in kling and "badges" in kling


def test_generate_with_named_model_succeeds(client, auth_headers, db_session):
    _fund_wallet(db_session, 100)
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={
            "type": "generate_video",
            "params": {"prompt": "a fox", "model": "kling-3.0", "duration_seconds": 5},
        },
    )
    assert res.status_code == 201
    assert res.json()["status"] == "succeeded"


def test_generate_with_unknown_model_rejected(client, auth_headers):
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={
            "type": "generate_video",
            "params": {"prompt": "a fox", "model": "not-a-real-model"},
        },
    )
    assert res.status_code == 422
    assert "model" in res.json()["detail"].lower()


def test_named_model_debits_wallet_and_charges_are_snapshotted(
    client, auth_headers, db_session
):
    _fund_wallet(db_session, 100)
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={
            "type": "generate_video",
            "params": {"prompt": "a fox", "model": "kling-3.0", "duration_seconds": 5},
        },
    )
    assert res.status_code == 201
    assert res.json()["status"] == "succeeded"

    wallet = client.get("/api/v1/marketplace/wallet", headers=auth_headers).json()
    assert wallet["balance_credits"] == 100 - 65  # kling-3.0 costs 65 credits

    job = res.json()
    from app.db.models import Job

    row = db_session.get(Job, job["id"])
    assert row.credits_charged == 65  # snapshotted even though job succeeded


def test_insufficient_credits_rejected_and_no_job_created(client, auth_headers):
    """A brand-new user has a 0 balance — a paid model must 402 rather than
    silently running for free, and no job row should be left behind."""
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={
            "type": "generate_video",
            "params": {"prompt": "a fox", "model": "kling-3.0"},
        },
    )
    assert res.status_code == 402
    assert client.get(J, headers=auth_headers).json() == []


def test_unnamed_model_generation_is_unmetered(client, auth_headers):
    """Omitting `model` is allowed and must not touch the wallet at all."""
    pid = _project(client, auth_headers)
    res = _create_video_job(client, auth_headers, pid)
    assert res.status_code == 201
    wallet = client.get("/api/v1/marketplace/wallet", headers=auth_headers).json()
    assert wallet["balance_credits"] == 0


def test_refund_credits_restores_wallet_balance(client, auth_headers, db_session):
    """Unit-level: a job that was charged but then fails should have its
    credits refunded and its own `credits_charged` zeroed (so a second
    failure-handling pass can't double-refund)."""
    from app.db.models import Job, JobType
    from app.services import job_service

    _fund_wallet(db_session, 100)
    pid = _project(client, auth_headers)

    job = job_service.create(
        db_session, pid, JobType.GENERATE_VIDEO, {"prompt": "x"}, credits_charged=40
    )
    job_service.refund_credits(db_session, job)

    wallet = client.get("/api/v1/marketplace/wallet", headers=auth_headers).json()
    assert wallet["balance_credits"] == 100 + 40
    db_session.refresh(job)
    assert job.credits_charged == 0

    # Refunding again is a safe no-op — must not double-credit.
    job_service.refund_credits(db_session, job)
    wallet = client.get("/api/v1/marketplace/wallet", headers=auth_headers).json()
    assert wallet["balance_credits"] == 100 + 40


def test_generation_clamps_duration_to_model_range(client, auth_headers, db_session):
    """kling-3.0 min duration is 3s; a 1s request must be clamped up on the
    produced asset rather than rejected."""
    from app.db.models import Asset

    _fund_wallet(db_session, 100)
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={
            "type": "generate_video",
            "params": {"prompt": "a fox", "model": "kling-3.0", "duration_seconds": 1},
        },
    )
    assert res.status_code == 201
    job = res.json()
    assert job["status"] == "succeeded"
    asset = db_session.get(Asset, job["result_asset"]["id"])
    # The mock generator renders exactly the (clamped) requested duration.
    assert asset.duration_seconds is not None
    assert asset.duration_seconds >= 3.0
