"""TTS voiceover + transcription jobs (mock audio backend in tests)."""

from __future__ import annotations

from fastapi.testclient import TestClient

P = "/api/v1/projects"


def _project(client: TestClient, headers) -> str:
    return client.post(P, headers=headers, json={"name": "Audio"}).json()["id"]


def _upload_video(client, headers, pid):
    return client.post(
        f"{P}/{pid}/assets",
        headers=headers,
        files={"file": ("clip.mp4", b"\x00\x01video-bytes", "video/mp4")},
    ).json()


def test_tts_job_produces_audio_asset(client: TestClient, auth_headers):
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={"type": "tts", "params": {"text": "Hello there", "voice": "default"}},
    )
    assert res.status_code == 201
    job = res.json()
    assert job["status"] == "succeeded"
    assert job["result_asset"]["kind"] == "audio"
    assert job["result_asset"]["source"] == "generated"


def test_tts_requires_text(client: TestClient, auth_headers):
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={"type": "tts", "params": {}},
    )
    assert res.status_code == 422


def test_transcribe_job_produces_subtitles_asset(client: TestClient, auth_headers):
    pid = _project(client, auth_headers)
    src = _upload_video(client, auth_headers, pid)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={"type": "transcribe", "params": {"asset_id": src["id"]}},
    )
    assert res.status_code == 201
    job = res.json()
    assert job["status"] == "succeeded"
    assert job["result_asset"]["kind"] == "subtitles"
    assert job["result_asset"]["source"] == "derived"

    # The SRT content is downloadable and well-formed.
    srt = client.get(
        f"/api/v1/assets/{job['result_asset']['id']}/content", headers=auth_headers
    )
    assert srt.status_code == 200
    assert "-->" in srt.text


def test_transcribe_requires_asset_id(client: TestClient, auth_headers):
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={"type": "transcribe", "params": {}},
    )
    assert res.status_code == 422


def test_transcribe_missing_asset_fails_job(client: TestClient, auth_headers):
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={"type": "transcribe", "params": {"asset_id": "does-not-exist"}},
    )
    assert res.status_code == 201
    assert res.json()["status"] == "failed"


def test_music_job_produces_audio(client: TestClient, auth_headers):
    pid = _project(client, auth_headers)
    res = client.post(
        f"{P}/{pid}/jobs",
        headers=auth_headers,
        json={"type": "music", "params": {"prompt": "lofi beats"}},
    )
    assert res.status_code == 201
    assert res.json()["result_asset"]["kind"] == "audio"
