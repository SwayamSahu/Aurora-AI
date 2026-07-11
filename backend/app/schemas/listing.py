from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ListingSeller(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str | None = None


class ListingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    price_credits: int = Field(gt=0)
    stock: int | None = Field(default=None, ge=1)
    source_asset_id: str
    cover_media_id: str | None = None
    status: Literal["draft", "active"] | None = None


class ListingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    price_credits: int | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=1)
    cover_media_id: str | None = None
    status: Literal["draft", "active", "delisted"] | None = None


class ListingMediaRead(BaseModel):
    id: str
    url: str


class ListingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    category: str
    tags: list[str]
    price_credits: int
    stock: int
    status: str
    like_count: int
    comment_count: int
    cover_media_id: str | None
    cover_url: str | None = None
    seller: ListingSeller
    created_at: datetime
    updated_at: datetime


class ListingDetail(ListingSummary):
    description: str | None


class ListingListResponse(BaseModel):
    items: list[ListingSummary]
    total: int
    next_offset: int | None = None


class SellableAssetRead(BaseModel):
    id: str
    name: str
    kind: str
    content_type: str
    content_url: str
    duration_seconds: float | None
    width: int | None
    height: int | None
