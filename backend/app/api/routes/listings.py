"""Marketplace listings (M2): public browse/search, owner CRUD, quota
enforcement, and preview media. Cart/checkout land in M3."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status

from app.api.deps import CurrentUser, DbSession, OptionalUser
from app.db.models import Listing
from app.schemas.listing import (
    ListingCreate,
    ListingDetail,
    ListingListResponse,
    ListingMediaRead,
    ListingSummary,
    ListingUpdate,
    SellableAssetRead,
)
from app.services import asset_service, listing_service
from app.services.marketplace_errors import MarketplaceError
from app.storage import get_storage

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

# Listing previews can be short video clips, so the cap is higher than blog's.
MAX_MEDIA_BYTES = 50 * 1024 * 1024  # 50 MB


def _summary(listing: Listing) -> ListingSummary:
    return listing_service.with_cover_url(ListingSummary, listing)


def _detail(listing: Listing) -> ListingDetail:
    return listing_service.with_cover_url(ListingDetail, listing)


# --------------------------------------------------------------------------- #
# Public browse
# --------------------------------------------------------------------------- #
@router.get("/listings", response_model=ListingListResponse)
def list_listings(
    db: DbSession,
    category: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
    sort: Annotated[str, Query()] = "recent",
    limit: Annotated[int, Query(ge=1, le=48)] = 24,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ListingListResponse:
    items, total = listing_service.list_active(
        db, category=category, query=q, sort=sort, limit=limit, offset=offset
    )
    next_offset = offset + limit if offset + limit < total else None
    return ListingListResponse(
        items=[_summary(listing) for listing in items],
        total=total,
        next_offset=next_offset,
    )


@router.get("/listings/categories", response_model=dict[str, int])
def listing_category_counts(db: DbSession) -> dict[str, int]:
    return listing_service.category_counts(db)


@router.get("/me/listings", response_model=list[ListingSummary])
def my_listings(current_user: CurrentUser, db: DbSession) -> list[ListingSummary]:
    return [
        _summary(listing)
        for listing in listing_service.list_for_seller(db, current_user.id)
    ]


@router.get("/me/assets", response_model=list[SellableAssetRead])
def my_sellable_assets(
    current_user: CurrentUser, db: DbSession
) -> list[SellableAssetRead]:
    assets = asset_service.list_for_owner_across_projects(db, current_user.id)
    return [
        SellableAssetRead(
            id=a.id,
            name=a.name,
            kind=a.kind.value,
            content_type=a.content_type,
            content_url=asset_service.content_url(a.id),
            duration_seconds=a.duration_seconds,
            width=a.width,
            height=a.height,
        )
        for a in assets
        if a.kind.value in ("video", "image")
    ]


@router.get("/listings/{listing_id}", response_model=ListingDetail)
def get_listing(
    listing_id: str, db: DbSession, current_user: OptionalUser
) -> ListingDetail:
    listing = listing_service.get_by_id(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found.")
    # Non-active listings are visible only to their seller.
    if listing.status.value != "active" and (
        current_user is None or current_user.id != listing.seller_id
    ):
        raise HTTPException(status_code=404, detail="Listing not found.")
    return _detail(listing)


# --------------------------------------------------------------------------- #
# Seller CRUD
# --------------------------------------------------------------------------- #
def _owned_listing(db: DbSession, user_id: str, listing_id: str) -> Listing:
    listing = listing_service.get_for_owner(db, user_id, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found.")
    return listing


@router.post("/listings", response_model=ListingDetail, status_code=201)
def create_listing(
    data: ListingCreate, current_user: CurrentUser, db: DbSession
) -> ListingDetail:
    source_asset = asset_service.get_for_owner(
        db, current_user.id, data.source_asset_id
    )
    if source_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found.")
    try:
        listing = listing_service.create(db, current_user, data)
    except MarketplaceError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    return _detail(listing)


@router.patch("/listings/{listing_id}", response_model=ListingDetail)
def update_listing(
    listing_id: str, data: ListingUpdate, current_user: CurrentUser, db: DbSession
) -> ListingDetail:
    listing = _owned_listing(db, current_user.id, listing_id)
    try:
        listing = listing_service.update(db, current_user, listing, data)
    except MarketplaceError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _detail(listing)


@router.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: str, current_user: CurrentUser, db: DbSession
) -> Response:
    listing = _owned_listing(db, current_user.id, listing_id)
    if listing.status.value == "sold":
        raise HTTPException(
            status_code=409, detail="Sold listings can't be deleted — delist instead."
        )
    listing_service.delete_listing(db, listing)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------- #
# Preview media — public read, auth-gated upload.
# --------------------------------------------------------------------------- #
@router.post("/listings/media", response_model=ListingMediaRead, status_code=201)
async def upload_listing_media(
    current_user: CurrentUser,
    db: DbSession,
    file: Annotated[UploadFile, File()],
) -> ListingMediaRead:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(data) > MAX_MEDIA_BYTES:
        raise HTTPException(status_code=413, detail="Preview too large (max 50MB).")
    content_type = file.content_type or "application/octet-stream"
    if not (content_type.startswith("image/") or content_type.startswith("video/")):
        raise HTTPException(
            status_code=422, detail="Only image or video previews are allowed."
        )

    key = f"marketplace/{current_user.id}/{uuid.uuid4()}-{file.filename or 'upload'}"
    get_storage().put(key, data, content_type)
    media = listing_service.create_media(db, current_user.id, key, content_type)
    return ListingMediaRead(id=media.id, url=listing_service.media_url(media.id))


@router.get("/listings/media/{media_id}")
def get_listing_media(media_id: str, db: DbSession) -> Response:
    media = listing_service.get_media(db, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found.")
    try:
        body = get_storage().get(media.storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Media bytes missing.") from exc
    return Response(
        content=body,
        media_type=media.content_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
