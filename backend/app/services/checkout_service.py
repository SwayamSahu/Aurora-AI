"""Transactional checkout: the one place credits, listings, and asset
ownership all move together. Everything below happens inside a single DB
transaction — if anything fails partway, the whole checkout rolls back (no
half-charged buyer, no half-sold listing).

Locking order matters for deadlock avoidance: listings are locked in a
stable (sorted-by-id) order before any wallet is touched, and each wallet is
locked individually right before it's mutated.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Listing,
    ListingStatus,
    Order,
    OrderItem,
    OrderStatus,
    TransactionType,
)
from app.services import (
    asset_service,
    cart_service,
    platform_settings_service,
    wallet_service,
)
from app.services.marketplace_errors import ListingUnavailableError, MarketplaceError


def checkout(db: Session, buyer_id: str) -> Order:
    cart_items = cart_service.list_cart(db, buyer_id)
    if not cart_items:
        raise ListingUnavailableError("Your cart is empty.")

    listing_ids = sorted({c.listing_id for c in cart_items})
    locked = {
        listing.id: listing
        for listing in db.scalars(
            select(Listing).where(Listing.id.in_(listing_ids)).with_for_update()
        )
    }

    # Validate every item is still purchasable before charging anyone.
    to_purchase: list[Listing] = []
    for cart_item in cart_items:
        listing = locked.get(cart_item.listing_id)
        if (
            listing is None
            or listing.status != ListingStatus.ACTIVE
            or listing.stock < 1
        ):
            title = cart_item.listing.title if cart_item.listing else "An item"
            raise ListingUnavailableError(f"'{title}' is no longer available.")
        if listing.seller_id == buyer_id:
            raise ListingUnavailableError("You can't buy your own listing.")
        to_purchase.append(listing)

    total = sum(listing.price_credits for listing in to_purchase)

    buyer_wallet = wallet_service.get_wallet_locked(db, buyer_id)
    wallet_service.debit(
        db,
        buyer_wallet,
        total,
        TransactionType.PURCHASE_SPEND,
        note="Marketplace purchase",
    )

    order = Order(buyer_id=buyer_id, total_credits=total)
    db.add(order)
    db.flush()  # assign order.id for related_order_id / FK use below

    fee_rate = platform_settings_service.get_platform_fee(db)

    for listing in to_purchase:
        listing.stock -= 1
        if listing.stock <= 0:
            listing.status = ListingStatus.SOLD

        fee = round(listing.price_credits * fee_rate)
        seller_earning = listing.price_credits - fee
        if seller_earning > 0:
            seller_wallet = wallet_service.get_wallet_locked(db, listing.seller_id)
            wallet_service.credit(
                db,
                seller_wallet,
                seller_earning,
                TransactionType.SALE_EARNING,
                note=f"Sold: {listing.title}",
                related_order_id=order.id,
            )

        clone = asset_service.clone_for_buyer(db, listing.source_asset, buyer_id)

        db.add(
            OrderItem(
                order_id=order.id,
                listing_id=listing.id,
                seller_id=listing.seller_id,
                title=listing.title,
                price_credits=listing.price_credits,
                platform_fee_credits=fee,
                cloned_asset_id=clone.id,
            )
        )

    cart_service.clear_cart(db, buyer_id)

    db.commit()
    db.refresh(order)
    return order


def refund_order(
    db: Session, order: Order, *, reason: str, item_ids: list[str] | None = None
) -> Order:
    """Admin-triggered refund, full or partial (`item_ids` selects which
    order items to refund; omit for all remaining items). Credits the buyer
    back per-item and reclaims each seller's earning where they still have
    the balance to cover it (a seller who already spent it isn't driven
    negative — the platform absorbs that gap, a deliberate v1
    simplification). Uses each item's `platform_fee_credits`, snapshotted at
    sale time, so a later platform-fee change never alters what a past sale
    reclaims.

    Does NOT reverse listing/stock state or delete the buyer's cloned asset
    — this is a financial reversal only. Re-listing, if desired, is a
    separate manual step for the admin/seller.
    """
    if order.status == OrderStatus.REFUNDED:
        raise MarketplaceError("Order already refunded.")

    if item_ids is not None:
        wanted = set(item_ids)
        to_refund = [
            item for item in order.items if item.id in wanted and not item.is_refunded
        ]
        if not to_refund:
            raise MarketplaceError("No refundable items match the given ids.")
    else:
        to_refund = [item for item in order.items if not item.is_refunded]
        if not to_refund:
            raise MarketplaceError("Order already refunded.")

    refund_total = sum(item.price_credits for item in to_refund)

    buyer_wallet = wallet_service.get_wallet_locked(db, order.buyer_id)
    wallet_service.credit(
        db,
        buyer_wallet,
        refund_total,
        TransactionType.REFUND,
        note=f"Order refund: {reason}",
        related_order_id=order.id,
    )

    for item in to_refund:
        seller_earning = item.price_credits - item.platform_fee_credits
        if seller_earning > 0:
            seller_wallet = wallet_service.get_wallet_locked(db, item.seller_id)
            reclaim = min(seller_earning, seller_wallet.balance_credits)
            if reclaim > 0:
                wallet_service.debit(
                    db,
                    seller_wallet,
                    reclaim,
                    TransactionType.REFUND,
                    note=f"Refund reclaim: {item.title} ({reason})",
                    related_order_id=order.id,
                )
        item.is_refunded = True

    order.status = (
        OrderStatus.REFUNDED
        if all(item.is_refunded for item in order.items)
        else OrderStatus.PARTIALLY_REFUNDED
    )
    db.commit()
    db.refresh(order)
    return order
