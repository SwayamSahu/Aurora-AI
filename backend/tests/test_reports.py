"""Admin Phase 3: content reporting/flagging — any user can flag a blog
post/comment or marketplace listing/comment, and moderators triage the
queue. Runs fully on the Mac (no GPU, no Stripe)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Asset, AssetKind, AssetSource, Project, User
from app.storage import get_storage


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
        "title": "My First Post",
        "category": "tutorials",
        "body_html": "<h2>Hello</h2><p>World body text here.</p>",
        "status": "published",
        **overrides,
    }
    return client.post("/api/v1/blog/posts", json=payload, headers=headers).json()


def _asset_for(db_session, email: str) -> Asset:
    user = db_session.scalar(select(User).where(User.email == email))
    project = Project(owner_id=user.id, name="Seller project")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    key = f"projects/{project.id}/seed-clip.mp4"
    get_storage().put(key, b"fake video bytes", "video/mp4")

    asset = Asset(
        project_id=project.id,
        name="clip.mp4",
        kind=AssetKind.VIDEO,
        source=AssetSource.GENERATED,
        storage_key=key,
        content_type="video/mp4",
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def _create_listing(client, headers, asset_id, **overrides):
    payload = {
        "title": "Neon City Loop",
        "category": "sci-fi",
        "price_credits": 50,
        "source_asset_id": asset_id,
        "status": "active",
        **overrides,
    }
    return client.post(
        "/api/v1/marketplace/listings", json=payload, headers=headers
    ).json()


# ------------------------------- creating reports ----------------------------- #
def test_user_can_report_a_blog_post(client: TestClient, db_session):
    h_author = _register(client, "rauthor1@example.com")
    post = _create_post(client, h_author)

    h_reporter = _register(client, "rreporter1@example.com")
    res = client.post(
        "/api/v1/reports",
        json={"target_type": "blog_post", "target_id": post["id"], "reason": "spam"},
        headers=h_reporter,
    )
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "open"
    assert body["target_preview"]["title"] == "My First Post"
    assert body["reporter"]["email"] == "rreporter1@example.com"


def test_user_can_report_a_listing(client: TestClient, db_session):
    h_seller = _register(client, "rseller1@example.com")
    asset = _asset_for(db_session, "rseller1@example.com")
    listing = _create_listing(client, h_seller, asset.id)

    h_reporter = _register(client, "rreporter2@example.com")
    res = client.post(
        "/api/v1/reports",
        json={
            "target_type": "listing",
            "target_id": listing["id"],
            "reason": "inappropriate",
            "note": "Not what it claims to be.",
        },
        headers=h_reporter,
    )
    assert res.status_code == 201
    assert res.json()["target_preview"]["title"] == "Neon City Loop"


def test_report_rejects_unknown_target(client: TestClient, db_session):
    h_reporter = _register(client, "rreporter3@example.com")
    res = client.post(
        "/api/v1/reports",
        json={"target_type": "blog_post", "target_id": "does-not-exist", "reason": "spam"},
        headers=h_reporter,
    )
    assert res.status_code == 404


def test_report_rejects_invalid_reason(client: TestClient, db_session):
    h_author = _register(client, "rauthor2@example.com")
    post = _create_post(client, h_author)
    h_reporter = _register(client, "rreporter4@example.com")
    res = client.post(
        "/api/v1/reports",
        json={"target_type": "blog_post", "target_id": post["id"], "reason": "not-a-reason"},
        headers=h_reporter,
    )
    assert res.status_code == 422


def test_duplicate_open_report_is_rejected(client: TestClient, db_session):
    h_author = _register(client, "rauthor3@example.com")
    post = _create_post(client, h_author)
    h_reporter = _register(client, "rreporter5@example.com")

    payload = {"target_type": "blog_post", "target_id": post["id"], "reason": "spam"}
    first = client.post("/api/v1/reports", json=payload, headers=h_reporter)
    assert first.status_code == 201
    second = client.post("/api/v1/reports", json=payload, headers=h_reporter)
    assert second.status_code == 409


def test_report_requires_auth(client: TestClient, db_session):
    res = client.post(
        "/api/v1/reports",
        json={"target_type": "blog_post", "target_id": "whatever", "reason": "spam"},
    )
    assert res.status_code == 401


# --------------------------------- admin triage -------------------------------- #
def test_moderator_can_list_and_resolve_reports(client: TestClient, db_session):
    h_author = _register(client, "rauthor4@example.com")
    post = _create_post(client, h_author)
    h_reporter = _register(client, "rreporter6@example.com")
    report = client.post(
        "/api/v1/reports",
        json={"target_type": "blog_post", "target_id": post["id"], "reason": "spam"},
        headers=h_reporter,
    ).json()

    h_mod = _register(client, "rmod1@example.com")
    mod = db_session.scalar(select(User).where(User.email == "rmod1@example.com"))
    from app.db.models import UserRole

    mod.role = UserRole.MODERATOR
    db_session.commit()

    res = client.get("/api/v1/admin/reports?status=open", headers=h_mod)
    assert res.status_code == 200
    assert any(r["id"] == report["id"] for r in res.json()["items"])

    resolved = client.patch(
        f"/api/v1/admin/reports/{report['id']}",
        json={"status": "resolved", "resolution_note": "Removed the post."},
        headers=h_mod,
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolution_note"] == "Removed the post."

    # No longer shows under the open filter.
    still_open = client.get("/api/v1/admin/reports?status=open", headers=h_mod)
    assert not any(r["id"] == report["id"] for r in still_open.json()["items"])


def test_resolving_a_report_is_audited(client: TestClient, db_session):
    h_author = _register(client, "rauthor5@example.com")
    post = _create_post(client, h_author)
    h_reporter = _register(client, "rreporter7@example.com")
    report = client.post(
        "/api/v1/reports",
        json={"target_type": "blog_post", "target_id": post["id"], "reason": "abuse"},
        headers=h_reporter,
    ).json()

    h_admin = _register(client, "radmin1@example.com")
    _make_admin(db_session, "radmin1@example.com")
    client.patch(
        f"/api/v1/admin/reports/{report['id']}",
        json={"status": "dismissed"},
        headers=h_admin,
    )

    res = client.get("/api/v1/admin/audit?target_type=report", headers=h_admin)
    entry = next(a for a in res.json()["items"] if a["target_id"] == report["id"])
    assert entry["action"] == "report.dismissed"


def test_non_moderator_gets_403_on_admin_reports(client: TestClient, db_session):
    h_user = _register(client, "ruser1@example.com")
    res = client.get("/api/v1/admin/reports", headers=h_user)
    assert res.status_code == 403


def test_report_on_deleted_target_shows_no_preview(client: TestClient, db_session):
    h_author = _register(client, "rauthor6@example.com")
    post = _create_post(client, h_author)
    h_reporter = _register(client, "rreporter8@example.com")
    report = client.post(
        "/api/v1/reports",
        json={"target_type": "blog_post", "target_id": post["id"], "reason": "spam"},
        headers=h_reporter,
    ).json()

    h_admin = _register(client, "radmin2@example.com")
    _make_admin(db_session, "radmin2@example.com")
    client.delete(f"/api/v1/blog/posts/{post['id']}", headers=h_author)

    res = client.get("/api/v1/admin/reports", headers=h_admin)
    entry = next(r for r in res.json()["items"] if r["id"] == report["id"])
    assert entry["target_preview"] is None
