from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CreditPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    price_cents: int
    credits_granted: int
    listing_quota: int


class PlanPurchaseCreate(BaseModel):
    plan_id: str


class PlanPurchaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    plan_id: str
    status: Literal["pending", "paid", "failed"]
    price_cents: int
    credits_granted: int
    created_at: datetime


class WalletRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    balance_credits: int
    listing_quota: int
    active_plan_id: str | None


class CreditTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    amount: int
    balance_after: int
    note: str | None
    created_at: datetime


class WalletHistoryResponse(BaseModel):
    items: list[CreditTransactionRead]
    total: int
    next_offset: int | None = None
