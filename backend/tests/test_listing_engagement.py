"""Marketplace M6 — listing likes, comments, and conditional generation
(prompt/seed/model) reveal. Runs fully on the Mac (no GPU)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import (
    Asset,
    AssetKind,
    AssetSource,
    Job,
    JobStatus,
    JobType,
    Project,
    User,
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


def _asset_for(db_session, email: str, *, with_job: bool = False) -> Asset:
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

    if with_job:
        job = Job(
            project_id=project.id,
            type=JobType.GENERATE_VIDEO,
            status=JobStatus.SUCCEEDED,
            progress=1.0,
            params={"prompt": "a neon city at night", "seed": 42, "model": "aurora-v1"},
            result_asset_id=asset.id,
        )
        db_session.add(job)
        db_session.commit()

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


# ------------------------------- likes ----------------------------------- #
def test_like_toggle_updates_count_and_liked_by_me(client: TestClient, db_session):
    h_seller = _register(client, "eseller1@example.com")
    asset = _asset_for(db_session, "eseller1@example.com")
    listing = _listing(client, h_seller, asset.id)

    h_liker = _register(client, "eliker1@example.com")
    liked = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/like",
        json={"liked": True},
        headers=h_liker,
    )
    assert liked.status_code == 200
    body = liked.json()
    assert body["like_count"] == 1
    assert body["liked_by_me"] is True

    unliked = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/like",
        json={"liked": False},
        headers=h_liker,
    )
    assert unliked.json()["like_count"] == 0
    assert unliked.json()["liked_by_me"] is False


def test_liking_twice_is_idempotent(client: TestClient, db_session):
    h_seller = _register(client, "eseller2@example.com")
    asset = _asset_for(db_session, "eseller2@example.com")
    listing = _listing(client, h_seller, asset.id)

    h_liker = _register(client, "eliker2@example.com")
    for _ in range(3):
        res = client.post(
            f"/api/v1/marketplace/listings/{listing['id']}/like",
            json={"liked": True},
            headers=h_liker,
        )
    assert res.json()["like_count"] == 1


def test_like_requires_auth(client: TestClient, db_session):
    h_seller = _register(client, "eseller3@example.com")
    asset = _asset_for(db_session, "eseller3@example.com")
    listing = _listing(client, h_seller, asset.id)

    res = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/like", json={"liked": True}
    )
    assert res.status_code == 401


def test_get_listing_reports_liked_by_me_for_viewer(client: TestClient, db_session):
    h_seller = _register(client, "eseller4@example.com")
    asset = _asset_for(db_session, "eseller4@example.com")
    listing = _listing(client, h_seller, asset.id)

    h_liker = _register(client, "eliker4@example.com")
    client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/like",
        json={"liked": True},
        headers=h_liker,
    )

    as_liker = client.get(
        f"/api/v1/marketplace/listings/{listing['id']}", headers=h_liker
    ).json()
    assert as_liker["liked_by_me"] is True

    h_other = _register(client, "eother4@example.com")
    as_other = client.get(
        f"/api/v1/marketplace/listings/{listing['id']}", headers=h_other
    ).json()
    assert as_other["liked_by_me"] is False


# ------------------------------ comments ---------------------------------- #
def test_add_list_delete_comment(client: TestClient, db_session):
    h_seller = _register(client, "eseller5@example.com")
    asset = _asset_for(db_session, "eseller5@example.com")
    listing = _listing(client, h_seller, asset.id)

    h_commenter = _register(client, "ecommenter5@example.com")
    add = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/comments",
        json={"body": "Love this clip!"},
        headers=h_commenter,
    )
    assert add.status_code == 201
    comment = add.json()
    assert comment["body"] == "Love this clip!"
    assert comment["author"]["full_name"] == "ecommenter5"

    listed = client.get(f"/api/v1/marketplace/listings/{listing['id']}/comments").json()
    assert len(listed) == 1

    detail = client.get(f"/api/v1/marketplace/listings/{listing['id']}").json()
    assert detail["comment_count"] == 1

    deleted = client.delete(
        f"/api/v1/marketplace/comments/{comment['id']}", headers=h_commenter
    )
    assert deleted.status_code == 204
    assert (
        client.get(f"/api/v1/marketplace/listings/{listing['id']}").json()[
            "comment_count"
        ]
        == 0
    )


def test_cannot_delete_others_comment(client: TestClient, db_session):
    h_seller = _register(client, "eseller6@example.com")
    asset = _asset_for(db_session, "eseller6@example.com")
    listing = _listing(client, h_seller, asset.id)

    h_commenter = _register(client, "ecommenter6@example.com")
    comment = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/comments",
        json={"body": "Nice!"},
        headers=h_commenter,
    ).json()

    h_other = _register(client, "eother6@example.com")
    res = client.delete(
        f"/api/v1/marketplace/comments/{comment['id']}", headers=h_other
    )
    assert res.status_code == 403


def test_comment_requires_nonempty_body(client: TestClient, db_session):
    h_seller = _register(client, "eseller7@example.com")
    asset = _asset_for(db_session, "eseller7@example.com")
    listing = _listing(client, h_seller, asset.id)

    res = client.post(
        f"/api/v1/marketplace/listings/{listing['id']}/comments",
        json={"body": ""},
        headers=h_seller,
    )
    assert res.status_code == 422


# --------------------------- generation reveal ----------------------------- #
def test_generation_reveal_hidden_from_strangers(client: TestClient, db_session):
    h_seller = _register(client, "eseller8@example.com")
    asset = _asset_for(db_session, "eseller8@example.com", with_job=True)
    listing = _listing(client, h_seller, asset.id)

    h_stranger = _register(client, "estranger8@example.com")
    res = client.get(
        f"/api/v1/marketplace/listings/{listing['id']}", headers=h_stranger
    ).json()
    assert res["generation"] is None

    anon = client.get(f"/api/v1/marketplace/listings/{listing['id']}").json()
    assert anon["generation"] is None


def test_generation_reveal_visible_to_seller(client: TestClient, db_session):
    h_seller = _register(client, "eseller9@example.com")
    asset = _asset_for(db_session, "eseller9@example.com", with_job=True)
    listing = _listing(client, h_seller, asset.id)

    res = client.get(
        f"/api/v1/marketplace/listings/{listing['id']}", headers=h_seller
    ).json()
    assert res["generation"] == {
        "prompt": "a neon city at night",
        "seed": 42,
        "model": "aurora-v1",
    }


def test_generation_reveal_visible_to_buyer_after_purchase(
    client: TestClient, db_session
):
    h_seller = _register(client, "eseller10@example.com")
    asset = _asset_for(db_session, "eseller10@example.com", with_job=True)
    listing = _listing(client, h_seller, asset.id, price_credits=20)

    h_buyer = _register(client, "ebuyer10@example.com")
    _grant_credits(client, h_buyer, 100, db_session)

    # Before purchase, hidden.
    before = client.get(
        f"/api/v1/marketplace/listings/{listing['id']}", headers=h_buyer
    ).json()
    assert before["generation"] is None

    client.post(
        "/api/v1/marketplace/cart", json={"listing_id": listing["id"]}, headers=h_buyer
    )
    client.post("/api/v1/marketplace/checkout", headers=h_buyer)

    # After purchase, the listing is sold (non-active) but the buyer can
    # still fetch it, now with generation data revealed.
    after = client.get(
        f"/api/v1/marketplace/listings/{listing['id']}", headers=h_buyer
    ).json()
    assert after["generation"]["prompt"] == "a neon city at night"


def test_generation_is_none_for_uploaded_asset(client: TestClient, db_session):
    """An uploaded (not AI-generated) asset has no backing Job, so
    generation is always None even for the owner."""
    h_seller = _register(client, "eseller11@example.com")
    asset = _asset_for(db_session, "eseller11@example.com", with_job=False)
    listing = _listing(client, h_seller, asset.id)

    res = client.get(
        f"/api/v1/marketplace/listings/{listing['id']}", headers=h_seller
    ).json()
    assert res["generation"] is None
