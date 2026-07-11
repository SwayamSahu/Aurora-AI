"""Marketplace M7 — admin console (plan CRUD, moderation, wallet
adjustments, refunds) and the listing-creation rate limit. Runs fully on
the Mac (no GPU, no Stripe — MockPaymentProvider only)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
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


# ------------------------------- access control ---------------------------- #
def test_non_admin_gets_403_on_every_admin_route(client: TestClient, db_session):
    h = _register(client, "regular@example.com")
    assert client.get("/api/v1/admin/marketplace/plans", headers=h).status_code == 403
    assert (
        client.post(
            "/api/v1/admin/marketplace/plans",
            json={
                "name": "X",
                "price_cents": 0,
                "credits_granted": 0,
                "listing_quota": 1,
            },
            headers=h,
        ).status_code
        == 403
    )
    assert (
        client.get("/api/v1/admin/marketplace/listings", headers=h).status_code == 403
    )


def test_admin_routes_require_auth(client: TestClient):
    assert client.get("/api/v1/admin/marketplace/plans").status_code == 401


# --------------------------------- plan CRUD -------------------------------- #
def test_admin_can_create_update_and_list_all_plans(client: TestClient, db_session):
    h = _register(client, "admin1@example.com")
    _make_admin(db_session, "admin1@example.com")

    created = client.post(
        "/api/v1/admin/marketplace/plans",
        json={
            "name": "Mega",
            "price_cents": 4999,
            "credits_granted": 5000,
            "listing_quota": 100,
            "is_active": False,
            "sort_order": 5,
        },
        headers=h,
    )
    assert created.status_code == 201
    plan = created.json()
    assert plan["is_active"] is False

    # Inactive plans don't show on the public catalog...
    public = client.get("/api/v1/marketplace/plans").json()
    assert not any(p["id"] == plan["id"] for p in public)
    # ...but do show in the admin catalog.
    admin_list = client.get("/api/v1/admin/marketplace/plans", headers=h).json()
    assert any(p["id"] == plan["id"] for p in admin_list)

    updated = client.patch(
        f"/api/v1/admin/marketplace/plans/{plan['id']}",
        json={"is_active": True, "price_cents": 3999},
        headers=h,
    )
    assert updated.status_code == 200
    assert updated.json()["is_active"] is True
    assert updated.json()["price_cents"] == 3999

    public_after = client.get("/api/v1/marketplace/plans").json()
    assert any(p["id"] == plan["id"] for p in public_after)


def test_update_unknown_plan_404s(client: TestClient, db_session):
    h = _register(client, "admin2@example.com")
    _make_admin(db_session, "admin2@example.com")
    res = client.patch(
        "/api/v1/admin/marketplace/plans/does-not-exist",
        json={"is_active": False},
        headers=h,
    )
    assert res.status_code == 404


# --------------------------------- moderation -------------------------------- #
def test_admin_can_delist_any_listing(client: TestClient, db_session):
    h_seller = _register(client, "aseller1@example.com")
    asset = _asset_for(db_session, "aseller1@example.com")
    listing = _listing(client, h_seller, asset.id)

    h_admin = _register(client, "admin3@example.com")
    _make_admin(db_session, "admin3@example.com")

    res = client.post(
        f"/api/v1/admin/marketplace/listings/{listing['id']}/delist", headers=h_admin
    )
    assert res.status_code == 200
    assert res.json()["status"] == "delisted"

    browse = client.get("/api/v1/marketplace/listings").json()
    assert not any(item["id"] == listing["id"] for item in browse["items"])


def test_admin_listing_browse_can_filter_by_status(client: TestClient, db_session):
    h_seller = _register(client, "aseller2@example.com")
    asset1 = _asset_for(db_session, "aseller2@example.com")
    asset2 = _asset_for(db_session, "aseller2@example.com")
    _listing(client, h_seller, asset1.id, status="draft", title="Draft One")
    _listing(client, h_seller, asset2.id, status="active", title="Active One")

    h_admin = _register(client, "admin4@example.com")
    _make_admin(db_session, "admin4@example.com")

    drafts = client.get(
        "/api/v1/admin/marketplace/listings?status=draft", headers=h_admin
    ).json()
    assert all(item["status"] == "draft" for item in drafts)
    assert any(item["title"] == "Draft One" for item in drafts)


# ----------------------------- wallet adjustments ---------------------------- #
def test_admin_can_credit_and_debit_a_wallet(client: TestClient, db_session):
    h_user = _register(client, "auser1@example.com")
    user = db_session.scalar(select(User).where(User.email == "auser1@example.com"))

    h_admin = _register(client, "admin5@example.com")
    _make_admin(db_session, "admin5@example.com")

    credited = client.post(
        f"/api/v1/admin/marketplace/wallets/{user.id}/adjust",
        json={"amount": 100, "note": "support goodwill credit"},
        headers=h_admin,
    )
    assert credited.status_code == 200
    assert credited.json()["balance_credits"] == 100

    wallet = client.get("/api/v1/marketplace/wallet", headers=h_user).json()
    assert wallet["balance_credits"] == 100

    debited = client.post(
        f"/api/v1/admin/marketplace/wallets/{user.id}/adjust",
        json={"amount": -40, "note": "correcting a duplicate grant"},
        headers=h_admin,
    )
    assert debited.status_code == 200
    assert debited.json()["balance_credits"] == 60


def test_admin_debit_beyond_balance_fails_cleanly(client: TestClient, db_session):
    _register(client, "auser2@example.com")
    user = db_session.scalar(select(User).where(User.email == "auser2@example.com"))

    h_admin = _register(client, "admin6@example.com")
    _make_admin(db_session, "admin6@example.com")

    res = client.post(
        f"/api/v1/admin/marketplace/wallets/{user.id}/adjust",
        json={"amount": -50, "note": "oops"},
        headers=h_admin,
    )
    assert res.status_code == 402


def test_adjust_amount_zero_is_rejected(client: TestClient, db_session):
    _register(client, "auser3@example.com")
    user = db_session.scalar(select(User).where(User.email == "auser3@example.com"))
    h_admin = _register(client, "admin7@example.com")
    _make_admin(db_session, "admin7@example.com")

    res = client.post(
        f"/api/v1/admin/marketplace/wallets/{user.id}/adjust",
        json={"amount": 0, "note": "noop"},
        headers=h_admin,
    )
    assert res.status_code == 422


# --------------------------------- refunds ---------------------------------- #
def test_admin_can_refund_a_completed_order(client: TestClient, db_session):
    h_seller = _register(client, "aseller3@example.com")
    asset = _asset_for(db_session, "aseller3@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=100)

    h_buyer = _register(client, "abuyer1@example.com")
    _grant_credits(client, h_buyer, 200, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    order = client.post("/api/v1/marketplace/checkout", headers=h_buyer).json()

    # Buyer spent 100, seller earned 90 (10% platform fee).
    assert (
        client.get("/api/v1/marketplace/wallet", headers=h_buyer).json()[
            "balance_credits"
        ]
        == 100
    )
    assert (
        client.get("/api/v1/marketplace/wallet", headers=h_seller).json()[
            "balance_credits"
        ]
        == 90
    )

    h_admin = _register(client, "admin8@example.com")
    _make_admin(db_session, "admin8@example.com")

    refunded = client.post(
        f"/api/v1/admin/marketplace/orders/{order['id']}/refund", headers=h_admin
    )
    assert refunded.status_code == 200
    assert refunded.json()["status"] == "refunded"

    # Buyer got their 100 back; seller's 90 earning was reclaimed.
    assert (
        client.get("/api/v1/marketplace/wallet", headers=h_buyer).json()[
            "balance_credits"
        ]
        == 200
    )
    assert (
        client.get("/api/v1/marketplace/wallet", headers=h_seller).json()[
            "balance_credits"
        ]
        == 0
    )


def test_refunding_twice_fails_cleanly(client: TestClient, db_session):
    h_seller = _register(client, "aseller4@example.com")
    asset = _asset_for(db_session, "aseller4@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=20)

    h_buyer = _register(client, "abuyer2@example.com")
    _grant_credits(client, h_buyer, 50, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    order = client.post("/api/v1/marketplace/checkout", headers=h_buyer).json()

    h_admin = _register(client, "admin9@example.com")
    _make_admin(db_session, "admin9@example.com")

    client.post(
        f"/api/v1/admin/marketplace/orders/{order['id']}/refund", headers=h_admin
    )
    second = client.post(
        f"/api/v1/admin/marketplace/orders/{order['id']}/refund", headers=h_admin
    )
    assert second.status_code == 409


def test_refund_reclaim_never_drives_seller_wallet_negative(
    client: TestClient, db_session
):
    """If the seller already spent their earning, the refund reclaims only
    what's left rather than erroring or going negative."""
    h_seller = _register(client, "aseller5@example.com")
    asset = _asset_for(db_session, "aseller5@example.com")
    listing = _listing(client, h_seller, asset.id, price_credits=100)

    h_buyer = _register(client, "abuyer3@example.com")
    _grant_credits(client, h_buyer, 200, db_session)
    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    order = client.post("/api/v1/marketplace/checkout", headers=h_buyer).json()
    # Seller earned 90; spend it all elsewhere before the refund happens.
    seller_user = db_session.scalar(
        select(User).where(User.email == "aseller5@example.com")
    )

    h_admin = _register(client, "admin10@example.com")
    _make_admin(db_session, "admin10@example.com")
    client.post(
        f"/api/v1/admin/marketplace/wallets/{seller_user.id}/adjust",
        json={"amount": -90, "note": "seller withdrew/spent it"},
        headers=h_admin,
    )
    assert (
        client.get("/api/v1/marketplace/wallet", headers=h_seller).json()[
            "balance_credits"
        ]
        == 0
    )

    refunded = client.post(
        f"/api/v1/admin/marketplace/orders/{order['id']}/refund", headers=h_admin
    )
    assert refunded.status_code == 200
    # Seller wallet stays at 0 (nothing left to reclaim) instead of erroring.
    assert (
        client.get("/api/v1/marketplace/wallet", headers=h_seller).json()[
            "balance_credits"
        ]
        == 0
    )
    assert (
        client.get("/api/v1/marketplace/wallet", headers=h_buyer).json()[
            "balance_credits"
        ]
        == 200
    )


