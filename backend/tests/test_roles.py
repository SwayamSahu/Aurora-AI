"""Role system (F2) — user/moderator/admin gating, and the back-compat
`is_superuser` hybrid. Runs fully on the Mac (no GPU)."""

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


def _set_role(db_session, email: str, role: UserRole) -> None:
    user = db_session.scalar(select(User).where(User.email == email))
    user.role = role
    db_session.commit()


def _create_post(client, headers, **overrides):
    payload = {
        "title": "Role Test Post",
        "category": "tutorials",
        "body_html": "<p>Body.</p>",
        "status": "published",
        **overrides,
    }
    return client.post("/api/v1/blog/posts", json=payload, headers=headers)


# --------------------------- back-compat hybrid ----------------------------- #
def test_is_superuser_hybrid_maps_to_role(db_session):
    from app.core.security import hash_password

    user = User(email="hy@example.com", hashed_password=hash_password("x"))
    db_session.add(user)
    db_session.commit()

    # Defaults to the plain user role.
    assert user.role == UserRole.USER
    assert user.is_superuser is False
    assert user.is_moderator is False

    # Setting the back-compat flag flips the role.
    user.is_superuser = True
    assert user.role == UserRole.ADMIN
    assert user.is_superuser is True
    assert user.is_moderator is True  # admin is a superset of moderator

    user.is_superuser = False
    assert user.role == UserRole.USER


def test_moderator_is_not_superuser_but_is_moderator(db_session):
    from app.core.security import hash_password

    user = User(
        email="mod@example.com",
        hashed_password=hash_password("x"),
        role=UserRole.MODERATOR,
    )
    db_session.add(user)
    db_session.commit()
    assert user.is_moderator is True
    assert user.is_superuser is False


def test_userread_exposes_role(client: TestClient, db_session):
    _register(client, "roleuser@example.com")
    _set_role(db_session, "roleuser@example.com", UserRole.MODERATOR)
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "roleuser@example.com", "password": "supersecret1"},
    )
    user = res.json()["user"]
    assert user["role"] == "moderator"
    assert user["is_superuser"] is False


# ------------------------- moderator: content only -------------------------- #
def test_moderator_can_edit_any_post(client: TestClient, db_session):
    h_author = _register(client, "rauthor1@example.com")
    post = _create_post(client, h_author).json()

    h_mod = _register(client, "rmod1@example.com")
    _set_role(db_session, "rmod1@example.com", UserRole.MODERATOR)

    res = client.patch(
        f"/api/v1/blog/posts/{post['id']}",
        json={"title": "Edited by moderator"},
        headers=h_mod,
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Edited by moderator"


def test_moderator_can_access_content_moderation_dashboards(
    client: TestClient, db_session
):
    h_mod = _register(client, "rmod2@example.com")
    _set_role(db_session, "rmod2@example.com", UserRole.MODERATOR)

    assert client.get("/api/v1/admin/blog/posts", headers=h_mod).status_code == 200
    assert (
        client.get("/api/v1/admin/marketplace/listings", headers=h_mod).status_code
        == 200
    )


def test_moderator_cannot_touch_finance(client: TestClient, db_session):
    h_mod = _register(client, "rmod3@example.com")
    _set_role(db_session, "rmod3@example.com", UserRole.MODERATOR)

    # Plan catalog (admin-only).
    assert (
        client.get("/api/v1/admin/marketplace/plans", headers=h_mod).status_code == 403
    )
    assert (
        client.post(
            "/api/v1/admin/marketplace/plans",
            json={
                "name": "X",
                "price_cents": 0,
                "credits_granted": 0,
                "listing_quota": 1,
            },
            headers=h_mod,
        ).status_code
        == 403
    )
    # Wallet adjustment (admin-only).
    assert (
        client.post(
            "/api/v1/admin/marketplace/wallets/some-user/adjust",
            json={"amount": 100, "note": "nope"},
            headers=h_mod,
        ).status_code
        == 403
    )
    # Refund (admin-only).
    assert (
        client.post(
            "/api/v1/admin/marketplace/orders/some-order/refund", headers=h_mod
        ).status_code
        == 403
    )


# ------------------------------- admin: all --------------------------------- #
def test_admin_passes_both_moderator_and_admin_gates(client: TestClient, db_session):
    h_admin = _register(client, "radmin1@example.com")
    _set_role(db_session, "radmin1@example.com", UserRole.ADMIN)

    # Content moderation (moderator gate).
    assert client.get("/api/v1/admin/blog/posts", headers=h_admin).status_code == 200
    # Finance (admin gate).
    assert (
        client.get("/api/v1/admin/marketplace/plans", headers=h_admin).status_code
        == 200
    )


def test_regular_user_blocked_from_all_admin(client: TestClient, db_session):
    h = _register(client, "ruser@example.com")
    assert client.get("/api/v1/admin/blog/posts", headers=h).status_code == 403
    assert (
        client.get("/api/v1/admin/marketplace/listings", headers=h).status_code == 403
    )
    assert client.get("/api/v1/admin/marketplace/plans", headers=h).status_code == 403
