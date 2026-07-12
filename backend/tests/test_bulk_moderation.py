"""Admin Phase 3: bulk moderation — deleting/hiding many posts, comments,
or listings in one call. Runs fully on the Mac (no GPU, no Stripe)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Asset, AssetKind, AssetSource, CreditPlan, Project, User
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
        "title": "Bulk Test Post",
        "category": "tutorials",
        "body_html": "<p>Body text here.</p>",
        "status": "published",
        **overrides,
    }
    return client.post("/api/v1/blog/posts", json=payload, headers=headers).json()


def _asset_for(client, db_session, email: str) -> Asset:
    user = db_session.scalar(select(User).where(User.email == email))
    project = Project(owner_id=user.id, name="Seller project")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    key = f"projects/{project.id}/seed-clip-{project.id}.mp4"
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


def _grant_quota(client, headers, quota: int, db_session):
    plan = CreditPlan(
        name=f"Quota{quota}",
        price_cents=0,
        credits_granted=0,
        listing_quota=quota,
        is_active=True,
        sort_order=99,
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    client.post(f"/api/v1/marketplace/plans/{plan.id}/purchase", headers=headers)


def _create_listing(client, headers, asset_id, **overrides):
    payload = {
        "title": "Bulk Listing",
        "category": "sci-fi",
        "price_credits": 20,
        "source_asset_id": asset_id,
        "status": "active",
        **overrides,
    }
    return client.post(
        "/api/v1/marketplace/listings", json=payload, headers=headers
    ).json()


# --------------------------------- blog bulk actions --------------------------------- #
def test_bulk_delete_posts(client: TestClient, db_session):
    h_author = _register(client, "bulkauthor1@example.com")
    post1 = _create_post(client, h_author, title="Post One")
    post2 = _create_post(client, h_author, title="Post Two")

    h_admin = _register(client, "bulkadmin1@example.com")
    _make_admin(db_session, "bulkadmin1@example.com")

    res = client.post(
        "/api/v1/admin/blog/posts/bulk-delete",
        json={"ids": [post1["id"], post2["id"], "missing-id"]},
        headers=h_admin,
    )
    assert res.status_code == 200
    body = res.json()
    assert set(body["succeeded"]) == {post1["id"], post2["id"]}
    assert body["failed"] == ["missing-id"]

    assert client.get(f"/api/v1/blog/posts/{post1['slug']}").status_code == 404


def test_bulk_delete_posts_is_audited(client: TestClient, db_session):
    h_author = _register(client, "bulkauthor2@example.com")
    post = _create_post(client, h_author)

    h_admin = _register(client, "bulkadmin2@example.com")
    _make_admin(db_session, "bulkadmin2@example.com")

    client.post(
        "/api/v1/admin/blog/posts/bulk-delete",
        json={"ids": [post["id"]]},
        headers=h_admin,
    )
    res = client.get(
        "/api/v1/admin/audit?target_type=blog_post&action=post.bulk_delete",
        headers=h_admin,
    )
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["action_metadata"]["ids"] == [post["id"]]


def test_bulk_hide_blog_comments(client: TestClient, db_session):
    h_author = _register(client, "bulkauthor3@example.com")
    post = _create_post(client, h_author)
    h_commenter = _register(client, "bulkcommenter1@example.com")

    c1 = client.post(
        f"/api/v1/blog/posts/{post['id']}/comments",
        json={"body": "spam one"},
        headers=h_commenter,
    ).json()
    c2 = client.post(
        f"/api/v1/blog/posts/{post['id']}/comments",
        json={"body": "spam two"},
        headers=h_commenter,
    ).json()

    h_admin = _register(client, "bulkadmin3@example.com")
    _make_admin(db_session, "bulkadmin3@example.com")

    res = client.post(
        "/api/v1/admin/blog/comments/bulk-hide",
        json={"ids": [c1["id"], c2["id"]]},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert set(res.json()["succeeded"]) == {c1["id"], c2["id"]}

    public_comments = client.get(f"/api/v1/blog/posts/{post['slug']}/comments").json()
    assert not any(c["id"] in (c1["id"], c2["id"]) for c in public_comments)


def test_bulk_endpoints_require_moderator(client: TestClient, db_session):
    h_user = _register(client, "bulkuser1@example.com")
    res = client.post(
        "/api/v1/admin/blog/posts/bulk-delete",
        json={"ids": ["whatever"]},
        headers=h_user,
    )
    assert res.status_code == 403


# --------------------------------- marketplace bulk actions --------------------------------- #
def test_bulk_delist_listings(client: TestClient, db_session):
    h_seller = _register(client, "bulkseller1@example.com")
    _grant_quota(client, h_seller, 2, db_session)
    asset1 = _asset_for(client, db_session, "bulkseller1@example.com")
    asset2 = _asset_for(client, db_session, "bulkseller1@example.com")
    listing1 = _create_listing(client, h_seller, asset1.id)
    listing2 = _create_listing(client, h_seller, asset2.id)

    h_admin = _register(client, "bulkadmin4@example.com")
    _make_admin(db_session, "bulkadmin4@example.com")

    res = client.post(
        "/api/v1/admin/marketplace/listings/bulk-delist",
        json={"ids": [listing1["id"], listing2["id"]]},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert set(res.json()["succeeded"]) == {listing1["id"], listing2["id"]}

    listing = client.get(
        f"/api/v1/marketplace/listings/{listing1['id']}", headers=h_seller
    ).json()
    assert listing["status"] == "delisted"


def test_bulk_hide_listing_comments(client: TestClient, db_session):
    h_seller = _register(client, "bulkseller2@example.com")
    asset = _asset_for(client, db_session, "bulkseller2@example.com")
    listing = _create_listing(client, h_seller, asset.id)
    h_commenter = _register(client, "bulkcommenter2@example.com")

    c1 = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/comments",
        json={"body": "spam comment"},
        headers=h_commenter,
    ).json()

    h_admin = _register(client, "bulkadmin5@example.com")
    _make_admin(db_session, "bulkadmin5@example.com")

    res = client.post(
        "/api/v1/admin/marketplace/comments/bulk-hide",
        json={"ids": [c1["id"]]},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["succeeded"] == [c1["id"]]


def test_bulk_ids_request_requires_at_least_one_id(client: TestClient, db_session):
    h_admin = _register(client, "bulkadmin6@example.com")
    _make_admin(db_session, "bulkadmin6@example.com")
    res = client.post(
        "/api/v1/admin/blog/posts/bulk-delete", json={"ids": []}, headers=h_admin
    )
    assert res.status_code == 422
