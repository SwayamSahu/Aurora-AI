"""Admin Phase 4: automated content-safety scanning on upload. Uses the
mock classifier's deterministic marker (see
`app.generators.mock.content_safety.FORCE_FLAG_MARKER`) to force a flagged
result without a real model. Runs fully on the Mac (no GPU)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import User
from app.generators.mock.content_safety import FORCE_FLAG_MARKER


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


def test_clean_upload_is_not_flagged(client: TestClient, db_session):
    author = _register(client, "safeupload@example.com")
    png = b"\x89PNG\r\n\x1a\nfake-but-good-enough-for-storage-round-trip"
    res = client.post(
        "/api/v1/blog/media",
        files={"file": ("cover.png", png, "image/png")},
        headers=author,
    )
    assert res.status_code == 201


def test_blog_media_flagged_by_scan_creates_system_report(
    client: TestClient, db_session
):
    author = _register(client, "flaguploader1@example.com")
    payload = b"\x89PNG\r\n\x1a\n" + FORCE_FLAG_MARKER
    up = client.post(
        "/api/v1/blog/media",
        files={"file": ("cover.png", payload, "image/png")},
        headers=author,
    )
    assert up.status_code == 201
    media_id = up.json()["id"]

    h_admin = _register(client, "flagadmin1@example.com")
    _make_admin(db_session, "flagadmin1@example.com")

    res = client.get("/api/v1/admin/reports?target_type=blog_media", headers=h_admin)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["target_id"] == media_id
    assert items[0]["reporter"] is None
    assert items[0]["reason"] == "inappropriate"
    assert "nsfw" in items[0]["note"]


def test_listing_media_flagged_by_scan_creates_system_report(
    client: TestClient, db_session
):
    seller = _register(client, "flaguploader2@example.com")
    payload = b"\x89PNG\r\n\x1a\n" + FORCE_FLAG_MARKER
    up = client.post(
        "/api/v1/marketplace/listings/media",
        files={"file": ("preview.png", payload, "image/png")},
        headers=seller,
    )
    assert up.status_code == 201
    media_id = up.json()["id"]

    h_admin = _register(client, "flagadmin2@example.com")
    _make_admin(db_session, "flagadmin2@example.com")

    res = client.get(
        "/api/v1/admin/reports?target_type=listing_media", headers=h_admin
    )
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["target_id"] == media_id


def test_flagged_media_is_still_publicly_servable(client: TestClient, db_session):
    """Auto-flagging opens a report for review — it doesn't take content
    down or block the uploader; only an explicit moderator/DMCA action does."""
    author = _register(client, "flaguploader3@example.com")
    payload = b"\x89PNG\r\n\x1a\n" + FORCE_FLAG_MARKER
    up = client.post(
        "/api/v1/blog/media",
        files={"file": ("cover.png", payload, "image/png")},
        headers=author,
    )
    media = up.json()

    got = client.get(media["url"])
    assert got.status_code == 200
    assert got.content == payload
