"""Revenue analytics for the admin dashboard. Reads only — aggregates over
`orders`/`order_items`, using each item's `platform_fee_credits` snapshot so
numbers stay accurate even after the platform fee is edited later."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db.models import Order, OrderItem
from app.services import platform_settings_service


def get_revenue_summary(db: Session, *, days: int = 30) -> dict:
    total_orders = db.scalar(select(func.count(Order.id))) or 0
    active_buyers = db.scalar(select(func.count(func.distinct(Order.buyer_id)))) or 0
    active_sellers = (
        db.scalar(select(func.count(func.distinct(OrderItem.seller_id)))) or 0
    )

    total_gmv = db.scalar(select(func.coalesce(func.sum(OrderItem.price_credits), 0))) or 0
    total_refunded = (
        db.scalar(
            select(func.coalesce(func.sum(OrderItem.price_credits), 0)).where(
                OrderItem.is_refunded.is_(True)
            )
        )
        or 0
    )
    total_revenue = (
        db.scalar(
            select(func.coalesce(func.sum(OrderItem.platform_fee_credits), 0)).where(
                OrderItem.is_refunded.is_(False)
            )
        )
        or 0
    )

    since = datetime.now(UTC) - timedelta(days=days)
    day = func.date(OrderItem.created_at)
    rows = db.execute(
        select(
            day.label("day"),
            func.coalesce(
                func.sum(
                    case(
                        (OrderItem.is_refunded.is_(False), OrderItem.platform_fee_credits),
                        else_=0,
                    )
                ),
                0,
            ).label("revenue"),
            func.coalesce(func.sum(OrderItem.price_credits), 0).label("gmv"),
            func.count(func.distinct(OrderItem.order_id)).label("orders"),
        )
        .where(OrderItem.created_at >= since)
        .group_by(day)
        .order_by(day)
    ).all()

    daily = [
        {
            "date": str(row.day),
            "revenue_credits": int(row.revenue),
            "gmv_credits": int(row.gmv),
            "order_count": int(row.orders),
        }
        for row in rows
    ]

    return {
        "total_revenue_credits": int(total_revenue),
        "total_gmv_credits": int(total_gmv),
        "total_orders": int(total_orders),
        "total_refunded_credits": int(total_refunded),
        "active_sellers": int(active_sellers),
        "active_buyers": int(active_buyers),
        "current_platform_fee": platform_settings_service.get_platform_fee(db),
        "daily": daily,
    }
