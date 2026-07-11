from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
