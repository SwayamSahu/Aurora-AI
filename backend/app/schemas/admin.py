from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.blog import BlogPostSummary
from app.schemas.listing import ListingSummary


class AdminPlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    price_cents: int = Field(ge=0)
    credits_granted: int = Field(ge=0)
    listing_quota: int = Field(ge=0)
    is_active: bool = True
    sort_order: int = 0


class AdminPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    price_cents: int | None = Field(default=None, ge=0)
    credits_granted: int | None = Field(default=None, ge=0)
    listing_quota: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    sort_order: int | None = None


class AdminPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    price_cents: int
    credits_granted: int
    listing_quota: int
    is_active: bool
    sort_order: int


class WalletAdjustRequest(BaseModel):
    # Positive credits the wallet, negative debits it.
    amount: int
    note: str = Field(min_length=1, max_length=280)

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("amount must not be zero.")
        return value


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    created_at: datetime


class AdminUserListResponse(BaseModel):
    items: list[AdminUserRead]
    total: int
    next_offset: int | None = None


class AdminUserDetail(AdminUserRead):
    wallet_balance: int
    listing_quota: int
    post_count: int
    listing_count: int
    order_count: int
    sales_count: int
    recent_posts: list[BlogPostSummary]
    recent_listings: list[ListingSummary]


class AdminUserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def role_is_valid(cls, value: str | None) -> str | None:
        if value is not None and value not in ("user", "moderator", "admin"):
            raise ValueError("role must be one of user, moderator, admin.")
        return value
