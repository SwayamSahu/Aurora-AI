"""Marketplace M1 — wallet, credit ledger, plan catalog + purchase.

Runs fully on the Mac (no GPU, no real payment provider — MockPaymentProvider
always succeeds). The seeded plan catalog only exists via the Alembic
migration's bulk_insert, not in the isolated SQLite test schema, so tests
insert their own `CreditPlan` rows directly via `db_session`.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db.models import CreditPlan
from app.services import wallet_service
from app.services.marketplace_errors import InsufficientCreditsError


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


def _make_plan(db_session, **overrides) -> CreditPlan:
    fields = {
        "name": "Creator",
        "price_cents": 999,
        "credits_granted": 500,
        "listing_quota": 10,
        "is_active": True,
        "sort_order": 1,
        **overrides,
    }
    plan = CreditPlan(**fields)
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


def test_wallet_is_lazily_created_with_free_quota(client: TestClient):
    h = _register(client, "wallet1@example.com")
    res = client.get("/api/v1/marketplace/wallet", headers=h)
    assert res.status_code == 200
    wallet = res.json()
    assert wallet["balance_credits"] == 0
    assert wallet["listing_quota"] == 1  # FREE_LISTING_QUOTA
    assert wallet["active_plan_id"] is None


def test_list_plans_returns_active_only(client: TestClient, db_session):
    _make_plan(db_session, name="Creator", is_active=True, sort_order=1)
    _make_plan(db_session, name="Retired", is_active=False, sort_order=2)
    res = client.get("/api/v1/marketplace/plans")
    assert res.status_code == 200
    names = [p["name"] for p in res.json()]
    assert names == ["Creator"]


def test_purchase_plan_credits_wallet_and_raises_quota(client: TestClient, db_session):
    h = _register(client, "buyer@example.com")
    plan = _make_plan(db_session, credits_granted=500, listing_quota=10)

    res = client.post(f"/api/v1/marketplace/plans/{plan.id}/purchase", headers=h)
    assert res.status_code == 201
    purchase = res.json()
    assert purchase["status"] == "paid"
    assert purchase["credits_granted"] == 500

    wallet = client.get("/api/v1/marketplace/wallet", headers=h).json()
    assert wallet["balance_credits"] == 500
    assert wallet["listing_quota"] == 10
    assert wallet["active_plan_id"] == plan.id


def test_purchase_plan_quota_is_a_high_water_mark(client: TestClient, db_session):
    """Buying a second, smaller plan tops up credits but never lowers quota."""
    h = _register(client, "buyer2@example.com")
    big = _make_plan(db_session, name="Pro", credits_granted=2000, listing_quota=50)
    small = _make_plan(db_session, name="Starter", credits_granted=100, listing_quota=3)

    client.post(f"/api/v1/marketplace/plans/{big.id}/purchase", headers=h)
    client.post(f"/api/v1/marketplace/plans/{small.id}/purchase", headers=h)

    wallet = client.get("/api/v1/marketplace/wallet", headers=h).json()
    assert wallet["balance_credits"] == 2100
    assert wallet["listing_quota"] == 50  # unchanged by the smaller plan
    assert wallet["active_plan_id"] == small.id  # still "on" the latest purchase


def test_purchase_unknown_or_inactive_plan_404s(client: TestClient, db_session):
    h = _register(client, "buyer3@example.com")
    inactive = _make_plan(db_session, is_active=False)
    assert (
        client.post(
            f"/api/v1/marketplace/plans/{inactive.id}/purchase", headers=h
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/marketplace/plans/does-not-exist/purchase", headers=h
        ).status_code
        == 404
    )


def test_purchase_requires_auth(client: TestClient, db_session):
    plan = _make_plan(db_session)
    res = client.post(f"/api/v1/marketplace/plans/{plan.id}/purchase")
    assert res.status_code == 401


def test_wallet_transaction_history_lists_every_purchase(
    client: TestClient, db_session
):
    h = _register(client, "buyer4@example.com")
    p1 = _make_plan(db_session, name="A", credits_granted=100, listing_quota=1)
    p2 = _make_plan(db_session, name="B", credits_granted=200, listing_quota=2)
    client.post(f"/api/v1/marketplace/plans/{p1.id}/purchase", headers=h)
    client.post(f"/api/v1/marketplace/plans/{p2.id}/purchase", headers=h)

    res = client.get("/api/v1/marketplace/wallet/transactions", headers=h)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    assert sorted(t["amount"] for t in body["items"]) == [100, 200]
    assert all(t["type"] == "plan_purchase" for t in body["items"])
    # balance_after on the two rows reflects an accumulating ledger, in some order.
    assert sorted(t["balance_after"] for t in body["items"]) == [100, 300]


def test_wallet_service_debit_rejects_insufficient_balance(db_session):
    from app.core.security import hash_password
    from app.db.models import User

    user = User(
        email="svc@example.com", hashed_password=hash_password("x"), full_name="Svc"
    )
    db_session.add(user)
    db_session.commit()

    wallet = wallet_service.get_or_create_wallet(db_session, user.id)
    assert wallet.balance_credits == 0

    with pytest.raises(InsufficientCreditsError):
        wallet_service.debit(
            db_session, wallet, 10, wallet_service.TransactionType.PURCHASE_SPEND
        )