# ------------------------------ rate limiting -------------------------------- #
def test_listing_creation_is_rate_limited(client: TestClient, db_session, monkeypatch):
    monkeypatch.setattr(settings, "marketplace_listing_rate_limit_per_hour", 2)
    h_seller = _register(client, "aratelimited@example.com")
    asset = _asset_for(db_session, "aratelimited@example.com")

    first = _listing(client, h_seller, asset.id, title="One", status="draft")
    second_res = client.post(
        "/api/v1/marketplace/listings",
        json={
            "title": "Two",
            "category": "sci-fi",
            "price_credits": 10,
            "source_asset_id": asset.id,
            "status": "draft",
        },
        headers=h_seller,
    )
    assert first["id"]
    assert second_res.status_code == 201

    third_res = client.post(
        "/api/v1/marketplace/listings",
        json={
            "title": "Three",
            "category": "sci-fi",
            "price_credits": 10,
            "source_asset_id": asset.id,
            "status": "draft",
        },
        headers=h_seller,
    )
    assert third_res.status_code == 429


def test_admin_bypasses_rate_limit(client: TestClient, db_session, monkeypatch):
    monkeypatch.setattr(settings, "marketplace_listing_rate_limit_per_hour", 1)
    h_admin = _register(client, "admin11@example.com")
    _make_admin(db_session, "admin11@example.com")
    asset = _asset_for(db_session, "admin11@example.com")

    for i in range(3):
        res = client.post(
            "/api/v1/marketplace/listings",
            json={
                "title": f"Admin listing {i}",
                "category": "sci-fi",
                "price_credits": 10,
                "source_asset_id": asset.id,
                "status": "draft",
            },
            headers=h_admin,
        )
        assert res.status_code == 201
