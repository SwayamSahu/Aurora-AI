"""Marketplace: wallet + credit plans (M1). Listings/cart/checkout land in
later phases under the same `/marketplace` prefix."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, DbSession
from app.db.models import CreditPlan
from app.schemas.billing import (
    CreditPlanRead,
    CreditTransactionRead,
    PlanPurchaseRead,
    WalletHistoryResponse,
    WalletRead,
)
from app.services import plan_service, wallet_service
from app.services.marketplace_errors import MarketplaceError
from app.services.payment_provider import get_payment_provider

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


# --------------------------------------------------------------------------- #
# Plans (public catalog, auth-gated purchase)
# --------------------------------------------------------------------------- #
@router.get("/plans", response_model=list[CreditPlanRead])
def list_plans(db: DbSession) -> list[CreditPlan]:
    return plan_service.list_plans(db)


@router.post(
    "/plans/{plan_id}/purchase", response_model=PlanPurchaseRead, status_code=201
)
def purchase_plan(
    plan_id: str, current_user: CurrentUser, db: DbSession
) -> PlanPurchaseRead:
    plan = plan_service.get_plan(db, plan_id)
    if plan is None or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan not found.")
    try:
        purchase = plan_service.purchase_plan(
            db, current_user.id, plan, get_payment_provider()
        )
    except MarketplaceError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    return PlanPurchaseRead.model_validate(purchase)


# --------------------------------------------------------------------------- #
# Wallet
# --------------------------------------------------------------------------- #
@router.get("/wallet", response_model=WalletRead)
def get_wallet(current_user: CurrentUser, db: DbSession) -> WalletRead:
    wallet = wallet_service.get_or_create_wallet(db, current_user.id)
    return WalletRead.model_validate(wallet)


@router.get("/wallet/transactions", response_model=WalletHistoryResponse)
def get_wallet_transactions(
    current_user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 24,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> WalletHistoryResponse:
    wallet = wallet_service.get_or_create_wallet(db, current_user.id)
    items, total = wallet_service.list_transactions(
        db, wallet.id, limit=limit, offset=offset
    )
    next_offset = offset + limit if offset + limit < total else None
    return WalletHistoryResponse(
        items=[CreditTransactionRead.model_validate(t) for t in items],
        total=total,
        next_offset=next_offset,
    )
