"""Marketplace M3 — cart, transactional checkout, order history.

Runs fully on the Mac (no GPU). Source assets get real bytes written via
`get_storage()` so `checkout`'s asset-clone step has something to copy.
"""

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


def _grant_credits(client, headers, credits: int, db_session):
    from app.db.models import CreditPlan

    plan = CreditPlan(
        name=f"Topup{credits}",
        price_cents=0,
        credits_granted=credits,
        listing_quota=1,
        is_active=True,
        sort_order=99,
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    client.post(f"/api/v1/marketplace/plans/{plan.id}/purchase", headers=headers)


def test_cart_add_view_remove(client: TestClient, db_session):
    h_seller = _register(client, "cseller1@example.com")
    asset = _asset_for(db_session, "cseller1@example.com")
    listing = _listing(client, h_seller, asset.id)

    h_buyer = _register(client, "cbuyer1@example.com")
    add = client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    assert add.status_code == 201
    cart = add.json()
    assert cart["total_credits"] == 50
    assert len(cart["items"]) == 1

    cart_item_id = cart["items"][0]["id"]
    removed = client.delete(f"/api/v1/marketplace/cart/{cart_item_id}", headers=h_buyer)
    assert removed.status_code == 204
    assert client.get("/api/v1/marketplace/cart", headers=h_buyer).json()["items"] == []


def test_cannot_add_own_listing_to_cart(client: TestClient, db_session):
    h_seller = _register(client, "cseller2@example.com")
    asset = _asset_for(db_session, "cseller2@example.com")
    listing = _listing(client, h_seller, asset.id)

    res = client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_seller
    )
    assert res.status_code == 400


def test_cannot_add_draft_listing_to_cart(client: TestClient, db_session):
    h_seller = _register(client, "cseller3@example.com")
    asset = _asset_for(db_session, "cseller3@example.com")
    listing = _listing(client, h_seller, asset.id, status="draft")

    h_buyer = _register(client, "cbuyer3@example.com")
    res = client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    assert res.status_code == 400


def test_adding_same_listing_twice_is_idempotent(client: TestClient, db_session):
    h_seller = _register(client, "cseller4@example.com")
    asset = _asset_for(db_session, "cseller4@example.com")
    listing = _listing(client, h_seller, asset.id)

    h_buyer = _register(client, "cbuyer4@example.com")
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    second = client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    assert len(second.json()["items"]) == 1


def test_checkout_requires_sufficient_credits(client: TestClient, db_session):
    h_seller = _register(client, "cseller5@example.com")
    asset = _asset_for(db_session, "cseller5@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=999)

    h_buyer = _register(client, "cbuyer5@example.com")
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    res = client.post("/api/v1/marketplace/checkout", headers=h_buyer)
    assert res.status_code == 402


def test_checkout_empty_cart_fails(client: TestClient, db_session):
    h_buyer = _register(client, "cbuyer6@example.com")
    res = client.post("/api/v1/marketplace/checkout", headers=h_buyer)
    assert res.status_code == 402


def test_successful_checkout_moves_credits_clones_asset_and_marks_sold(
    client: TestClient, db_session
):
    h_seller = _register(client, "cseller7@example.com")
    asset = _asset_for(db_session, "cseller7@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=100)

    h_buyer = _register(client, "cbuyer7@example.com")
    _grant_credits(client, h_buyer, 200, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )

    res = client.post("/api/v1/marketplace/checkout", headers=h_buyer)
    assert res.status_code == 201
    order = res.json()
    assert order["total_credits"] == 100
    assert order["status"] == "completed"
    assert len(order["items"]) == 1
    cloned_asset_id = order["items"][0]["cloned_asset_id"]
    assert cloned_asset_id is not None

    # Buyer wallet debited.
    buyer_wallet = client.get("/api/v1/marketplace/wallet", headers=h_buyer).json()
    assert buyer_wallet["balance_credits"] == 100

    # Seller wallet credited minus the platform fee (default 10%).
    seller_wallet = client.get("/api/v1/marketplace/wallet", headers=h_seller).json()
    assert seller_wallet["balance_credits"] == 90

    # Listing (unique, stock=1) is now sold and gone from public browse.
    browse = client.get("/api/v1/marketplace/listings").json()
    assert not any(item["id"] == listing["id"] for item in browse["items"])

    # Cart was cleared.
    assert client.get("/api/v1/marketplace/cart", headers=h_buyer).json()["items"] == []

    # The clone is a real, separately-owned asset in the buyer's library.
    clone = db_session.get(Asset, cloned_asset_id)
    assert clone is not None
    assert clone.id != asset.id
    project = db_session.get(Project, clone.project_id)
    buyer = db_session.scalar(select(User).where(User.email == "cbuyer7@example.com"))
    assert project.owner_id == buyer.id
    assert get_storage().get(clone.storage_key) == b"fake video bytes"


def test_multi_stock_listing_stays_active_until_last_unit(
    client: TestClient, db_session
):
    h_seller = _register(client, "cseller8@example.com")
    asset = _asset_for(db_session, "cseller8@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=10, stock=2)

    h_buyer1 = _register(client, "cbuyer8a@example.com")
    _grant_credits(client, h_buyer1, 50, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer1
    )
    client.post("/api/v1/marketplace/checkout", headers=h_buyer1)

    browse = client.get("/api/v1/marketplace/listings").json()
    match = next(item for item in browse["items"] if item["id"] == listing["id"])
    assert match["status"] == "active"
    assert match["stock"] == 1

    h_buyer2 = _register(client, "cbuyer8b@example.com")
    _grant_credits(client, h_buyer2, 50, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer2
    )
    client.post("/api/v1/marketplace/checkout", headers=h_buyer2)

    browse2 = client.get("/api/v1/marketplace/listings").json()
    assert not any(item["id"] == listing["id"] for item in browse2["items"])


def test_checkout_fails_cleanly_if_listing_delisted_after_adding_to_cart(
    client: TestClient, db_session
):
    h_seller = _register(client, "cseller9@example.com")
    asset = _asset_for(db_session, "cseller9@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=10)

    h_buyer = _register(client, "cbuyer9@example.com")
    _grant_credits(client, h_buyer, 50, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )

    client.patch(
        f"/api/v1/marketplace/listings/{listing['id']}",
        json={"status": "delisted"},
        headers=h_seller,
    )

    res = client.post("/api/v1/marketplace/checkout", headers=h_buyer)
    assert res.status_code == 402

    # Buyer wasn't charged.
    wallet = client.get("/api/v1/marketplace/wallet", headers=h_buyer).json()
    assert wallet["balance_credits"] == 50


def test_order_and_sales_history(client: TestClient, db_session):
    h_seller = _register(client, "cseller10@example.com")
    asset = _asset_for(db_session, "cseller10@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=30)

    h_buyer = _register(client, "cbuyer10@example.com")
    _grant_credits(client, h_buyer, 50, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    client.post("/api/v1/marketplace/checkout", headers=h_buyer)

    orders = client.get("/api/v1/marketplace/orders", headers=h_buyer).json()
    assert len(orders) == 1
    assert orders[0]["total_credits"] == 30

    sales = client.get("/api/v1/marketplace/orders/sales", headers=h_seller).json()
    assert len(sales) == 1
    assert sales[0]["price_credits"] == 30
    assert sales[0]["title"] == "Neon City Loop"
