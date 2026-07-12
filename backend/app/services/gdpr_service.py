"""GDPR data portability (Art. 20) and right to erasure (Art. 17).

Erasure anonymizes the `User` row rather than deleting it: nearly every
table FK's to `users.id` with `ondelete=CASCADE` (posts, listings, orders,
comments, wallets), so a hard delete would silently destroy other people's
order history too (an `OrderItem.seller_id` cascade would wipe a buyer's
purchase record if the seller's account were deleted outright). Scrubbing
PII on the row while keeping it in place is the standard, safe approach.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import BlogComment, ListingComment, User
from app.services import blog_service, listing_service, order_service, wallet_service


def export_user_data(db: Session, user: User) -> dict:
    """Everything the platform holds about this user, in one JSON-able dict
    — the user's own copy under GDPR Art. 20 (data portability)."""
    wallet = wallet_service.get_or_create_wallet(db, user.id)
    transactions, _ = wallet_service.list_transactions(db, wallet.id, limit=10_000)
    posts = blog_service.list_for_author(db, user.id)
    listings = listing_service.list_for_seller(db, user.id)
    orders = order_service.list_for_buyer(db, user.id)
    sales = order_service.list_sales_for_seller(db, user.id)
    blog_comments = list(
        db.scalars(select(BlogComment).where(BlogComment.author_id == user.id))
    )
    listing_comments = list(
        db.scalars(select(ListingComment).where(ListingComment.author_id == user.id))
    )

    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "profile": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "created_at": user.created_at.isoformat(),
        },
        "wallet": {
            "balance_credits": wallet.balance_credits,
            "listing_quota": wallet.listing_quota,
            "transactions": [
                {
                    "type": tx.type.value,
                    "amount": tx.amount,
                    "balance_after": tx.balance_after,
                    "note": tx.note,
                    "created_at": tx.created_at.isoformat(),
                }
                for tx in transactions
            ],
        },
        "blog_posts": [
            {"id": p.id, "title": p.title, "status": p.status.value, "slug": p.slug}
            for p in posts
        ],
        "blog_comments": [
            {"id": c.id, "post_id": c.post_id, "body": c.body}
            for c in blog_comments
        ],
        "listings": [
            {
                "id": listing.id,
                "title": listing.title,
                "status": listing.status.value,
                "price_credits": listing.price_credits,
            }
            for listing in listings
        ],
        "listing_comments": [
            {"id": c.id, "listing_id": c.listing_id, "body": c.body}
            for c in listing_comments
        ],
        "orders": [
            {
                "id": o.id,
                "total_credits": o.total_credits,
                "status": o.status.value,
                "created_at": o.created_at.isoformat(),
                "items": [{"title": i.title, "price_credits": i.price_credits} for i in o.items],
            }
            for o in orders
        ],
        "sales": [
            {
                "order_id": s.order_id,
                "title": s.title,
                "price_credits": s.price_credits,
                "created_at": s.created_at.isoformat(),
            }
            for s in sales
        ],
    }


def anonymize_user(db: Session, user: User) -> User:
    """Right-to-erasure: scrub PII, deactivate, keep the row (and every
    CASCADE-linked record it anchors) intact. Idempotent."""
    if user.erased_at is not None:
        return user
    user.email = f"erased-{user.id}@deleted.invalid"
    user.full_name = None
    user.hashed_password = hash_password(secrets.token_urlsafe(32))
    user.preferences = {}
    user.is_active = False
    user.erased_at = datetime.now(UTC)
    db.commit()
    db.refresh(user)
    return user
