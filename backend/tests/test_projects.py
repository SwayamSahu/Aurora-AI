"""Project CRUD + ownership isolation."""

from __future__ import annotations

from fastapi.testclient import TestClient

P = "/api/v1/projects"


def _other_user_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": "mallory@example.com", "password": "password999"},
    )
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "mallory@example.com", "password": "password999"},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_create_and_get_project(client: TestClient, auth_headers):
    res = client.post(P, headers=auth_headers, json={"name": "My Film"})
    assert res.status_code == 201
    pid = res.json()["id"]

    got = client.get(f"{P}/{pid}", headers=auth_headers)
    assert got.status_code == 200
    assert got.json()["name"] == "My Film"
    assert got.json()["asset_count"] == 0


def test_create_requires_auth(client: TestClient):
    assert client.post(P, json={"name": "X"}).status_code == 401


def test_list_projects_with_search_and_sort(client: TestClient, auth_headers):
    for name in ["Alpha", "Beta", "Gamma"]:
        client.post(P, headers=auth_headers, json={"name": name})

    all_res = client.get(P, headers=auth_headers)
    assert all_res.status_code == 200
    assert len(all_res.json()) == 3

    searched = client.get(f"{P}?search=alph", headers=auth_headers)
    assert [p["name"] for p in searched.json()] == ["Alpha"]

    by_name = client.get(f"{P}?sort=name", headers=auth_headers)
    assert [p["name"] for p in by_name.json()] == ["Alpha", "Beta", "Gamma"]


def test_update_project(client: TestClient, auth_headers):
    pid = client.post(P, headers=auth_headers, json={"name": "Old"}).json()["id"]
    res = client.patch(
        f"{P}/{pid}", headers=auth_headers, json={"name": "New", "description": "d"}
    )
    assert res.status_code == 200
    assert res.json()["name"] == "New"
    assert res.json()["description"] == "d"


def test_delete_project(client: TestClient, auth_headers):
    pid = client.post(P, headers=auth_headers, json={"name": "Temp"}).json()["id"]
    assert client.delete(f"{P}/{pid}", headers=auth_headers).status_code == 204
    assert client.get(f"{P}/{pid}", headers=auth_headers).status_code == 404


def test_duplicate_project(client: TestClient, auth_headers):
    pid = client.post(P, headers=auth_headers, json={"name": "Orig"}).json()["id"]
    res = client.post(f"{P}/{pid}/duplicate", headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["name"] == "Orig (copy)"
    assert len(client.get(P, headers=auth_headers).json()) == 2


def test_ownership_isolation(client: TestClient, auth_headers):
    pid = client.post(P, headers=auth_headers, json={"name": "Secret"}).json()["id"]
    other = _other_user_headers(client)
    # Other user can't see or touch it.
    assert client.get(f"{P}/{pid}", headers=other).status_code == 404
    assert client.delete(f"{P}/{pid}", headers=other).status_code == 404
    assert client.get(P, headers=other).json() == []
