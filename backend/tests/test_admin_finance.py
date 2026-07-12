"""Admin Phase 2: runtime-editable platform fee, item-level partial
refunds, global ledger search, and the revenue analytics summary. Runs
fully on the Mac (no GPU, no Stripe)."""

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


# ------------------------------- platform fee -------------------------------- #
def test_admin_can_read_and_update_platform_fee(client: TestClient, db_session):
    h_admin = _register(client, "feeadmin1@example.com")
    _make_admin(db_session, "feeadmin1@example.com")

    res = client.get("/api/v1/admin/marketplace/settings/fee", headers=h_admin)
    assert res.status_code == 200
    assert res.json()["platform_fee"] == 0.10

    res = client.patch(
        "/api/v1/admin/marketplace/settings/fee",
        json={"platform_fee": 0.2},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["platform_fee"] == 0.2

    res = client.get("/api/v1/admin/marketplace/settings/fee", headers=h_admin)
    assert res.json()["platform_fee"] == 0.2


def test_platform_fee_rejects_out_of_range_values(client: TestClient, db_session):
    h_admin = _register(client, "feeadmin2@example.com")
    _make_admin(db_session, "feeadmin2@example.com")

    res = client.patch(
        "/api/v1/admin/marketplace/settings/fee",
        json={"platform_fee": 1.5},
        headers=h_admin,
    )
    assert res.status_code == 422


def test_fee_change_only_affects_future_sales(client: TestClient, db_session):
    h_seller = _register(client, "feeseller1@example.com")
    asset = _asset_for(db_session, "feeseller1@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=100)

    h_buyer = _register(client, "feebuyer1@example.com")
    _grant_credits(client, h_buyer, 500, db_session)
    h_admin = _register(client, "feeadmin3@example.com")
    _make_admin(db_session, "feeadmin3@example.com")

    # First sale at the default 10% fee.
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    order1 = client.post("/api/v1/marketplace/checkout", headers=h_buyer).json()

    # Bump the fee to 50%, then sell again (seller creates a second listing).
    client.patch(
        "/api/v1/admin/marketplace/settings/fee",
        json={"platform_fee": 0.5},
        headers=h_admin,
    )
    asset2 = _asset_for(db_session, "feeseller1@example.com")
    listing2 = _listing(client, h_seller, asset2.id, price_credits=100)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing2["id"]}, headers=h_buyer
    )
    order2 = client.post("/api/v1/marketplace/checkout", headers=h_buyer).json()

    # Seller earned 90 from the first sale (10% fee) and 50 from the second
    # (50% fee) — the rate change never touched the already-completed sale.
    assert (
        client.get("/api/v1/marketplace/wallet", headers=h_seller).json()[
            "balance_credits"
        ]
        == 140
    )
    assert order1["items"][0]["price_credits"] == 100
    assert order2["items"][0]["price_credits"] == 100


def test_non_admin_gets_403_on_platform_fee(client: TestClient, db_session):
    h_user = _register(client, "feeuser1@example.com")
    res = client.get("/api/v1/admin/marketplace/settings/fee", headers=h_user)
    assert res.status_code == 403


