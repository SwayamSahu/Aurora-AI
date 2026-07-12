"""Admin Phase 4: system health dashboard. Runs fully on the Mac (no GPU)."""

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


def _make_admin(db_session, email: str) -> None:
    user = db_session.scalar(select(User).where(User.email == email))
    user.is_superuser = True
    db_session.commit()


def test_admin_can_view_system_health(client: TestClient, db_session):
    h_admin = _register(client, "healthadmin1@example.com")
    _make_admin(db_session, "healthadmin1@example.com")

    res = client.get("/api/v1/admin/system/health", headers=h_admin)
    assert res.status_code == 200
    body = res.json()
    assert body["database"]["ok"] is True
    assert "counts" in body
    assert body["counts"]["total_users"] >= 1
    assert "generator_backend" in body


def test_non_admin_gets_403_on_system_health(client: TestClient, db_session):
    h_user = _register(client, "healthuser1@example.com")
    res = client.get("/api/v1/admin/system/health", headers=h_user)
    assert res.status_code == 403
