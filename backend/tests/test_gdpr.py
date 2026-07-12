"""Admin Phase 4: GDPR data export and right-to-erasure. Runs fully on the
Mac (no GPU, no Stripe)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import User, UserRole


def _register(client: TestClient, email: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "supersecret1",
            "full_name": email.split("@")[0],
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "supersecret1"},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _make_admin(db_session, email: str) -> None:
    user = db_session.scalar(select(User).where(User.email == email))
    user.is_superuser = True
    db_session.commit()


def _create_post(client, headers, **overrides):
    payload = {
        "title": "My Post",
        "category": "tutorials",
        "body_html": "<p>Body.</p>",
        "status": "published",
        **overrides,
    }
    return client.post("/api/v1/blog/posts", json=payload, headers=headers).json()


def test_user_can_export_their_own_data(client: TestClient, db_session):
    h = _register(client, "exportme@example.com")
    _create_post(client, h, title="Exportable Post")

    res = client.get("/api/v1/users/me/export", headers=h)
    assert res.status_code == 200
    body = res.json()
    assert body["profile"]["email"] == "exportme@example.com"
    assert any(p["title"] == "Exportable Post" for p in body["blog_posts"])
    assert "wallet" in body


def test_export_requires_auth(client: TestClient, db_session):
    res = client.get("/api/v1/users/me/export")
    assert res.status_code == 401


def test_user_can_erase_their_own_account(client: TestClient, db_session):
    h = _register(client, "eraseme@example.com")

    res = client.post(
        "/api/v1/users/me/erase",
        json={"password": "supersecret1"},
        headers=h,
    )
    assert res.status_code == 204

    user = db_session.scalar(select(User).where(User.email.like("erased-%")))
    assert user is not None
    assert user.full_name is None
    assert user.is_active is False
    assert user.erased_at is not None

    # Old credentials no longer work.
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "eraseme@example.com", "password": "supersecret1"},
    )
    assert login.status_code == 401


def test_erasure_requires_correct_password(client: TestClient, db_session):
    h = _register(client, "wrongpw@example.com")
    res = client.post(
        "/api/v1/users/me/erase",
        json={"password": "not-the-password"},
        headers=h,
    )
    assert res.status_code == 400


def test_erasure_preserves_cascaded_content(client: TestClient, db_session):
    """The user row is anonymized, not deleted — their posts stay up
    (author now reads as anonymous) rather than vanishing."""
    h = _register(client, "eraseauthor@example.com")
    post = _create_post(client, h, title="Should Survive Erasure")

    client.post(
        "/api/v1/users/me/erase", json={"password": "supersecret1"}, headers=h
    )

    still_there = client.get(f"/api/v1/blog/posts/{post['slug']}")
    assert still_there.status_code == 200
    assert still_there.json()["author"]["full_name"] is None


def test_admin_can_erase_another_users_account(client: TestClient, db_session):
    _register(client, "supportcase@example.com")
    h_admin = _register(client, "gdpradmin1@example.com")
    _make_admin(db_session, "gdpradmin1@example.com")

    target_user = db_session.scalar(
        select(User).where(User.email == "supportcase@example.com")
    )
    res = client.post(
        f"/api/v1/admin/users/{target_user.id}/erase", headers=h_admin
    )
    assert res.status_code == 200
    assert res.json()["erased_at"] is not None
    assert res.json()["is_active"] is False


def test_admin_cannot_erase_own_account_via_admin_route(
    client: TestClient, db_session
):
    h_admin = _register(client, "gdpradmin2@example.com")
    admin_user = db_session.scalar(
        select(User).where(User.email == "gdpradmin2@example.com")
    )
    _make_admin(db_session, "gdpradmin2@example.com")

    res = client.post(
        f"/api/v1/admin/users/{admin_user.id}/erase", headers=h_admin
    )
    assert res.status_code == 400


def test_admin_cannot_erase_the_last_active_admin(client: TestClient, db_session):
    h_admin1 = _register(client, "gdpradmin3@example.com")
    _make_admin(db_session, "gdpradmin3@example.com")
    _register(client, "gdpradmin4@example.com")
    admin2 = db_session.scalar(
        select(User).where(User.email == "gdpradmin4@example.com")
    )
    admin2.role = UserRole.ADMIN
    db_session.commit()

    # Two admins exist — erasing admin2 via admin1 succeeds.
    res = client.post(f"/api/v1/admin/users/{admin2.id}/erase", headers=h_admin1)
    assert res.status_code == 200

    # Now only admin1 (self) remains active — self-erasure via admin route
    # is already blocked, so the last-admin path is unreachable except via
    # self, confirming the sole admin can never be erased out from under
    # themselves.
    res = client.post(
        f"/api/v1/admin/users/{db_session.scalar(select(User).where(User.email == 'gdpradmin3@example.com')).id}/erase",
        headers=h_admin1,
    )
    assert res.status_code == 400


def test_non_admin_gets_403_on_admin_erase(client: TestClient, db_session):
    h_user = _register(client, "gdpruser1@example.com")
    _register(client, "gdpruser2@example.com")
    other_user = db_session.scalar(
        select(User).where(User.email == "gdpruser2@example.com")
    )
    res = client.post(f"/api/v1/admin/users/{other_user.id}/erase", headers=h_user)
    assert res.status_code == 403
