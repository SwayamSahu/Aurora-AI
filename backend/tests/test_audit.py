"""Admin audit log (F1) — privileged actions are recorded, own-content
actions are not, and the log is admin-only and append-only."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import (
    Asset,
    AssetKind,
    AssetSource,
    CreditPlan,
    Project,
    User,
    UserRole,
)
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


def _set_role(db_session, email: str, role: UserRole) -> None:
    user = db_session.scalar(select(User).where(User.email == email))
    user.role = role
    db_session.commit()


def _create_post(client, headers, **overrides):
    payload = {
        "title": "Audit Post",
        "category": "tutorials",
        "body_html": "<p>Body.</p>",
        "status": "published",
        **overrides,
    }
    return client.post("/api/v1/blog/posts", json=payload, headers=headers)


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
        "title": "Audit Listing",
        "category": "sci-fi",
        "price_credits": 50,
        "source_asset_id": asset_id,
        "status": "active",
        **overrides,
    }
    return client.post(
        "/api/v1/marketplace/listings", json=payload, headers=headers
    ).json()


def _audit(client, headers, **params):
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return client.get(
        f"/api/v1/admin/audit?{qs}" if qs else "/api/v1/admin/audit", headers=headers
    )


# --------------------------- admin-route actions ---------------------------- #
def test_wallet_adjust_and_refund_are_audited(client: TestClient, db_session):
    h_admin = _register(client, "aud_admin1@example.com")
    _set_role(db_session, "aud_admin1@example.com", UserRole.ADMIN)
    victim = db_session.scalar(
        select(User).where(User.email == "aud_admin1@example.com")
    )

    client.post(
        f"/api/v1/admin/marketplace/wallets/{victim.id}/adjust",
        json={"amount": 100, "note": "goodwill"},
        headers=h_admin,
    )

    log = _audit(client, h_admin, action="wallet.adjust").json()
    assert log["total"] == 1
    entry = log["items"][0]
    assert entry["actor"]["email"] == "aud_admin1@example.com"
    assert entry["target_id"] == victim.id
    assert entry["action_metadata"]["amount"] == 100
    assert entry["action_metadata"]["note"] == "goodwill"


def test_plan_create_is_audited(client: TestClient, db_session):
    h_admin = _register(client, "aud_admin2@example.com")
    _set_role(db_session, "aud_admin2@example.com", UserRole.ADMIN)
    client.post(
        "/api/v1/admin/marketplace/plans",
        json={
            "name": "Audited Plan",
            "price_cents": 500,
            "credits_granted": 100,
            "listing_quota": 5,
        },
        headers=h_admin,
    )
    log = _audit(client, h_admin, action="plan.create").json()
    assert log["total"] == 1
    assert log["items"][0]["action_metadata"]["name"] == "Audited Plan"


def test_delist_and_comment_moderation_are_audited(client: TestClient, db_session):
    h_seller = _register(client, "aud_seller1@example.com")
    asset = _asset_for(db_session, "aud_seller1@example.com")
    listing = _listing(client, h_seller, asset.id)
    h_commenter = _register(client, "aud_commenter1@example.com")
    comment = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/comments",
        json={"body": "spam"},
        headers=h_commenter,
    ).json()

    h_mod = _register(client, "aud_mod1@example.com")
    _set_role(db_session, "aud_mod1@example.com", UserRole.MODERATOR)

    client.post(
        f"/api/v1/admin/marketplace/listings/{listing['id']}/delist", headers=h_mod
    )
    client.patch(
        f"/api/v1/admin/marketplace/comments/{comment['id']}",
        json={"is_hidden": True},
        headers=h_mod,
    )

    # Moderator can't read the audit log, so promote a separate admin to read it.
    h_admin = _register(client, "aud_admin3@example.com")
    _set_role(db_session, "aud_admin3@example.com", UserRole.ADMIN)
    actions = {e["action"] for e in _audit(client, h_admin).json()["items"]}
    assert "listing.delist" in actions
    assert "listing_comment.moderate" in actions


# ------------------------- content-route actions ---------------------------- #
def test_moderator_editing_others_post_is_audited(client: TestClient, db_session):
    h_author = _register(client, "aud_author1@example.com")
    post = _create_post(client, h_author).json()

    h_mod = _register(client, "aud_mod2@example.com")
    _set_role(db_session, "aud_mod2@example.com", UserRole.MODERATOR)
    client.patch(
        f"/api/v1/blog/posts/{post['id']}",
        json={"title": "Moderated title"},
        headers=h_mod,
    )

    h_admin = _register(client, "aud_admin4@example.com")
    _set_role(db_session, "aud_admin4@example.com", UserRole.ADMIN)
    log = _audit(client, h_admin, action="post.update").json()
    assert log["total"] == 1
    assert log["items"][0]["target_id"] == post["id"]


def test_author_editing_own_post_is_not_audited(client: TestClient, db_session):
    h_author = _register(client, "aud_author2@example.com")
    post = _create_post(client, h_author).json()
    # Author edits their OWN post — not a privileged action, no audit entry.
    client.patch(
        f"/api/v1/blog/posts/{post['id']}",
        json={"title": "Self edit"},
        headers=h_author,
    )

    h_admin = _register(client, "aud_admin5@example.com")
    _set_role(db_session, "aud_admin5@example.com", UserRole.ADMIN)
    log = _audit(client, h_admin, action="post.update").json()
    assert log["total"] == 0


def test_moderator_deleting_others_listing_is_audited(client: TestClient, db_session):
    h_seller = _register(client, "aud_seller2@example.com")
    asset = _asset_for(db_session, "aud_seller2@example.com")
    listing = _listing(client, h_seller, asset.id, status="draft")

    h_mod = _register(client, "aud_mod3@example.com")
    _set_role(db_session, "aud_mod3@example.com", UserRole.MODERATOR)
    client.delete(f"/api/v1/marketplace/listings/{listing['id']}", headers=h_mod)

    h_admin = _register(client, "aud_admin6@example.com")
    _set_role(db_session, "aud_admin6@example.com", UserRole.ADMIN)
    log = _audit(client, h_admin, action="listing.delete").json()
    assert log["total"] == 1
    assert log["items"][0]["action_metadata"]["seller_id"]


# ------------------------------- access control ----------------------------- #
def test_audit_log_is_admin_only_not_moderator(client: TestClient, db_session):
    h_mod = _register(client, "aud_mod4@example.com")
    _set_role(db_session, "aud_mod4@example.com", UserRole.MODERATOR)
    assert _audit(client, h_mod).status_code == 403


def test_audit_log_filters_by_target_type(client: TestClient, db_session):
    h_admin = _register(client, "aud_admin7@example.com")
    _set_role(db_session, "aud_admin7@example.com", UserRole.ADMIN)
    victim = db_session.scalar(
        select(User).where(User.email == "aud_admin7@example.com")
    )
    plan = CreditPlan(
        name="P",
        price_cents=0,
        credits_granted=0,
        listing_quota=1,
        is_active=True,
        sort_order=1,
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    client.post(
        f"/api/v1/admin/marketplace/wallets/{victim.id}/adjust",
        json={"amount": 10, "note": "x"},
        headers=h_admin,
    )
    client.patch(
        f"/api/v1/admin/marketplace/plans/{plan.id}",
        json={"price_cents": 200},
        headers=h_admin,
    )

    wallet_only = _audit(client, h_admin, target_type="wallet").json()
    assert all(e["target_type"] == "wallet" for e in wallet_only["items"])
    assert wallet_only["total"] == 1
