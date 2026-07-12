from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.listing import ListingSummary


class CartItemAdd(BaseModel):
    listing_id: str


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    listing: ListingSummary
    created_at: datetime


class CartRead(BaseModel):
    items: list[CartItemRead]
    total_credits: int


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    listing_id: str | None
    seller_id: str
    title: str
    price_credits: int
    is_refunded: bool
    cloned_asset_id: str | None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    total_credits: int
    status: str
    items: list[OrderItemRead]
    created_at: datetime


class SaleRead(BaseModel):
    """A single sold item, from the seller's point of view."""

    id: str
    order_id: str
    title: str
    price_credits: int
    buyer_id: str
    created_at: datetime
