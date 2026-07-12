"""Marketplace listings (M2): public browse/search, owner CRUD, quota
enforcement, and preview media. Cart/checkout (M3) and real engagement —
likes/comments, conditional generation-prompt reveal (M6)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status

from app.api.deps import CurrentUser, DbSession, OptionalUser
from app.db.models import Listing, ListingComment, User
from app.schemas.listing import (
    ListingCommentCreate,
    ListingCommentRead,
    ListingCreate,
    ListingDetail,
    ListingLikeToggle,
    ListingListResponse,
    ListingMediaRead,
    ListingSummary,
    ListingUpdate,
    SellableAssetRead,
)
from app.services import asset_service, audit_service, listing_service, order_service
from app.services.marketplace_errors import MarketplaceError, RateLimitedError
from app.storage import get_storage

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

# Listing previews can be short video clips, so the cap is higher than blog's.
MAX_MEDIA_BYTES = 50 * 1024 * 1024  # 50 MB


def _summary(listing: Listing) -> ListingSummary:
    return listing_service.to_read(ListingSummary, listing)


def _detail(listing: Listing) -> ListingDetail:
    return listing_service.to_read(ListingDetail, listing)


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

    is_seller = current_user is not None and current_user.id == listing.seller_id
    is_buyer = current_user is not None and order_service.buyer_has_purchased(
        db, current_user.id, listing_id
    )
    is_moderator = current_user is not None and current_user.is_moderator
    # Non-active listings are visible only to their seller, a buyer who
    # purchased them (so "sold" doesn't 404 the item you just bought), or
    # an admin moderating it.
    if listing.status.value != "active" and not (is_seller or is_buyer or is_moderator):
        raise HTTPException(status_code=404, detail="Listing not found.")

    out = _detail(listing)
    out.liked_by_me = listing_service.is_liked_by(
        db, listing.id, current_user.id if current_user else None
    )
    # The generation prompt/seed is the seller's private data pre-purchase
    # (it's effectively the "recipe") — only the seller or a buyer who
    # already paid for it gets to see it.
    if is_seller or is_buyer:
        out.generation = listing_service.generation_meta(db, listing)
    return out


# --------------------------------------------------------------------------- #
# Seller CRUD
# --------------------------------------------------------------------------- #
def _owned_listing(db: DbSession, current_user: User, listing_id: str) -> Listing:
    listing = listing_service.get_by_id(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found.")
    # 404 (not 403) for a non-owner, non-admin — matches the original M2
    # contract of not revealing that a listing exists to someone who can't
    # see it, rather than confirming its existence via a 403.
    if listing.seller_id != current_user.id and not current_user.is_moderator:
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
    except RateLimitedError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except MarketplaceError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    return _detail(listing)


@router.patch("/listings/{listing_id}", response_model=ListingDetail)
def update_listing(
    listing_id: str, data: ListingUpdate, current_user: CurrentUser, db: DbSession
) -> ListingDetail:
    listing = _owned_listing(db, current_user, listing_id)
    acting_as_mod = listing.seller_id != current_user.id
    try:
        listing = listing_service.update(db, current_user, listing, data)
    except MarketplaceError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if acting_as_mod:
        audit_service.record(
            db,
            actor_id=current_user.id,
            action="listing.update",
            target_type="listing",
            target_id=listing.id,
            metadata={"title": listing.title, "seller_id": listing.seller_id},
        )
    return _detail(listing)


@router.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: str, current_user: CurrentUser, db: DbSession
) -> Response:
    listing = _owned_listing(db, current_user, listing_id)
    if listing.status.value == "sold":
        raise HTTPException(
            status_code=409, detail="Sold listings can't be deleted — delist instead."
        )
    acting_as_mod = listing.seller_id != current_user.id
    snapshot = {"title": listing.title, "seller_id": listing.seller_id}
    lid = listing.id
    listing_service.delete_listing(db, listing)
    if acting_as_mod:
        audit_service.record(
            db,
            actor_id=current_user.id,
            action="listing.delete",
            target_type="listing",
            target_id=lid,
            metadata=snapshot,
        )
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


# --------------------------------------------------------------------------- #
# Engagement — likes + comments
# --------------------------------------------------------------------------- #
@router.post("/listings/{listing_id}/like", response_model=ListingDetail)
def toggle_like(
    listing_id: str,
    data: ListingLikeToggle,
    current_user: CurrentUser,
    db: DbSession,
) -> ListingDetail:
    listing = listing_service.get_by_id(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found.")
    listing = listing_service.set_like(db, listing, current_user.id, data.liked)
    out = _detail(listing)
    out.liked_by_me = data.liked
    return out


@router.get("/listings/{listing_id}/comments", response_model=list[ListingCommentRead])
def get_comments(listing_id: str, db: DbSession) -> list[ListingCommentRead]:
    listing = listing_service.get_by_id(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found.")
    return [
        ListingCommentRead.model_validate(c)
        for c in listing_service.list_comments(db, listing.id)
    ]


@router.post(
    "/listings/{listing_id}/comments",
    response_model=ListingCommentRead,
    status_code=201,
)
def create_comment(
    listing_id: str,
    data: ListingCommentCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ListingCommentRead:
    listing = listing_service.get_by_id(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found.")
    comment = listing_service.add_comment(db, listing, current_user.id, data.body)
    return ListingCommentRead.model_validate(comment)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: str, current_user: CurrentUser, db: DbSession
) -> Response:
    comment: ListingComment | None = listing_service.get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.author_id != current_user.id and not current_user.is_moderator:
        raise HTTPException(status_code=403, detail="Not your comment.")
    acting_as_mod = comment.author_id != current_user.id
    cid, cauthor = comment.id, comment.author_id
    listing_service.delete_comment(db, comment)
    if acting_as_mod:
        audit_service.record(
            db,
            actor_id=current_user.id,
            action="listing_comment.delete",
            target_type="listing_comment",
            target_id=cid,
            metadata={"author_id": cauthor},
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
