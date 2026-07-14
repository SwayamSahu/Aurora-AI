"""Credit economy: wallets, the append-only ledger, and the plan catalog.

Credits are the platform's only currency (no cash payouts in v1 — see
`app/services/wallet_service.py`). Listings/cart/orders (M2/M3) debit and
credit through this ledger; they don't touch `balance_credits` directly.
"""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class CreditPlan(UUIDMixin, TimestampMixin, Base):
    """An admin-managed, purchasable credit pack. Buying a plan grants
    `credits_granted` credits and raises the buyer's listing quota to
    `listing_quota` (quota is a high-water mark, not a recurring
    subscription — see `plan_service.purchase_plan`)."""

    __tablename__ = "credit_plans"

    name: Mapped[str] = mapped_column(String(80))
    price_cents: Mapped[int] = mapped_column(Integer)  # USD cents; 0 = free
    credits_granted: Mapped[int] = mapped_column(Integer)
    listing_quota: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Wallet(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "wallets"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    balance_credits: Mapped[int] = mapped_column(Integer, default=0)
    # Denormalized high-water mark from the best plan ever purchased —
    # checked by listing_service to cap how many active listings a seller
    # may have. Kept in sync with active_plan_id in the same transaction.
    listing_quota: Mapped[int] = mapped_column(Integer, default=0)
    active_plan_id: Mapped[str | None] = mapped_column(
        ForeignKey("credit_plans.id", ondelete="SET NULL"), nullable=True
    )

    active_plan: Mapped[CreditPlan | None] = relationship()
    transactions: Mapped[list[CreditTransaction]] = relationship(
        back_populates="wallet", cascade="all, delete-orphan"
    )


class TransactionType(str, enum.Enum):
    TOPUP = "topup"  # direct credit purchase (no plan)
    PLAN_PURCHASE = "plan_purchase"  # credits granted from buying a plan
    PURCHASE_SPEND = "purchase_spend"  # buyer spent credits on a listing
    SALE_EARNING = "sale_earning"  # seller earned credits from a sale
    PLATFORM_FEE = "platform_fee"  # platform's cut of a sale
    REFUND = "refund"
    ADMIN_ADJUST = "admin_adjust"
    GENERATION_SPEND = "generation_spend"  # credits spent on an AI generation job


class CreditTransaction(UUIDMixin, TimestampMixin, Base):
    """Append-only ledger row — never updated or deleted. `Wallet.balance_credits`
    is a cache kept in sync with this table inside the same DB transaction
    as every insert (see `wallet_service.credit`/`debit`)."""

    __tablename__ = "credit_transactions"

    wallet_id: Mapped[str] = mapped_column(
        ForeignKey("wallets.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), index=True)
    amount: Mapped[int] = mapped_column(Integer)  # signed: +credit, -debit
    balance_after: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(String(280), nullable=True)
    related_order_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    wallet: Mapped[Wallet] = relationship(back_populates="transactions")


class PurchaseStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class PlanPurchase(UUIDMixin, TimestampMixin, Base):
    """Record of a user buying a `CreditPlan`. `price_cents`/`credits_granted`
    are snapshotted at purchase time so later catalog edits don't rewrite
    history."""

    __tablename__ = "plan_purchases"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("credit_plans.id", ondelete="RESTRICT")
    )
    status: Mapped[PurchaseStatus] = mapped_column(
        Enum(PurchaseStatus), default=PurchaseStatus.PENDING, index=True
    )
    payment_provider: Mapped[str] = mapped_column(String(40))
    provider_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    price_cents: Mapped[int] = mapped_column(Integer)
    credits_granted: Mapped[int] = mapped_column(Integer)

    plan: Mapped[CreditPlan] = relationship()


class PlatformSetting(UUIDMixin, TimestampMixin, Base):
    """Generic runtime-editable key/value settings, admin-managed. Values
    are stored as strings and parsed by whichever service reads them (see
    `platform_settings_service`) — avoids a migration for every new knob."""

    __tablename__ = "platform_settings"

    key: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    value: Mapped[str] = mapped_column(String(200))
