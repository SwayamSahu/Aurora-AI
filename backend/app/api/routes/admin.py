"""Marketplace admin console (M7): plan catalog CRUD, listing moderation,
manual wallet adjustments, and order refunds. Every route requires
`is_superuser` (see `AdminUser` in `app.api.deps`)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, DbSession
from app.db.models import ListingComment, ListingStatus
from app.schemas.admin import (
    AdminPlanCreate,
    AdminPlanRead,
    AdminPlanUpdate,
    WalletAdjustRequest,
)
from app.schemas.commerce import OrderRead
from app.schemas.listing import (
    ListingCommentAdminUpdate,
    ListingCommentRead,
    ListingSummary,
)
from app.services import (
    checkout_service,
    listing_service,
    order_service,
    plan_service,
    wallet_service,
)
from app.services.marketplace_errors import MarketplaceError

router = APIRouter(prefix="/admin/marketplace", tags=["admin"])


# --------------------------------------------------------------------------- #
# Plan catalog
# --------------------------------------------------------------------------- #
@router.get("/plans", response_model=list[AdminPlanRead])
def list_plans(admin: AdminUser, db: DbSession) -> list[AdminPlanRead]:
    return [AdminPlanRead.model_validate(p) for p in plan_service.list_all_plans(db)]


@router.post("/plans", response_model=AdminPlanRead, status_code=201)
def create_plan(
    data: AdminPlanCreate, admin: AdminUser, db: DbSession
) -> AdminPlanRead:
    plan = plan_service.create_plan(db, data)
    return AdminPlanRead.model_validate(plan)


@router.patch("/plans/{plan_id}", response_model=AdminPlanRead)
def update_plan(
    plan_id: str, data: AdminPlanUpdate, admin: AdminUser, db: DbSession
) -> AdminPlanRead:
    plan = plan_service.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found.")
    plan = plan_service.update_plan(db, plan, data)
    return AdminPlanRead.model_validate(plan)


# --------------------------------------------------------------------------- #
# Moderation
# --------------------------------------------------------------------------- #
@router.get("/listings", response_model=list[ListingSummary])
def list_all_listings(
    admin: AdminUser,
    db: DbSession,
    status: Annotated[str | None, Query()] = None,
    seller_id: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
) -> list[ListingSummary]:
    stmt_status = ListingStatus(status) if status else None
    listings = listing_service.list_for_moderation(
        db, status=stmt_status, seller_id=seller_id, query=q
    )
    return [listing_service.to_read(ListingSummary, listing) for listing in listings]


@router.post("/listings/{listing_id}/delist", response_model=ListingSummary)
def delist_listing(listing_id: str, admin: AdminUser, db: DbSession) -> ListingSummary:
    listing = listing_service.get_by_id(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found.")
    listing = listing_service.admin_delist(db, listing)
    return listing_service.to_read(ListingSummary, listing)


# --------------------------------------------------------------------------- #
# Comment moderation
# --------------------------------------------------------------------------- #
@router.get("/listings/{listing_id}/comments", response_model=list[ListingCommentRead])
def list_listing_comments(
    listing_id: str, admin: AdminUser, db: DbSession
) -> list[ListingCommentRead]:
    listing = listing_service.get_by_id(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found.")
    return [
        ListingCommentRead.model_validate(c)
        for c in listing_service.list_comments(db, listing.id, include_hidden=True)
    ]


@router.patch("/comments/{comment_id}", response_model=ListingCommentRead)
def moderate_listing_comment(
    comment_id: str,
    data: ListingCommentAdminUpdate,
    admin: AdminUser,
    db: DbSession,
) -> ListingCommentRead:
    comment: ListingComment | None = listing_service.get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if data.body is not None:
        comment = listing_service.update_comment_body(db, comment, data.body)
    if data.is_hidden is not None:
        comment = listing_service.set_comment_hidden(db, comment, data.is_hidden)
    return ListingCommentRead.model_validate(comment)


# --------------------------------------------------------------------------- #
# Wallet adjustments + refunds
# --------------------------------------------------------------------------- #
@router.post("/wallets/{user_id}/adjust")
def adjust_wallet(
    user_id: str, data: WalletAdjustRequest, admin: AdminUser, db: DbSession
) -> dict:
    wallet = wallet_service.get_wallet_locked(db, user_id)
    try:
        wallet_service.admin_adjust(db, wallet, data.amount, data.note)
    except MarketplaceError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    return {"balance_credits": wallet.balance_credits}


@router.post("/orders/{order_id}/refund", response_model=OrderRead)
def refund_order(order_id: str, admin: AdminUser, db: DbSession) -> OrderRead:
    order = order_service.get_for_admin(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    try:
        order = checkout_service.refund_order(db, order)
    except MarketplaceError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return OrderRead.model_validate(order)
