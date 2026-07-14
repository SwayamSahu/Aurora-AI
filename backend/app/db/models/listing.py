"""Marketplace listings (M2). A listing sells access to a clone of one of
the seller's own private `Asset`s — see `checkout_service` (M3) for the
clone-on-purchase mechanism. Likes/comments (M6) are their own tables
(`ListingLike`/`ListingComment`), same pattern as blog's.
"""

from __future__ import annotations

import enum

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDMixin


class ListingStatus(str, enum.Enum):
    DRAFT = "draft"  # not publicly visible, doesn't count against quota
    ACTIVE = "active"  # publicly browsable/purchasable, counts against quota
    SOLD = "sold"  # stock hit zero — system-set only, not user-settable
    DELISTED = "delisted"  # seller pulled it; doesn't count against quota


class Listing(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "listings"

    seller_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # RESTRICT (not CASCADE): a seller must delist before deleting the
    # underlying asset, so a sold listing's clone-on-purchase source can't
    # silently vanish out from under order history.
    source_asset_id: Mapped[str] = mapped_column(
        ForeignKey("assets.id", ondelete="RESTRICT")
    )

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(60), index=True, default="other")
    tags: Mapped[list] = mapped_column(JSON, default=list)

    price_credits: Mapped[int] = mapped_column(Integer)
    # Units available. 1 = a unique one-of-a-kind sale; >1 = a reusable
    # template/prompt that can be bought by many buyers.
    stock: Mapped[int] = mapped_column(Integer, default=1)

    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus), default=ListingStatus.DRAFT, index=True
    )

    cover_media_id: Mapped[str | None] = mapped_column(
        ForeignKey("listing_media.id", ondelete="SET NULL"), nullable=True
    )

    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)

    seller: Mapped[User] = relationship()  # noqa: F821
    source_asset: Mapped[Asset] = relationship()  # noqa: F821
    cover_media: Mapped[ListingMedia | None] = relationship()


class ListingMedia(UUIDMixin, TimestampMixin, Base):
    """A publicly-servable preview (poster image or watermarked preview
    clip) for a listing. Same rationale as `BlogMedia`: `assets` requires
    auth+ownership to read, which is incompatible with a public storefront."""

    __tablename__ = "listing_media"

    uploader_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    storage_key: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(120))
    # See `BlogMedia.is_flagged` — same automated content-safety scan.
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_categories: Mapped[list] = mapped_column(JSON, default=list)


class ListingLike(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "listing_likes"
    __table_args__ = (
        UniqueConstraint("listing_id", "user_id", name="uq_listing_like_listing_user"),
    )

    listing_id: Mapped[str] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )


class ListingComment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "listing_comments"

    listing_id: Mapped[str] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text)
    # Admin-moderated soft-hide — excluded from the public comment list and
    # from `Listing.comment_count`, but not deleted (see listing_service).
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)

    author: Mapped[User] = relationship()  # noqa: F821
