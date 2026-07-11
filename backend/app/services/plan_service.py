"""Credit plan catalog + purchasing. Buying a plan is a one-time top-up
(not a recurring subscription — no renewal/cancellation engine in this
build): it grants credits immediately and raises the buyer's listing quota
to `max(current, plan.listing_quota)`, a high-water mark rather than
something that expires."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CreditPlan, PlanPurchase, PurchaseStatus, TransactionType
from app.services import wallet_service
from app.services.marketplace_errors import PaymentFailedError
from app.services.payment_provider import PaymentProvider


def list_plans(db: Session) -> list[CreditPlan]:
    return list(
        db.scalars(
            select(CreditPlan)
            .where(CreditPlan.is_active.is_(True))
            .order_by(CreditPlan.sort_order.asc())
        )
    )


def get_plan(db: Session, plan_id: str) -> CreditPlan | None:
    return db.get(CreditPlan, plan_id)


# --------------------------------- admin ---------------------------------- #
def list_all_plans(db: Session) -> list[CreditPlan]:
    """Includes inactive plans — active-only `list_plans` is for the public
    pricing page; this is for the admin catalog view."""
    return list(db.scalars(select(CreditPlan).order_by(CreditPlan.sort_order.asc())))


def create_plan(db: Session, data) -> CreditPlan:
    plan = CreditPlan(
        name=data.name,
        price_cents=data.price_cents,
        credits_granted=data.credits_granted,
        listing_quota=data.listing_quota,
        is_active=data.is_active if data.is_active is not None else True,
        sort_order=data.sort_order or 0,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(db: Session, plan: CreditPlan, data) -> CreditPlan:
    for field in (
        "name",
        "price_cents",
        "credits_granted",
        "listing_quota",
        "is_active",
        "sort_order",
    ):
        value = getattr(data, field, None)
        if value is not None:
            setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return plan


def purchase_plan(
    db: Session, user_id: str, plan: CreditPlan, provider: PaymentProvider
) -> PlanPurchase:
    """Charges the user for `plan` and, on success, credits their wallet and
    raises their listing quota — all inside one DB transaction so a failed
    charge never leaves a half-applied credit grant."""
    result = provider.charge(
        user_id=user_id,
        amount_cents=plan.price_cents,
        description=f"Aurora plan: {plan.name}",
    )

    purchase = PlanPurchase(
        user_id=user_id,
        plan_id=plan.id,
        payment_provider=provider.name,
        provider_ref=result.provider_ref,
        price_cents=plan.price_cents,
        credits_granted=plan.credits_granted,
        status=PurchaseStatus.PAID if result.success else PurchaseStatus.FAILED,
    )
    db.add(purchase)

    if not result.success:
        db.commit()
        db.refresh(purchase)
        raise PaymentFailedError(result.failure_reason or "Payment failed.")

    wallet = wallet_service.get_wallet_locked(db, user_id)
    if plan.credits_granted > 0:
        wallet_service.credit(
            db,
            wallet,
            plan.credits_granted,
            TransactionType.PLAN_PURCHASE,
            note=f"Purchased plan: {plan.name}",
        )
    wallet.listing_quota = max(wallet.listing_quota, plan.listing_quota)
    wallet.active_plan_id = plan.id

    db.commit()
    db.refresh(purchase)
    return purchase
