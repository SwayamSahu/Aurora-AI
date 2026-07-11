"""Marketplace admin console extension — full listing edit/delete for any
seller, and listing-comment hide/edit/delete. Runs fully on the Mac (no GPU)."""

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


def _listing(client, headers, asset_id, **overrides):
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


# --------------------------------- listing CRUD ------------------------------ #
def test_admin_can_edit_any_listing(client: TestClient, db_session):
    h_seller = _register(client, "mseller1@example.com")
    asset = _asset_for(db_session, "mseller1@example.com")
    listing = _listing(client, h_seller, asset.id)

    h_admin = _register(client, "madmin1@example.com")
    _make_admin(db_session, "madmin1@example.com")

    res = client.patch(
        f"/api/v1/marketplace/listings/{listing['id']}",
        json={"title": "Edited by admin", "price_credits": 999},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Edited by admin"
    assert res.json()["price_credits"] == 999


def test_admin_can_delete_any_draft_listing(client: TestClient, db_session):
    h_seller = _register(client, "mseller2@example.com")
    asset = _asset_for(db_session, "mseller2@example.com")
    listing = _listing(client, h_seller, asset.id, status="draft")

    h_admin = _register(client, "madmin2@example.com")
    _make_admin(db_session, "madmin2@example.com")

    res = client.delete(
        f"/api/v1/marketplace/listings/{listing['id']}", headers=h_admin
    )
    assert res.status_code == 204


def test_admin_can_view_any_non_active_listing(client: TestClient, db_session):
    """Admin can GET a draft/delisted listing's detail — not just seller or
    buyer — matching blog's equivalent draft-visibility bypass."""
    h_seller = _register(client, "mseller9@example.com")
    asset = _asset_for(db_session, "mseller9@example.com")
    listing = _listing(client, h_seller, asset.id, status="draft")

    h_admin = _register(client, "madmin7@example.com")
    _make_admin(db_session, "madmin7@example.com")

    res = client.get(f"/api/v1/marketplace/listings/{listing['id']}", headers=h_admin)
    assert res.status_code == 200


def test_non_owner_still_gets_404_not_403(client: TestClient, db_session):
    """Preserves the original M2 contract: a non-owner, non-admin can't
    tell a listing exists — 404, not a confirming 403."""
    h_seller = _register(client, "mseller3@example.com")
    asset = _asset_for(db_session, "mseller3@example.com")
    listing = _listing(client, h_seller, asset.id)

    h_other = _register(client, "mintruder3@example.com")
    res = client.patch(
        f"/api/v1/marketplace/listings/{listing['id']}",
        json={"price_credits": 1},
        headers=h_other,
    )
    assert res.status_code == 404


def test_admin_edit_does_not_trip_sellers_quota(client: TestClient, db_session):
    """Admin editing a listing to active shouldn't be blocked by the
    listing's actual seller's (possibly zero) quota."""
    h_seller = _register(client, "mseller4@example.com")
    asset1 = _asset_for(db_session, "mseller4@example.com")
    asset2 = _asset_for(db_session, "mseller4@example.com")
    _listing(client, h_seller, asset1.id)  # uses up the free quota slot (1)
    draft = _listing(client, h_seller, asset2.id, status="draft")

    h_admin = _register(client, "madmin3@example.com")
    _make_admin(db_session, "madmin3@example.com")

    res = client.patch(
        f"/api/v1/marketplace/listings/{draft['id']}",
        json={"status": "active"},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "active"


# -------------------------------- comments ----------------------------------- #
def test_admin_can_delete_any_listing_comment(client: TestClient, db_session):
    h_seller = _register(client, "mseller5@example.com")
    asset = _asset_for(db_session, "mseller5@example.com")
    listing = _listing(client, h_seller, asset.id)
    h_commenter = _register(client, "mcommenter5@example.com")
    comment = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/comments",
        json={"body": "love it"},
        headers=h_commenter,
    ).json()

    h_admin = _register(client, "madmin4@example.com")
    _make_admin(db_session, "madmin4@example.com")

    res = client.delete(
        f"/api/v1/marketplace/comments/{comment['id']}", headers=h_admin
    )
    assert res.status_code == 204


def test_admin_can_hide_and_unhide_listing_comment(client: TestClient, db_session):
    h_seller = _register(client, "mseller6@example.com")
    asset = _asset_for(db_session, "mseller6@example.com")
    listing = _listing(client, h_seller, asset.id)
    h_commenter = _register(client, "mcommenter6@example.com")
    comment = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/comments",
        json={"body": "spammy content"},
        headers=h_commenter,
    ).json()

    h_admin = _register(client, "madmin5@example.com")
    _make_admin(db_session, "madmin5@example.com")

    hidden = client.patch(
        f"/api/v1/admin/marketplace/comments/{comment['id']}",
        json={"is_hidden": True},
        headers=h_admin,
    )
    assert hidden.status_code == 200
    assert hidden.json()["is_hidden"] is True

    public_comments = client.get(
        f"/api/v1/marketplace/listings/{listing['id']}/comments"
    ).json()
    assert not any(c["id"] == comment["id"] for c in public_comments)
    listing_after = client.get(
        f"/api/v1/marketplace/listings/{listing['id']}", headers=h_seller
    ).json()
    assert listing_after["comment_count"] == 0

    admin_comments = client.get(
        f"/api/v1/admin/marketplace/listings/{listing['id']}/comments", headers=h_admin
    ).json()
    assert any(c["id"] == comment["id"] and c["is_hidden"] for c in admin_comments)

    unhidden = client.patch(
        f"/api/v1/admin/marketplace/comments/{comment['id']}",
        json={"is_hidden": False},
        headers=h_admin,
    )
    assert unhidden.json()["is_hidden"] is False
    listing_restored = client.get(
        f"/api/v1/marketplace/listings/{listing['id']}", headers=h_seller
    ).json()
    assert listing_restored["comment_count"] == 1


def test_admin_can_edit_listing_comment_body(client: TestClient, db_session):
    h_seller = _register(client, "mseller7@example.com")
    asset = _asset_for(db_session, "mseller7@example.com")
    listing = _listing(client, h_seller, asset.id)
    h_commenter = _register(client, "mcommenter7@example.com")
    comment = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/comments",
        json={"body": "original"},
        headers=h_commenter,
    ).json()

    h_admin = _register(client, "madmin6@example.com")
    _make_admin(db_session, "madmin6@example.com")

    res = client.patch(
        f"/api/v1/admin/marketplace/comments/{comment['id']}",
        json={"body": "[redacted]"},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["body"] == "[redacted]"


def test_non_admin_gets_403_on_comment_moderation_routes(
    client: TestClient, db_session
):
    h_seller = _register(client, "mseller8@example.com")
    asset = _asset_for(db_session, "mseller8@example.com")
    listing = _listing(client, h_seller, asset.id)

    h_regular = _register(client, "mregular8@example.com")
    assert (
        client.get(
            f"/api/v1/admin/marketplace/listings/{listing['id']}/comments",
            headers=h_regular,
        ).status_code
        == 403
    )
