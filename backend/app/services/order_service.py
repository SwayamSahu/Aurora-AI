"""Read-side order history: buyer purchase history and seller sales history."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Order, OrderItem


def list_for_buyer(db: Session, buyer_id: str) -> list[Order]:
    return list(
        db.scalars(
            select(Order)
            .where(Order.buyer_id == buyer_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
        )
    )


def list_sales_for_seller(db: Session, seller_id: str) -> list[OrderItem]:
    return list(
        db.scalars(
            select(OrderItem)
            .where(OrderItem.seller_id == seller_id)
            .options(selectinload(OrderItem.order))
            .order_by(OrderItem.created_at.desc())
        )
    )
