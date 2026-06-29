"""Auth flow tests: register, login, me, password reset, profile, password change."""

from __future__ import annotations

from fastapi.testclient import TestClient

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"


def _register(client: TestClient, email="bob@example.com", pw="password123"):
    return client.post(
        REGISTER, json={"email": email, "password": pw, "full_name": "Bob"}
    )


def test_register_returns_token_and_user(client: TestClient):
    res = _register(client)
    assert res.status_code == 201
    body = res.json()
    assert body["access_token"]
    assert body["user"]["email"] == "bob@example.com"
    assert "hashed_password" not in body["user"]


def test_register_duplicate_email_conflicts(client: TestClient):
    _register(client)
    res = _register(client)
    assert res.status_code == 409


def test_register_rejects_short_password(client: TestClient):
    res = client.post(REGISTER, json={"email": "x@y.com", "password": "short"})
    assert res.status_code == 422


def test_login_success(client: TestClient):
    _register(client)
    res = client.post(
        LOGIN, data={"username": "bob@example.com", "password": "password123"}
    )
    assert res.status_code == 200
    assert res.json()["access_token"]


def test_login_wrong_password(client: TestClient):
    _register(client)
    res = client.post(
        LOGIN, data={"username": "bob@example.com", "password": "WRONG"}
    )
    assert res.status_code == 401


def test_me_requires_auth(client: TestClient):
    assert client.get(ME).status_code == 401


def test_me_with_token(client: TestClient, auth_headers):
    res = client.get(ME, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "alice@example.com"


def test_me_rejects_garbage_token(client: TestClient):
    res = client.get(ME, headers={"Authorization": "Bearer not.a.jwt"})
    assert res.status_code == 401


def test_update_profile(client: TestClient, auth_headers):
    res = client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"full_name": "Alice Smith", "preferences": {"default_model": "ltx"}},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["full_name"] == "Alice Smith"
    assert body["preferences"]["default_model"] == "ltx"


def test_change_password_flow(client: TestClient, auth_headers):
    # wrong current password rejected
    bad = client.post(
        "/api/v1/users/me/change-password",
        headers=auth_headers,
        json={"current_password": "WRONG", "new_password": "newpass12345"},
    )
    assert bad.status_code == 400

    ok = client.post(
        "/api/v1/users/me/change-password",
        headers=auth_headers,
        json={"current_password": "supersecret1", "new_password": "newpass12345"},
    )
    assert ok.status_code == 204

    # old password no longer works, new one does
    assert (
        client.post(
            LOGIN, data={"username": "alice@example.com", "password": "supersecret1"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            LOGIN, data={"username": "alice@example.com", "password": "newpass12345"}
        ).status_code
        == 200
    )


def test_password_reset_flow(client: TestClient):
    _register(client, email="carol@example.com", pw="initialpass1")
    # request reset — dev returns the token
    req = client.post(
        "/api/v1/auth/password-reset/request", json={"email": "carol@example.com"}
    )
    assert req.status_code == 200
    token = req.json()["reset_token"]
    assert token

    # confirm with new password
    confirm = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "resetpass999"},
    )
    assert confirm.status_code == 200

    # can log in with the new password
    assert (
        client.post(
            LOGIN, data={"username": "carol@example.com", "password": "resetpass999"}
        ).status_code
        == 200
    )


def test_password_reset_unknown_email_still_ok(client: TestClient):
    res = client.post(
        "/api/v1/auth/password-reset/request", json={"email": "ghost@example.com"}
    )
    assert res.status_code == 200
    assert res.json()["reset_token"] is None


def test_password_reset_invalid_token(client: TestClient):
    res = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "bogus", "new_password": "whatever12345"},
    )
    assert res.status_code == 400
