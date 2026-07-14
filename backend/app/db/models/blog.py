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


class BlogStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class BlogPost(UUIDMixin, TimestampMixin, Base):
    """A user-authored blog post.

    Body is stored twice: `body_html` (sanitized, for fast rendering) and
    `body_json` (the editor document, for lossless re-editing).
    """

    __tablename__ = "blog_posts"

    author_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str] = mapped_column(String(280), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(280))
    subtitle: Mapped[str | None] = mapped_column(String(400), nullable=True)
    excerpt: Mapped[str | None] = mapped_column(String(500), nullable=True)

    category: Mapped[str] = mapped_column(String(60), index=True, default="tutorials")
    tags: Mapped[list] = mapped_column(JSON, default=list)

    body_html: Mapped[str] = mapped_column(Text, default="")
    body_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Blog media is its own public-servable table (not the project-scoped
    # `assets` table, which requires auth and ownership to read — incompatible
    # with a public blog).
    cover_media_id: Mapped[str | None] = mapped_column(
        ForeignKey("blog_media.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[BlogStatus] = mapped_column(
        Enum(BlogStatus), default=BlogStatus.DRAFT, index=True
    )
    read_minutes: Mapped[int] = mapped_column(Integer, default=1)
    # Denormalized engagement counters (kept in sync by the service).
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)

    author: Mapped[User] = relationship()  # noqa: F821
    likes: Mapped[list[BlogLike]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    comments: Mapped[list[BlogComment]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class BlogMedia(UUIDMixin, TimestampMixin, Base):
    """A publicly-servable image uploaded for a blog post (cover or inline).

    Deliberately separate from the project-scoped `assets` table: blog reads
    are public, so blog media must be servable without auth/ownership checks.
    """

    __tablename__ = "blog_media"

    uploader_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    storage_key: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(120))
    # Set by the automated content-safety scan at upload time — see
    # `content_safety_service`. Flagged media stays servable (never blocks
    # the uploader) but auto-creates a moderator report for review.
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_categories: Mapped[list] = mapped_column(JSON, default=list)


class BlogLike(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "blog_likes"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_blog_like_post_user"),
    )

    post_id: Mapped[str] = mapped_column(
        ForeignKey("blog_posts.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    post: Mapped[BlogPost] = relationship(back_populates="likes")


class BlogComment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "blog_comments"

    post_id: Mapped[str] = mapped_column(
        ForeignKey("blog_posts.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text)
    # Admin-moderated soft-hide — excluded from the public comment list and
    # from `BlogPost.comment_count`, but not deleted (see blog_service).
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)

    post: Mapped[BlogPost] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()  # noqa: F821
