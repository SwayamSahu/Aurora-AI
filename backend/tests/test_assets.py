"""Asset upload / list / download / rename / delete + storage round-trip."""

from __future__ import annotations

from fastapi.testclient import TestClient

P = "/api/v1/projects"
A = "/api/v1/assets"


def _make_project(client: TestClient, headers) -> str:
    return client.post(P, headers=headers, json={"name": "Media"}).json()["id"]


def _upload(client: TestClient, headers, pid, content=b"\x00\x01\x02data", ct="video/mp4", name="clip.mp4"):
    return client.post(
        f"{P}/{pid}/assets",
        headers=headers,
        files={"file": (name, content, ct)},
    )


def test_upload_and_list_asset(client: TestClient, auth_headers):
    pid = _make_project(client, auth_headers)
    res = _upload(client, auth_headers, pid)
    assert res.status_code == 201
    body = res.json()
    assert body["kind"] == "video"
    assert body["source"] == "uploaded"
    assert body["url"].endswith("/content")

    listing = client.get(f"{P}/{pid}/assets", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    # Project asset_count reflects the upload.
    assert client.get(f"{P}/{pid}", headers=auth_headers).json()["asset_count"] == 1


def test_kind_inference_and_filter(client: TestClient, auth_headers):
    pid = _make_project(client, auth_headers)
    _upload(client, auth_headers, pid, content=b"img", ct="image/png", name="a.png")
    _upload(client, auth_headers, pid, content=b"vid", ct="video/mp4", name="b.mp4")

    images = client.get(f"{P}/{pid}/assets?kind=image", headers=auth_headers)
    assert [a["kind"] for a in images.json()] == ["image"]


def test_download_content_roundtrip(client: TestClient, auth_headers):
    pid = _make_project(client, auth_headers)
    payload = b"hello-bytes-1234"
    asset = _upload(client, auth_headers, pid, content=payload).json()

    res = client.get(f"{A}/{asset['id']}/content", headers=auth_headers)
    assert res.status_code == 200
    assert res.content == payload
    assert res.headers["content-type"].startswith("video/mp4")


def test_content_via_query_token(client: TestClient, auth_headers):
    pid = _make_project(client, auth_headers)
    asset = _upload(client, auth_headers, pid, content=b"q").json()
    token = auth_headers["Authorization"].split(" ", 1)[1]
    # No header — token passed via query (for <video>/<img> tags).
    res = client.get(f"{A}/{asset['id']}/content?token={token}")
    assert res.status_code == 200
    assert res.content == b"q"


def test_content_requires_auth(client: TestClient, auth_headers):
    pid = _make_project(client, auth_headers)
    asset = _upload(client, auth_headers, pid, content=b"x").json()
    assert client.get(f"{A}/{asset['id']}/content").status_code == 401


def test_rename_asset(client: TestClient, auth_headers):
    pid = _make_project(client, auth_headers)
    asset = _upload(client, auth_headers, pid).json()
    res = client.patch(
        f"{A}/{asset['id']}", headers=auth_headers, json={"name": "renamed.mp4"}
    )
    assert res.status_code == 200
    assert res.json()["name"] == "renamed.mp4"


def test_delete_asset_removes_content(client: TestClient, auth_headers):
    pid = _make_project(client, auth_headers)
    asset = _upload(client, auth_headers, pid).json()
    assert client.delete(f"{A}/{asset['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"{A}/{asset['id']}/content", headers=auth_headers).status_code == 404


def test_empty_upload_rejected(client: TestClient, auth_headers):
    pid = _make_project(client, auth_headers)
    res = _upload(client, auth_headers, pid, content=b"")
    assert res.status_code == 400


def test_cross_user_asset_isolation(client: TestClient, auth_headers):
    pid = _make_project(client, auth_headers)
    asset = _upload(client, auth_headers, pid).json()

    client.post(
        "/api/v1/auth/register",
        json={"email": "eve@example.com", "password": "passwordeve"},
    )
    other = {
        "Authorization": "Bearer "
        + client.post(
            "/api/v1/auth/login",
            data={"username": "eve@example.com", "password": "passwordeve"},
        ).json()["access_token"]
    }
    assert client.get(f"{A}/{asset['id']}", headers=other).status_code == 404
    assert client.delete(f"{A}/{asset['id']}", headers=other).status_code == 404
