"""Marketplace cart, checkout, and order history (M3)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentUser, DbSession
from app.db.models import CartItem, Order, OrderItem
from app.schemas.commerce import (
    CartItemAdd,
    CartItemRead,
    CartRead,
    OrderItemRead,
    OrderRead,
    SaleRead,
)
from app.schemas.listing import ListingSummary
from app.services import cart_service, checkout_service, listing_service, order_service
from app.services.marketplace_errors import MarketplaceError

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


def _cart_item_read(item: CartItem) -> CartItemRead:
    return CartItemRead(
        id=item.id,
        listing=listing_service.with_cover_url(ListingSummary, item.listing),
        created_at=item.created_at,
    )


def _cart_read(items: list[CartItem]) -> CartRead:
    reads = [_cart_item_read(i) for i in items]
    return CartRead(
        items=reads, total_credits=sum(r.listing.price_credits for r in reads)
    )


def _order_read(order: Order) -> OrderRead:
    return OrderRead(
        id=order.id,
        total_credits=order.total_credits,
        status=order.status.value,
        items=[OrderItemRead.model_validate(i) for i in order.items],
        created_at=order.created_at,
    )


def _sale_read(item: OrderItem) -> SaleRead:
    return SaleRead(
        id=item.id,
        order_id=item.order_id,
        title=item.title,
        price_credits=item.price_credits,
        buyer_id=item.order.buyer_id,
        created_at=item.created_at,
    )


# --------------------------------------------------------------------------- #
# Cart
# --------------------------------------------------------------------------- #
@router.get("/cart", response_model=CartRead)
def get_cart(current_user: CurrentUser, db: DbSession) -> CartRead:
    return _cart_read(cart_service.list_cart(db, current_user.id))


@router.post("/cart", response_model=CartRead, status_code=201)
def add_to_cart(
    data: CartItemAdd, current_user: CurrentUser, db: DbSession
) -> CartRead:
    try:
        cart_service.add_to_cart(db, current_user.id, data.listing_id)
    except MarketplaceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _cart_read(cart_service.list_cart(db, current_user.id))


@router.delete("/cart/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    cart_item_id: str, current_user: CurrentUser, db: DbSession
) -> Response:
    removed = cart_service.remove_from_cart(db, current_user.id, cart_item_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------- #
# Checkout
# --------------------------------------------------------------------------- #
@router.post("/checkout", response_model=OrderRead, status_code=201)
def checkout(current_user: CurrentUser, db: DbSession) -> OrderRead:
    try:
        order = checkout_service.checkout(db, current_user.id)
    except MarketplaceError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    return _order_read(order)


# --------------------------------------------------------------------------- #
# Order history
# --------------------------------------------------------------------------- #
@router.get("/orders", response_model=list[OrderRead])
def my_orders(current_user: CurrentUser, db: DbSession) -> list[OrderRead]:
    return [_order_read(o) for o in order_service.list_for_buyer(db, current_user.id)]


@router.get("/orders/sales", response_model=list[SaleRead])
def my_sales(current_user: CurrentUser, db: DbSession) -> list[SaleRead]:
    return [
        _sale_read(i) for i in order_service.list_sales_for_seller(db, current_user.id)
    ]
