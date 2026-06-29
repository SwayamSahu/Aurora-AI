"""Timeline document load/save + non-destructive round-trip."""

from __future__ import annotations

from fastapi.testclient import TestClient

P = "/api/v1/projects"


def _project(client: TestClient, headers) -> str:
    return client.post(P, headers=headers, json={"name": "Edit"}).json()["id"]


def test_get_timeline_creates_default(client: TestClient, auth_headers):
    pid = _project(client, auth_headers)
    res = client.get(f"{P}/{pid}/timeline", headers=auth_headers)
    assert res.status_code == 200
    doc = res.json()["document"]
    types = [t["type"] for t in doc["tracks"]]
    assert types == ["video", "text", "audio"]
    assert all(t["clips"] == [] for t in doc["tracks"])


def test_save_and_reload_timeline(client: TestClient, auth_headers):
    pid = _project(client, auth_headers)
    base = client.get(f"{P}/{pid}/timeline", headers=auth_headers).json()["document"]

    # Add a clip to the video track.
    base["version"] = 2
    base["tracks"][0]["clips"].append(
        {
            "id": "clip-1",
            "kind": "video",
            "asset_id": "asset-xyz",
            "start": 0.0,
            "duration": 4.0,
            "trim_start": 0.5,
        }
    )
    save = client.put(f"{P}/{pid}/timeline", headers=auth_headers, json=base)
    assert save.status_code == 200
    assert save.json()["version"] == 2

    reload = client.get(f"{P}/{pid}/timeline", headers=auth_headers).json()
    clips = reload["document"]["tracks"][0]["clips"]
    assert len(clips) == 1
    assert clips[0]["asset_id"] == "asset-xyz"
    assert clips[0]["trim_start"] == 0.5


def test_save_text_clip_preserves_fields(client: TestClient, auth_headers):
    pid = _project(client, auth_headers)
    doc = client.get(f"{P}/{pid}/timeline", headers=auth_headers).json()["document"]
    doc["tracks"][1]["clips"].append(
        {
            "id": "t1",
            "kind": "text",
            "start": 1.0,
            "duration": 3.0,
            "text": "Hello world",
            "style": {"fontSize": 48, "color": "#fff"},
        }
    )
    client.put(f"{P}/{pid}/timeline", headers=auth_headers, json=doc)
    reload = client.get(f"{P}/{pid}/timeline", headers=auth_headers).json()
    clip = reload["document"]["tracks"][1]["clips"][0]
    assert clip["text"] == "Hello world"
    assert clip["style"]["fontSize"] == 48


def test_timeline_requires_ownership(client: TestClient, auth_headers):
    pid = _project(client, auth_headers)
    client.post(
        "/api/v1/auth/register",
        json={"email": "nope@example.com", "password": "passwordnope"},
    )
    other = {
        "Authorization": "Bearer "
        + client.post(
            "/api/v1/auth/login",
            data={"username": "nope@example.com", "password": "passwordnope"},
        ).json()["access_token"]
    }
    assert client.get(f"{P}/{pid}/timeline", headers=other).status_code == 404


def test_invalid_document_rejected(client: TestClient, auth_headers):
    pid = _project(client, auth_headers)
    # tracks must be a list of track objects.
    res = client.put(
        f"{P}/{pid}/timeline",
        headers=auth_headers,
        json={"version": 1, "tracks": [{"id": "x"}]},  # missing type/name
    )
    assert res.status_code == 422
