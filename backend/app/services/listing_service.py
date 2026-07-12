"""Listing persistence: browse/search, owner CRUD, and quota enforcement.

Only `status == ACTIVE` listings count against a seller's quota and appear
in public browse results — drafts and delisted items are free to keep
around. `SOLD` is set only by `checkout_service` (M3), never by this
module's `update()`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.db.models import (
    Job,
    Listing,
    ListingComment,
    ListingLike,
    ListingMedia,
    ListingStatus,
    User,
)
from app.services import wallet_service
from app.services.marketplace_errors import QuotaExceededError, RateLimitedError

_EAGER = (selectinload(Listing.source_asset), selectinload(Listing.cover_media))


def media_url(media_id: str) -> str:
    return f"{settings.api_v1_prefix}/marketplace/listings/media/{media_id}"


def cover_url(listing: Listing) -> str | None:
    return media_url(listing.cover_media_id) if listing.cover_media_id else None


def to_read(schema_cls, listing: Listing):
    """Validates `listing` into `schema_cls` and fills in the fields the ORM
    doesn't carry directly: the public preview URL/type, and the product's
    shape (kind/dimensions/duration) mirrored from the private source asset.
    Requires `listing.source_asset` (and `.cover_media`, if set) to already
    be loaded — see `_EAGER` in the query functions above."""
    data = schema_cls.model_validate(listing)
    data.cover_url = cover_url(listing)
    data.cover_content_type = (
        listing.cover_media.content_type if listing.cover_media else None
    )
    asset = listing.source_asset
    data.kind = asset.kind.value
    data.width = asset.width
    data.height = asset.height
    data.duration_seconds = asset.duration_seconds
    return data


_MUTABLE_FIELDS = (
    "title",
    "description",
    "category",
    "tags",
    "price_credits",
    "cover_media_id",
    "stock",
)


def _active_count(db: Session, seller_id: str) -> int:
    return (
        db.scalar(
            select(func.count()).where(
                Listing.seller_id == seller_id, Listing.status == ListingStatus.ACTIVE
            )
        )
        or 0
    )


def _ensure_quota(db: Session, seller: User) -> None:
    if seller.is_superuser:
        return
    wallet = wallet_service.get_or_create_wallet(db, seller.id)
    if _active_count(db, seller.id) >= wallet.listing_quota:
        raise QuotaExceededError(
            f"Your plan allows {wallet.listing_quota} active listing(s). "
            "Delist one or buy a plan with a higher quota."
        )


def _ensure_not_rate_limited(db: Session, seller: User) -> None:
    if seller.is_superuser:
        return
    cutoff = datetime.now(UTC) - timedelta(hours=1)
    recent = (
        db.scalar(
            select(func.count()).where(
                Listing.seller_id == seller.id, Listing.created_at >= cutoff
            )
        )
        or 0
    )
    if recent >= settings.marketplace_listing_rate_limit_per_hour:
        raise RateLimitedError(
            "You're creating listings too fast — try again in a bit."
        )


def create(db: Session, seller: User, data) -> Listing:
    _ensure_not_rate_limited(db, seller)
    status = ListingStatus(data.status) if data.status else ListingStatus.DRAFT
    if status == ListingStatus.ACTIVE:
        _ensure_quota(db, seller)

    listing = Listing(
        seller_id=seller.id,
        source_asset_id=data.source_asset_id,
        title=data.title,
        description=data.description,
        category=data.category or "other",
        tags=data.tags or [],
        price_credits=data.price_credits,
        stock=data.stock if data.stock is not None else 1,
        cover_media_id=data.cover_media_id,
        status=status,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def get_by_id(db: Session, listing_id: str) -> Listing | None:
    return db.scalar(select(Listing).where(Listing.id == listing_id).options(*_EAGER))


def get_for_owner(db: Session, seller_id: str, listing_id: str) -> Listing | None:
    listing = get_by_id(db, listing_id)
    if listing is None or listing.seller_id != seller_id:
        return None
    return listing


def update(db: Session, seller: User, listing: Listing, data) -> Listing:
    for field in _MUTABLE_FIELDS:
        value = getattr(data, field, None)
        if value is not None:
            setattr(listing, field, value)

    if data.status is not None:
        new_status = ListingStatus(data.status)
        if new_status == ListingStatus.SOLD:
            raise ValueError("Listings can't be manually set to 'sold'.")
        if (
            new_status == ListingStatus.ACTIVE
            and listing.status != ListingStatus.ACTIVE
        ):
            _ensure_quota(db, seller)
        listing.status = new_status

    db.commit()
    db.refresh(listing)
    return listing


def delete_listing(db: Session, listing: Listing) -> None:
    db.delete(listing)
    db.commit()


def list_active(
    db: Session,
    *,
    category: str | None = None,
    query: str | None = None,
    sort: str = "recent",
    limit: int = 24,
    offset: int = 0,
) -> tuple[list[Listing], int]:
    stmt = (
        select(Listing).where(Listing.status == ListingStatus.ACTIVE).options(*_EAGER)
    )
    if category and category != "all":
        stmt = stmt.where(Listing.category == category)
    if query:
        like = f"%{query}%"
        stmt = stmt.where(Listing.title.ilike(like) | Listing.description.ilike(like))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    if sort == "popular":
        stmt = stmt.order_by(Listing.like_count.desc(), Listing.created_at.desc())
    elif sort == "price_low":
        stmt = stmt.order_by(Listing.price_credits.asc())
    elif sort == "price_high":
        stmt = stmt.order_by(Listing.price_credits.desc())
    else:  # recent
        stmt = stmt.order_by(Listing.created_at.desc())

    items = list(db.scalars(stmt.limit(limit).offset(offset)))
    return items, total


def list_for_seller(db: Session, seller_id: str) -> list[Listing]:
    return list(
        db.scalars(
            select(Listing)
            .where(Listing.seller_id == seller_id)
            .options(*_EAGER)
            .order_by(Listing.updated_at.desc())
        )
    )


def list_for_moderation(
    db: Session,
    *,
    status: ListingStatus | None = None,
    seller_id: str | None = None,
    query: str | None = None,
    limit: int = 24,
    offset: int = 0,
) -> tuple[list[Listing], int]:
    stmt = select(Listing)
    if status is not None:
        stmt = stmt.where(Listing.status == status)
    if seller_id:
        stmt = stmt.where(Listing.seller_id == seller_id)
    if query:
        like = f"%{query}%"
        stmt = stmt.where(Listing.title.ilike(like) | Listing.description.ilike(like))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = (
        stmt.options(*_EAGER)
        .order_by(Listing.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = list(db.scalars(stmt))
    return items, total


def admin_delist(db: Session, listing: Listing) -> Listing:
    listing.status = ListingStatus.DELISTED
    db.commit()
    db.refresh(listing)
    return listing


def category_counts(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(Listing.category, func.count(Listing.id))
        .where(Listing.status == ListingStatus.ACTIVE)
        .group_by(Listing.category)
    ).all()
    return {cat: count for cat, count in rows}


# ------------------------------- media ---------------------------------- #
def create_media(
    db: Session, uploader_id: str, storage_key: str, content_type: str
) -> ListingMedia:
    media = ListingMedia(
        uploader_id=uploader_id, storage_key=storage_key, content_type=content_type
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def get_media(db: Session, media_id: str) -> ListingMedia | None:
    return db.get(ListingMedia, media_id)


# ----------------------------- engagement ------------------------------ #
def is_liked_by(db: Session, listing_id: str, user_id: str | None) -> bool:
    if not user_id:
        return False
    return (
        db.scalar(
            select(ListingLike.id).where(
                ListingLike.listing_id == listing_id, ListingLike.user_id == user_id
            )
        )
        is not None
    )


def set_like(db: Session, listing: Listing, user_id: str, liked: bool) -> Listing:
    exists = db.scalar(
        select(ListingLike).where(
            ListingLike.listing_id == listing.id, ListingLike.user_id == user_id
        )
    )
    if liked and exists is None:
        db.add(ListingLike(listing_id=listing.id, user_id=user_id))
    elif not liked and exists is not None:
        db.execute(
            delete(ListingLike).where(
                ListingLike.listing_id == listing.id, ListingLike.user_id == user_id
            )
        )
    db.flush()  # count the pending insert/delete under autoflush=False sessions
    listing.like_count = (
        db.scalar(
            select(func.count(ListingLike.id)).where(
                ListingLike.listing_id == listing.id
            )
        )
        or 0
    )
    db.commit()
    db.refresh(listing)
    return listing


def add_comment(
    db: Session, listing: Listing, author_id: str, body: str
) -> ListingComment:
    comment = ListingComment(
        listing_id=listing.id, author_id=author_id, body=body.strip()
    )
    db.add(comment)
    listing.comment_count = listing.comment_count + 1
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(
    db: Session, listing_id: str, *, include_hidden: bool = False
) -> list[ListingComment]:
    stmt = select(ListingComment).where(ListingComment.listing_id == listing_id)
    if not include_hidden:
        stmt = stmt.where(ListingComment.is_hidden.is_(False))
    return list(db.scalars(stmt.order_by(ListingComment.created_at.asc())))


def get_comment(db: Session, comment_id: str) -> ListingComment | None:
    return db.get(ListingComment, comment_id)


def delete_comment(db: Session, comment: ListingComment) -> None:
    listing = db.get(Listing, comment.listing_id)
    was_visible = not comment.is_hidden
    db.delete(comment)
    if listing is not None and was_visible:
        listing.comment_count = max(0, listing.comment_count - 1)
    db.commit()


def set_comment_hidden(
    db: Session, comment: ListingComment, hidden: bool
) -> ListingComment:
    """Admin soft-hide/unhide — the row stays, but it's excluded from public
    reads and from the listing's visible `comment_count`."""
    if comment.is_hidden == hidden:
        return comment
    listing = db.get(Listing, comment.listing_id)
    comment.is_hidden = hidden
    if listing is not None:
        delta = -1 if hidden else 1
        listing.comment_count = max(0, listing.comment_count + delta)
    db.commit()
    db.refresh(comment)
    return comment


def update_comment_body(
    db: Session, comment: ListingComment, body: str
) -> ListingComment:
    """Admin-only edit — regular users can't edit their own comments in
    this build, only delete them."""
    comment.body = body.strip()
    db.commit()
    db.refresh(comment)
    return comment


# --------------------------- generation reveal --------------------------- #
def generation_meta(db: Session, listing: Listing) -> dict | None:
    """The prompt/seed/model behind this listing's source asset, if it was
    AI-generated (not uploaded). Callers must gate this behind an
    ownership/purchase check — it is never safe to expose publicly."""
    job = db.scalar(select(Job).where(Job.result_asset_id == listing.source_asset_id))
    if job is None:
        return None
    params = job.params or {}
    meta = {
        k: params[k] for k in ("prompt", "seed", "model") if params.get(k) is not None
    }
    return meta or None
