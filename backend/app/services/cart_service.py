"""Server-side cart (not local/client state) so it persists across devices.
Adding is idempotent — re-adding an already-cart listing just returns the
existing row rather than erroring or duplicating (the unique constraint on
(user_id, listing_id) backs this)."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import CartItem, Listing, ListingStatus
from app.services.marketplace_errors import ListingUnavailableError


def list_cart(db: Session, user_id: str) -> list[CartItem]:
    return list(
        db.scalars(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(selectinload(CartItem.listing))
            .order_by(CartItem.created_at.asc())
        )
    )


def add_to_cart(db: Session, user_id: str, listing_id: str) -> CartItem:
    listing = db.get(Listing, listing_id)
    if listing is None or listing.status != ListingStatus.ACTIVE:
        raise ListingUnavailableError("That listing isn't available.")
    if listing.seller_id == user_id:
        raise ListingUnavailableError("You can't buy your own listing.")

    existing = db.scalar(
        select(CartItem).where(
            CartItem.user_id == user_id, CartItem.listing_id == listing_id
        )
    )
    if existing is not None:
        return existing

    item = CartItem(user_id=user_id, listing_id=listing_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_cart(db: Session, user_id: str, cart_item_id: str) -> bool:
    item = db.scalar(
        select(CartItem).where(CartItem.id == cart_item_id, CartItem.user_id == user_id)
    )
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True


def clear_cart(db: Session, user_id: str) -> None:
    db.execute(delete(CartItem).where(CartItem.user_id == user_id))