# ------------------------------- partial refunds ------------------------------ #
def test_admin_can_partially_refund_specific_items(client: TestClient, db_session):
    h_seller = _register(client, "prseller1@example.com")
    _grant_quota(client, h_seller, 2, db_session)
    asset1 = _asset_for(db_session, "prseller1@example.com")
    asset2 = _asset_for(db_session, "prseller1@example.com")
    listing1 = _listing(client, h_seller, asset1.id, price_credits=40, title="Item A")
    listing2 = _listing(client, h_seller, asset2.id, price_credits=60, title="Item B")

    h_buyer = _register(client, "prbuyer1@example.com")
    _grant_credits(client, h_buyer, 200, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing1["id"]}, headers=h_buyer
    )
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing2["id"]}, headers=h_buyer
    )
    order = client.post("/api/v1/marketplace/checkout", headers=h_buyer).json()
    assert len(order["items"]) == 2

    item_a = next(i for i in order["items"] if i["price_credits"] == 40)

    h_admin = _register(client, "pradmin1@example.com")
    _make_admin(db_session, "pradmin1@example.com")

    res = client.post(
        f"/api/v1/admin/marketplace/orders/{order['id']}/refund",
        json={"reason": "item A was defective", "item_ids": [item_a["id"]]},
        headers=h_admin,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "partially_refunded"
    refunded_item = next(i for i in body["items"] if i["id"] == item_a["id"])
    other_item = next(i for i in body["items"] if i["id"] != item_a["id"])
    assert refunded_item["is_refunded"] is True
    assert other_item["is_refunded"] is False

    # Buyer got back only the 40 credits for item A.
    assert (
        client.get("/api/v1/marketplace/wallet", headers=h_buyer).json()[
            "balance_credits"
        ]
        == 200 - 100 + 40
    )


def test_partial_refund_then_full_refund_completes_order(
    client: TestClient, db_session
):
    h_seller = _register(client, "prseller2@example.com")
    _grant_quota(client, h_seller, 2, db_session)
    asset1 = _asset_for(db_session, "prseller2@example.com")
    asset2 = _asset_for(db_session, "prseller2@example.com")
    listing1 = _listing(client, h_seller, asset1.id, price_credits=40)
    listing2 = _listing(client, h_seller, asset2.id, price_credits=60)

    h_buyer = _register(client, "prbuyer2@example.com")
    _grant_credits(client, h_buyer, 200, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing1["id"]}, headers=h_buyer
    )
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing2["id"]}, headers=h_buyer
    )
    order = client.post("/api/v1/marketplace/checkout", headers=h_buyer).json()
    item_a = order["items"][0]

    h_admin = _register(client, "pradmin2@example.com")
    _make_admin(db_session, "pradmin2@example.com")

    client.post(
        f"/api/v1/admin/marketplace/orders/{order['id']}/refund",
        json={"reason": "partial", "item_ids": [item_a["id"]]},
        headers=h_admin,
    )
    # Omitting item_ids refunds everything still outstanding.
    res = client.post(
        f"/api/v1/admin/marketplace/orders/{order['id']}/refund",
        json={"reason": "refund the rest"},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "refunded"
    assert all(i["is_refunded"] for i in res.json()["items"])


def test_refund_requires_a_reason(client: TestClient, db_session):
    h_seller = _register(client, "prseller3@example.com")
    asset = _asset_for(db_session, "prseller3@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=20)
    h_buyer = _register(client, "prbuyer3@example.com")
    _grant_credits(client, h_buyer, 50, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    order = client.post("/api/v1/marketplace/checkout", headers=h_buyer).json()

    h_admin = _register(client, "pradmin3@example.com")
    _make_admin(db_session, "pradmin3@example.com")

    res = client.post(
        f"/api/v1/admin/marketplace/orders/{order['id']}/refund",
        json={"reason": ""},
        headers=h_admin,
    )
    assert res.status_code == 422


def test_refunding_already_refunded_items_is_rejected(client: TestClient, db_session):
    h_seller = _register(client, "prseller4@example.com")
    asset = _asset_for(db_session, "prseller4@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=20)
    h_buyer = _register(client, "prbuyer4@example.com")
    _grant_credits(client, h_buyer, 50, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    order = client.post("/api/v1/marketplace/checkout", headers=h_buyer).json()
    item = order["items"][0]

    h_admin = _register(client, "pradmin4@example.com")
    _make_admin(db_session, "pradmin4@example.com")

    client.post(
        f"/api/v1/admin/marketplace/orders/{order['id']}/refund",
        json={"reason": "first", "item_ids": [item["id"]]},
        headers=h_admin,
    )
    res = client.post(
        f"/api/v1/admin/marketplace/orders/{order['id']}/refund",
        json={"reason": "again", "item_ids": [item["id"]]},
        headers=h_admin,
    )
    assert res.status_code == 409


def test_partial_refund_is_audited(client: TestClient, db_session):
    h_seller = _register(client, "prseller5@example.com")
    asset = _asset_for(db_session, "prseller5@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=20)
    h_buyer = _register(client, "prbuyer5@example.com")
    _grant_credits(client, h_buyer, 50, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    order = client.post("/api/v1/marketplace/checkout", headers=h_buyer).json()
    item = order["items"][0]

    h_admin = _register(client, "pradmin5@example.com")
    _make_admin(db_session, "pradmin5@example.com")

    client.post(
        f"/api/v1/admin/marketplace/orders/{order['id']}/refund",
        json={"reason": "damaged", "item_ids": [item["id"]]},
        headers=h_admin,
    )

    res = client.get(
        "/api/v1/admin/audit?target_type=order",
        headers=h_admin,
    )
    entry = next(a for a in res.json()["items"] if a["target_id"] == order["id"])
    assert entry["action"] == "order.refund_partial"
    assert entry["action_metadata"]["reason"] == "damaged"


# ------------------------------- ledger search -------------------------------- #
def test_admin_can_search_ledger_globally(client: TestClient, db_session):
    h_buyer = _register(client, "ledgerbuyer1@example.com")
    _grant_credits(client, h_buyer, 30, db_session)

    h_admin = _register(client, "ledgeradmin1@example.com")
    _make_admin(db_session, "ledgeradmin1@example.com")

    res = client.get("/api/v1/admin/ledger?q=ledgerbuyer1", headers=h_admin)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1
    assert all("ledgerbuyer1" in item["user"]["email"] for item in body["items"])


def test_ledger_search_filters_by_type(client: TestClient, db_session):
    h_buyer = _register(client, "ledgerbuyer2@example.com")
    _grant_credits(client, h_buyer, 30, db_session)

    h_admin = _register(client, "ledgeradmin2@example.com")
    _make_admin(db_session, "ledgeradmin2@example.com")

    res = client.get(
        "/api/v1/admin/ledger?type=plan_purchase&q=ledgerbuyer2", headers=h_admin
    )
    assert res.status_code == 200
    assert all(item["type"] == "plan_purchase" for item in res.json()["items"])


def test_non_admin_gets_403_on_ledger_search(client: TestClient, db_session):
    h_user = _register(client, "ledgeruser1@example.com")
    res = client.get("/api/v1/admin/ledger", headers=h_user)
    assert res.status_code == 403


# ------------------------------- revenue analytics ----------------------------- #
def test_admin_can_view_revenue_summary(client: TestClient, db_session):
    h_seller = _register(client, "revseller1@example.com")
    asset = _asset_for(db_session, "revseller1@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=100)
    h_buyer = _register(client, "revbuyer1@example.com")
    _grant_credits(client, h_buyer, 200, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    client.post("/api/v1/marketplace/checkout", headers=h_buyer)

    h_admin = _register(client, "revadmin1@example.com")
    _make_admin(db_session, "revadmin1@example.com")

    res = client.get("/api/v1/admin/analytics/revenue", headers=h_admin)
    assert res.status_code == 200
    body = res.json()
    assert body["total_orders"] >= 1
    assert body["total_gmv_credits"] >= 100
    assert body["total_revenue_credits"] >= 10
    assert body["current_platform_fee"] == 0.10
    assert isinstance(body["daily"], list)


def test_non_admin_gets_403_on_revenue_analytics(client: TestClient, db_session):
    h_user = _register(client, "revuser1@example.com")
    res = client.get("/api/v1/admin/analytics/revenue", headers=h_user)
    assert res.status_code == 403
