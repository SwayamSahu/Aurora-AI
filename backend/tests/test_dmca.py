"""Admin Phase 4: DMCA takedown notices — public submission (no account
needed) and moderator triage. Runs fully on the Mac (no GPU)."""

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


def _create_post(client, headers, **overrides):
    payload = {
        "title": "Copyrighted Clip",
        "category": "tutorials",
        "body_html": "<p>Body.</p>",
        "status": "published",
        **overrides,
    }
    return client.post("/api/v1/blog/posts", json=payload, headers=headers).json()


def _dmca_payload(**overrides):
    return {
        "claimant_name": "Jane Rightsholder",
        "claimant_email": "jane@example.com",
        "target_type": "blog_post",
        "target_id": "placeholder",
        "work_description": "My original short film, published 2024.",
        "good_faith_statement": True,
        "signature": "Jane Rightsholder",
        **overrides,
    }


def test_anyone_can_submit_a_dmca_notice_without_an_account(
    client: TestClient, db_session
):
    author = _register(client, "dcmaauthor1@example.com")
    post = _create_post(client, author)

    res = client.post(
        "/api/v1/dmca", json=_dmca_payload(target_id=post["id"])
    )
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "open"
    assert body["target_preview"]["title"] == "Copyrighted Clip"


def test_dmca_requires_good_faith_statement(client: TestClient, db_session):
    author = _register(client, "dcmaauthor2@example.com")
    post = _create_post(client, author)
    res = client.post(
        "/api/v1/dmca",
        json=_dmca_payload(target_id=post["id"], good_faith_statement=False),
    )
    assert res.status_code == 422


def test_dmca_rejects_missing_target(client: TestClient, db_session):
    res = client.post(
        "/api/v1/dmca", json=_dmca_payload(target_id="does-not-exist")
    )
    assert res.status_code == 404


def test_moderator_can_list_and_reject_dmca_request(client: TestClient, db_session):
    author = _register(client, "dcmaauthor3@example.com")
    post = _create_post(client, author)
    submitted = client.post(
        "/api/v1/dmca", json=_dmca_payload(target_id=post["id"])
    ).json()

    h_admin = _register(client, "dcmaadmin1@example.com")
    _make_admin(db_session, "dcmaadmin1@example.com")

    res = client.get("/api/v1/admin/dmca?status=open", headers=h_admin)
    assert res.status_code == 200
    assert any(r["id"] == submitted["id"] for r in res.json()["items"])

    resolved = client.patch(
        f"/api/v1/admin/dmca/{submitted['id']}",
        json={"status": "rejected", "resolution_note": "No valid claim shown."},
        headers=h_admin,
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "rejected"
    assert resolved.json()["resolved_by"]["email"] == "dcmaadmin1@example.com"

    # The post is untouched by a rejection.
    still_up = client.get(f"/api/v1/blog/posts/{post['slug']}")
    assert still_up.status_code == 200
    assert still_up.json()["status"] == "published"


def test_content_removed_takes_the_post_down(client: TestClient, db_session):
    author = _register(client, "dcmaauthor4@example.com")
    post = _create_post(client, author)
    submitted = client.post(
        "/api/v1/dmca", json=_dmca_payload(target_id=post["id"])
    ).json()

    h_admin = _register(client, "dcmaadmin2@example.com")
    _make_admin(db_session, "dcmaadmin2@example.com")

    resolved = client.patch(
        f"/api/v1/admin/dmca/{submitted['id']}",
        json={"status": "content_removed"},
        headers=h_admin,
    )
    assert resolved.status_code == 200

    # Unpublished (draft), not hard-deleted — the author can still see it
    # via the author-scoped route, but it 404s publicly.
    now_hidden = client.get(f"/api/v1/blog/posts/{post['slug']}")
    assert now_hidden.status_code == 404

    as_author = client.get(f"/api/v1/blog/posts/{post['slug']}", headers=author)
    assert as_author.status_code == 200
    assert as_author.json()["status"] == "draft"


def test_content_removed_delists_a_listing(client: TestClient, db_session):
    from app.db.models import Asset, AssetKind, AssetSource, Project
    from app.storage import get_storage

    seller = _register(client, "dcmaseller1@example.com")
    seller_user = db_session.scalar(
        select(User).where(User.email == "dcmaseller1@example.com")
    )
    project = Project(owner_id=seller_user.id, name="proj")
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

    listing = client.post(
        "/api/v1/marketplace/listings",
        json={
            "title": "Infringing Clip",
            "category": "sci-fi",
            "price_credits": 20,
            "source_asset_id": asset.id,
            "status": "active",
        },
        headers=seller,
    ).json()

    submitted = client.post(
        "/api/v1/dmca", json=_dmca_payload(target_type="listing", target_id=listing["id"])
    ).json()

    h_admin = _register(client, "dcmaadmin3@example.com")
    _make_admin(db_session, "dcmaadmin3@example.com")
    client.patch(
        f"/api/v1/admin/dmca/{submitted['id']}",
        json={"status": "content_removed"},
        headers=h_admin,
    )

    updated = client.get(
        f"/api/v1/marketplace/listings/{listing['id']}", headers=seller
    ).json()
    assert updated["status"] == "delisted"


def test_dmca_resolution_is_audited(client: TestClient, db_session):
    author = _register(client, "dcmaauthor5@example.com")
    post = _create_post(client, author)
    submitted = client.post(
        "/api/v1/dmca", json=_dmca_payload(target_id=post["id"])
    ).json()

    h_admin = _register(client, "dcmaadmin4@example.com")
    _make_admin(db_session, "dcmaadmin4@example.com")
    client.patch(
        f"/api/v1/admin/dmca/{submitted['id']}",
        json={"status": "content_removed"},
        headers=h_admin,
    )

    res = client.get(
        "/api/v1/admin/audit?target_type=dmca_request", headers=h_admin
    )
    entry = next(a for a in res.json()["items"] if a["target_id"] == submitted["id"])
    assert entry["action"] == "dmca.content_removed"


def test_non_moderator_gets_403_on_admin_dmca(client: TestClient, db_session):
    h_user = _register(client, "dcmauser1@example.com")
    res = client.get("/api/v1/admin/dmca", headers=h_user)
    assert res.status_code == 403
