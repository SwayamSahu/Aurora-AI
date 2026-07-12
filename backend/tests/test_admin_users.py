"""Admin user management (Phase 1): list/search users, per-user aggregated
detail, role changes, suspend/reactivate, and the last-admin/self-lockout
guardrails. Runs fully on the Mac (no GPU)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import User


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


def _make_admin(db_session, email: str) -> User:
    user = db_session.scalar(select(User).where(User.email == email))
    user.is_superuser = True
    db_session.commit()
    db_session.refresh(user)
    return user


def _get_user(db_session, email: str) -> User:
    return db_session.scalar(select(User).where(User.email == email))


def test_admin_can_list_and_search_users(client: TestClient, db_session):
    _register(client, "alice@example.com")
    _register(client, "bob@example.com")
    h_admin = _register(client, "admin1@example.com")
    _make_admin(db_session, "admin1@example.com")

    res = client.get("/api/v1/admin/users", headers=h_admin)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 3
    emails = {u["email"] for u in body["items"]}
    assert "alice@example.com" in emails

    res = client.get("/api/v1/admin/users?q=alice", headers=h_admin)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["email"] == "alice@example.com"


def test_admin_users_list_is_paginated(client: TestClient, db_session):
    h_admin = _register(client, "admin2@example.com")
    _make_admin(db_session, "admin2@example.com")
    for i in range(5):
        _register(client, f"user{i}@example.com")

    res = client.get("/api/v1/admin/users?limit=2&offset=0", headers=h_admin)
    body = res.json()
    assert len(body["items"]) == 2
    assert body["next_offset"] == 2


def test_admin_can_view_user_detail(client: TestClient, db_session):
    _register(client, "carol@example.com")
    h_admin = _register(client, "admin3@example.com")
    _make_admin(db_session, "admin3@example.com")

    carol = _get_user(db_session, "carol@example.com")
    res = client.get(f"/api/v1/admin/users/{carol.id}", headers=h_admin)
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "carol@example.com"
    assert body["wallet_balance"] == 0
    assert body["post_count"] == 0
    assert body["listing_count"] == 0
    assert "recent_posts" in body
    assert "recent_listings" in body


def test_admin_can_promote_and_demote_role(client: TestClient, db_session):
    _register(client, "dave@example.com")
    h_admin = _register(client, "admin4@example.com")
    _make_admin(db_session, "admin4@example.com")

    dave = _get_user(db_session, "dave@example.com")
    res = client.patch(
        f"/api/v1/admin/users/{dave.id}",
        json={"role": "moderator"},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["role"] == "moderator"

    res = client.patch(
        f"/api/v1/admin/users/{dave.id}",
        json={"role": "user"},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["role"] == "user"


def test_admin_can_suspend_and_reactivate_user(client: TestClient, db_session):
    _register(client, "erin@example.com")
    h_admin = _register(client, "admin5@example.com")
    _make_admin(db_session, "admin5@example.com")

    erin = _get_user(db_session, "erin@example.com")
    res = client.patch(
        f"/api/v1/admin/users/{erin.id}",
        json={"is_active": False},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # A suspended user can no longer authenticate.
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "erin@example.com", "password": "supersecret1"},
    )
    assert login.status_code == 401

    res = client.patch(
        f"/api/v1/admin/users/{erin.id}",
        json={"is_active": True},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is True


def test_admin_cannot_demote_or_suspend_self(client: TestClient, db_session):
    h_admin = _register(client, "admin6@example.com")
    admin = _make_admin(db_session, "admin6@example.com")

    res = client.patch(
        f"/api/v1/admin/users/{admin.id}",
        json={"role": "user"},
        headers=h_admin,
    )
    assert res.status_code == 400

    res = client.patch(
        f"/api/v1/admin/users/{admin.id}",
        json={"is_active": False},
        headers=h_admin,
    )
    assert res.status_code == 400


def test_admin_can_demote_a_peer_when_another_admin_remains(client: TestClient, db_session):
    h_admin = _register(client, "admin7@example.com")
    _make_admin(db_session, "admin7@example.com")
    _register(client, "admin7b@example.com")
    peer = _make_admin(db_session, "admin7b@example.com")

    # Two active admins exist, so demoting one (not self) via the other succeeds.
    res = client.patch(
        f"/api/v1/admin/users/{peer.id}",
        json={"role": "user"},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["role"] == "user"


def test_last_admin_guard_blocks_self_demotion_even_alone(client: TestClient, db_session):
    # With exactly one active admin, the only way to reach the last-admin
    # scenario is via self-action, which the self-lockout check already
    # rejects — confirming the sole admin can never be locked out.
    h_admin = _register(client, "admin7c@example.com")
    admin = _make_admin(db_session, "admin7c@example.com")

    res = client.patch(
        f"/api/v1/admin/users/{admin.id}",
        json={"role": "user"},
        headers=h_admin,
    )
    assert res.status_code == 400


def test_role_change_and_suspend_are_audited(client: TestClient, db_session):
    _register(client, "frank@example.com")
    h_admin = _register(client, "admin8@example.com")
    _make_admin(db_session, "admin8@example.com")

    frank = _get_user(db_session, "frank@example.com")
    client.patch(
        f"/api/v1/admin/users/{frank.id}",
        json={"role": "moderator"},
        headers=h_admin,
    )
    client.patch(
        f"/api/v1/admin/users/{frank.id}",
        json={"is_active": False},
        headers=h_admin,
    )

    res = client.get(
        "/api/v1/admin/audit?target_type=user",
        headers=h_admin,
    )
    assert res.status_code == 200
    actions = {a["action"] for a in res.json()["items"]}
    assert "user.role_change" in actions
    assert "user.suspend" in actions


def test_non_admin_gets_403_on_user_management(client: TestClient, db_session):
    h_user = _register(client, "gina@example.com")
    other = _register(client, "harold@example.com")
    harold = _get_user(db_session, "harold@example.com")

    res = client.get("/api/v1/admin/users", headers=h_user)
    assert res.status_code == 403

    res = client.patch(
        f"/api/v1/admin/users/{harold.id}",
        json={"role": "admin"},
        headers=h_user,
    )
    assert res.status_code == 403
