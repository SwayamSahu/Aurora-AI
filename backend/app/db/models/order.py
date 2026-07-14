"""Cart + completed orders (M3). Checkout is synchronous and always
succeeds-or-fails atomically (credits are spent instantly, no async payment
step) — so there's no "pending" order state, only completed/refunded."""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class CartItem(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("user_id", "listing_id", name="uq_cart_user_listing"),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    listing_id: Mapped[str] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )

    listing: Mapped[Listing] = relationship()  # noqa: F821


class OrderStatus(str, enum.Enum):
    COMPLETED = "completed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class Order(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    buyer_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    total_credits: Mapped[int] = mapped_column(Integer)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.COMPLETED, index=True
    )

    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(UUIDMixin, TimestampMixin, Base):
    """Snapshots the listing's title/price at purchase time — later edits
    to the listing (or its deletion) must never rewrite order history."""

    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    listing_id: Mapped[str | None] = mapped_column(
        ForeignKey("listings.id", ondelete="SET NULL"), nullable=True
    )
    seller_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    price_credits: Mapped[int] = mapped_column(Integer)
    # Platform's cut in credits, snapshotted at sale time so later changes
    # to the (runtime-editable) platform fee never rewrite historical
    # revenue — see `platform_settings_service`.
    platform_fee_credits: Mapped[int] = mapped_column(Integer, default=0)
    is_refunded: Mapped[bool] = mapped_column(Boolean, default=False)
    # The buyer's own cloned copy, created during checkout.
    cloned_asset_id: Mapped[str | None] = mapped_column(
        ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )

    order: Mapped[Order] = relationship(back_populates="items")
