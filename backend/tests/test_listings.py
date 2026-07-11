"""Marketplace M2 — listing browse/search, owner CRUD, quota enforcement.

Runs fully on the Mac (no GPU). Source assets are created directly via
`db_session` (mirroring the `sample_project` fixture pattern) rather than
through the real upload pipeline, since only asset *metadata* matters here.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Asset, AssetKind, AssetSource, CreditPlan, Project, User


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


def _asset_for(db_session, email: str) -> Asset:
    user = db_session.scalar(select(User).where(User.email == email))
    project = Project(owner_id=user.id, name="Seller project")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    asset = Asset(
        project_id=project.id,
        name="clip.mp4",
        kind=AssetKind.VIDEO,
        source=AssetSource.GENERATED,
        storage_key="fake/clip.mp4",
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
    return client.post("/api/v1/marketplace/listings", json=payload, headers=headers)


def test_create_listing_requires_owned_asset(client: TestClient, db_session):
    _register(client, "seller1@example.com")
    other_asset = _asset_for(db_session, "seller1@example.com")
    h_notowner = _register(client, "notowner@example.com")

    res = _create_listing(client, h_notowner, other_asset.id)
    assert res.status_code == 404


def test_create_active_listing_appears_in_public_browse(client: TestClient, db_session):
    h = _register(client, "seller2@example.com")
    asset = _asset_for(db_session, "seller2@example.com")
    res = _create_listing(client, h, asset.id)
    assert res.status_code == 201
    listing = res.json()
    assert listing["status"] == "active"
    assert listing["seller"]["full_name"] == "seller2"

    browse = client.get("/api/v1/marketplace/listings").json()
    assert any(item["id"] == listing["id"] for item in browse["items"])


def test_draft_listing_hidden_from_public_but_visible_to_owner(
    client: TestClient, db_session
):
    h = _register(client, "seller3@example.com")
    asset = _asset_for(db_session, "seller3@example.com")
    res = _create_listing(client, h, asset.id, status="draft")
    listing_id = res.json()["id"]

    browse = client.get("/api/v1/marketplace/listings").json()
    assert not any(item["id"] == listing_id for item in browse["items"])

    assert client.get(f"/api/v1/marketplace/listings/{listing_id}").status_code == 404
    assert (
        client.get(f"/api/v1/marketplace/listings/{listing_id}", headers=h).status_code
        == 200
    )


def test_free_quota_blocks_second_active_listing(client: TestClient, db_session):
    h = _register(client, "seller4@example.com")
    a1 = _asset_for(db_session, "seller4@example.com")
    a2 = _asset_for(db_session, "seller4@example.com")

    first = _create_listing(client, h, a1.id)
    assert first.status_code == 201

    second = _create_listing(client, h, a2.id, title="Second Piece")
    assert second.status_code == 402
    assert "quota" in second.json()["detail"].lower()


def test_buying_a_plan_raises_quota_and_unblocks_listing(
    client: TestClient, db_session
):
    h = _register(client, "seller5@example.com")
    a1 = _asset_for(db_session, "seller5@example.com")
    a2 = _asset_for(db_session, "seller5@example.com")
    _create_listing(client, h, a1.id)

    plan = CreditPlan(
        name="Creator",
        price_cents=999,
        credits_granted=0,
        listing_quota=10,
        is_active=True,
        sort_order=1,
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    client.post(f"/api/v1/marketplace/plans/{plan.id}/purchase", headers=h)

    second = _create_listing(client, h, a2.id, title="Second Piece")
    assert second.status_code == 201


def test_delisting_frees_a_quota_slot(client: TestClient, db_session):
    h = _register(client, "seller6@example.com")
    a1 = _asset_for(db_session, "seller6@example.com")
    a2 = _asset_for(db_session, "seller6@example.com")
    first = _create_listing(client, h, a1.id).json()

    client.patch(
        f"/api/v1/marketplace/listings/{first['id']}",
        json={"status": "delisted"},
        headers=h,
    )
    second = _create_listing(client, h, a2.id, title="Second Piece")
    assert second.status_code == 201


def test_owner_can_update_and_delete_draft_listing(client: TestClient, db_session):
    h = _register(client, "seller7@example.com")
    asset = _asset_for(db_session, "seller7@example.com")
    listing = _create_listing(client, h, asset.id, status="draft").json()

    upd = client.patch(
        f"/api/v1/marketplace/listings/{listing['id']}",
        json={"price_credits": 75},
        headers=h,
    )
    assert upd.status_code == 200
    assert upd.json()["price_credits"] == 75

    delete = client.delete(f"/api/v1/marketplace/listings/{listing['id']}", headers=h)
    assert delete.status_code == 204


def test_non_owner_cannot_update_or_delete(client: TestClient, db_session):
    h = _register(client, "seller8@example.com")
    asset = _asset_for(db_session, "seller8@example.com")
    listing = _create_listing(client, h, asset.id).json()

    h_other = _register(client, "intruder@example.com")
    assert (
        client.patch(
            f"/api/v1/marketplace/listings/{listing['id']}",
            json={"price_credits": 1},
            headers=h_other,
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/v1/marketplace/listings/{listing['id']}", headers=h_other
        ).status_code
        == 404
    )


def test_cannot_manually_set_status_sold(client: TestClient, db_session):
    """`sold` isn't in ListingUpdate's allowed status literal, so this is
    rejected at the schema layer (422) before it ever reaches the service's
    own defense-in-depth check."""
    h = _register(client, "seller9@example.com")
    asset = _asset_for(db_session, "seller9@example.com")
    listing = _create_listing(client, h, asset.id).json()
    res = client.patch(
        f"/api/v1/marketplace/listings/{listing['id']}",
        json={"status": "sold"},
        headers=h,
    )
    assert res.status_code == 422


def test_category_counts_only_include_active(client: TestClient, db_session):
    h = _register(client, "seller10@example.com")
    a1 = _asset_for(db_session, "seller10@example.com")
    a2 = _asset_for(db_session, "seller10@example.com")
    _create_listing(client, h, a1.id, category="anime")
    _create_listing(client, h, a2.id, category="anime", status="draft")

    counts = client.get("/api/v1/marketplace/listings/categories").json()
    assert counts.get("anime") == 1


def test_my_assets_lists_across_projects(client: TestClient, db_session):
    h = _register(client, "seller11@example.com")
    _asset_for(db_session, "seller11@example.com")
    _asset_for(db_session, "seller11@example.com")
    res = client.get("/api/v1/marketplace/me/assets", headers=h)
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_admin_bypasses_listing_quota(client: TestClient, db_session):
    h = _register(client, "admin1@example.com")
    user = db_session.scalar(select(User).where(User.email == "admin1@example.com"))
    user.is_superuser = True
    db_session.commit()

    a1 = _asset_for(db_session, "admin1@example.com")
    a2 = _asset_for(db_session, "admin1@example.com")
    assert _create_listing(client, h, a1.id).status_code == 201
    assert _create_listing(client, h, a2.id, title="Second").status_code == 201
