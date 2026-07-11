"""Blog persistence: posts (author-scoped writes), likes, comments.

Bodies are sanitized on write. Slugs are unique and derived from the title.
Read-time and excerpt are computed from the sanitized body.
"""

from __future__ import annotations

import re
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import BlogComment, BlogLike, BlogMedia, BlogPost
from app.db.models.blog import BlogStatus
from app.services.html_sanitize import html_to_text, sanitize_html

_WORDS_PER_MINUTE = 220
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def media_url(media_id: str) -> str:
    return f"{settings.api_v1_prefix}/blog/media/{media_id}"


def cover_url(post: BlogPost) -> str | None:
    return media_url(post.cover_media_id) if post.cover_media_id else None


def to_read(schema_cls, post: BlogPost):
    """Validates `post` into `schema_cls` and fills in `cover_url`, which
    the ORM doesn't carry directly (used for both summary and detail
    responses, in `blog.py` and `admin_blog.py`)."""
    data = schema_cls.model_validate(post)
    data.cover_url = cover_url(post)
    return data


def slugify(title: str) -> str:
    base = _SLUG_RE.sub("-", title.strip().lower()).strip("-")
    return base or "post"


def _unique_slug(db: Session, title: str, exclude_id: str | None = None) -> str:
    base = slugify(title)[:200]
    slug = base
    n = 2
    while True:
        stmt = select(BlogPost.id).where(BlogPost.slug == slug)
        if exclude_id:
            stmt = stmt.where(BlogPost.id != exclude_id)
        if db.scalar(stmt) is None:
            return slug
        slug = f"{base}-{n}"
        n += 1


def _read_minutes(body_html: str) -> int:
    words = len(html_to_text(body_html).split())
    return max(1, round(words / _WORDS_PER_MINUTE))


def _auto_excerpt(body_html: str, limit: int = 200) -> str:
    text = html_to_text(body_html)
    return text[:limit].rstrip() + ("…" if len(text) > limit else "")


def create(db: Session, author_id: str, data) -> BlogPost:
    body_html = sanitize_html(data.body_html or "")
    post = BlogPost(
        author_id=author_id,
        slug=_unique_slug(db, data.title),
        title=data.title,
        subtitle=data.subtitle,
        excerpt=(data.excerpt or _auto_excerpt(body_html))
        if body_html
        else data.excerpt,
        category=data.category or "tutorials",
        tags=data.tags or [],
        body_html=body_html,
        body_json=data.body_json or {},
        cover_media_id=data.cover_media_id,
        status=BlogStatus(data.status) if data.status else BlogStatus.DRAFT,
        read_minutes=_read_minutes(body_html),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_by_id(db: Session, post_id: str) -> BlogPost | None:
    return db.get(BlogPost, post_id)


def get_by_slug(db: Session, slug: str) -> BlogPost | None:
    return db.scalar(select(BlogPost).where(BlogPost.slug == slug))


def update(db: Session, post: BlogPost, data) -> BlogPost:
    if data.title is not None and data.title != post.title:
        post.title = data.title
        post.slug = _unique_slug(db, data.title, exclude_id=post.id)
    if data.subtitle is not None:
        post.subtitle = data.subtitle
    if data.category is not None:
        post.category = data.category
    if data.tags is not None:
        post.tags = data.tags
    if data.cover_media_id is not None:
        post.cover_media_id = data.cover_media_id
    if data.body_html is not None:
        post.body_html = sanitize_html(data.body_html)
        post.read_minutes = _read_minutes(post.body_html)
        if data.excerpt is None:
            post.excerpt = _auto_excerpt(post.body_html)
    if data.body_json is not None:
        post.body_json = data.body_json
    if data.excerpt is not None:
        post.excerpt = data.excerpt
    if data.status is not None:
        post.status = BlogStatus(data.status)
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post: BlogPost) -> None:
    db.delete(post)
    db.commit()


def list_published(
    db: Session,
    *,
    category: str | None = None,
    query: str | None = None,
    sort: str = "recent",
    limit: int = 24,
    offset: int = 0,
) -> tuple[list[BlogPost], int]:
    stmt = select(BlogPost).where(BlogPost.status == BlogStatus.PUBLISHED)
    if category and category != "all":
        stmt = stmt.where(BlogPost.category == category)
    if query:
        like = f"%{query}%"
        stmt = stmt.where(BlogPost.title.ilike(like) | BlogPost.excerpt.ilike(like))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    if sort == "popular":
        stmt = stmt.order_by(BlogPost.like_count.desc(), BlogPost.created_at.desc())
    else:  # recent
        stmt = stmt.order_by(BlogPost.updated_at.desc())

    posts = list(db.scalars(stmt.limit(limit).offset(offset)))
    return posts, total


def list_for_author(db: Session, author_id: str) -> list[BlogPost]:
    return list(
        db.scalars(
            select(BlogPost)
            .where(BlogPost.author_id == author_id)
            .order_by(BlogPost.updated_at.desc())
        )
    )


def list_for_admin(
    db: Session,
    *,
    status: BlogStatus | None = None,
    author_id: str | None = None,
    query: str | None = None,
    limit: int = 24,
    offset: int = 0,
) -> tuple[list[BlogPost], int]:
    """All posts regardless of author/status — for the moderation dashboard."""
    stmt = select(BlogPost)
    if status is not None:
        stmt = stmt.where(BlogPost.status == status)
    if author_id:
        stmt = stmt.where(BlogPost.author_id == author_id)
    if query:
        like = f"%{query}%"
        stmt = stmt.where(BlogPost.title.ilike(like) | BlogPost.excerpt.ilike(like))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    posts = list(
        db.scalars(
            stmt.order_by(BlogPost.updated_at.desc()).limit(limit).offset(offset)
        )
    )
    return posts, total


def featured(db: Session, limit: int = 4) -> list[BlogPost]:
    return list(
        db.scalars(
            select(BlogPost)
            .where(BlogPost.status == BlogStatus.PUBLISHED)
            .order_by(BlogPost.like_count.desc(), BlogPost.created_at.desc())
            .limit(limit)
        )
    )


def category_counts(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(BlogPost.category, func.count(BlogPost.id))
        .where(BlogPost.status == BlogStatus.PUBLISHED)
        .group_by(BlogPost.category)
    ).all()
    return {cat: count for cat, count in rows}


# ----------------------------- engagement ------------------------------ #
def is_liked_by(db: Session, post_id: str, user_id: str | None) -> bool:
    if not user_id:
        return False
    return (
        db.scalar(
            select(BlogLike.id).where(
                BlogLike.post_id == post_id, BlogLike.user_id == user_id
            )
        )
        is not None
    )


def set_like(db: Session, post: BlogPost, user_id: str, liked: bool) -> BlogPost:
    exists = db.scalar(
        select(BlogLike).where(BlogLike.post_id == post.id, BlogLike.user_id == user_id)
    )
    if liked and exists is None:
        db.add(BlogLike(id=str(uuid.uuid4()), post_id=post.id, user_id=user_id))
    elif not liked and exists is not None:
        db.execute(
            delete(BlogLike).where(
                BlogLike.post_id == post.id, BlogLike.user_id == user_id
            )
        )
    # Flush so the pending insert/delete is counted even when the session has
    # autoflush disabled (as the test session does).
    db.flush()
    post.like_count = (
        db.scalar(select(func.count(BlogLike.id)).where(BlogLike.post_id == post.id))
        or 0
    )
    db.commit()
    db.refresh(post)
    return post


def add_comment(db: Session, post: BlogPost, author_id: str, body: str) -> BlogComment:
    comment = BlogComment(post_id=post.id, author_id=author_id, body=body.strip())
    db.add(comment)
    post.comment_count = post.comment_count + 1
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(
    db: Session, post_id: str, *, include_hidden: bool = False
) -> list[BlogComment]:
    stmt = select(BlogComment).where(BlogComment.post_id == post_id)
    if not include_hidden:
        stmt = stmt.where(BlogComment.is_hidden.is_(False))
    return list(db.scalars(stmt.order_by(BlogComment.created_at.asc())))


def get_comment(db: Session, comment_id: str) -> BlogComment | None:
    return db.get(BlogComment, comment_id)


def delete_comment(db: Session, comment: BlogComment) -> None:
    post = db.get(BlogPost, comment.post_id)
    was_visible = not comment.is_hidden
    db.delete(comment)
    if post is not None and was_visible:
        post.comment_count = max(0, post.comment_count - 1)
    db.commit()


def set_comment_hidden(db: Session, comment: BlogComment, hidden: bool) -> BlogComment:
    """Admin soft-hide/unhide — the row stays, but it's excluded from public
    reads and from the post's visible `comment_count`."""
    if comment.is_hidden == hidden:
        return comment
    post = db.get(BlogPost, comment.post_id)
    comment.is_hidden = hidden
    if post is not None:
        delta = -1 if hidden else 1
        post.comment_count = max(0, post.comment_count + delta)
    db.commit()
    db.refresh(comment)
    return comment


def update_comment_body(db: Session, comment: BlogComment, body: str) -> BlogComment:
    """Admin-only edit (e.g. redacting something) — regular users can't
    edit their own comments in this build, only delete them."""
    comment.body = body.strip()
    db.commit()
    db.refresh(comment)
    return comment


# ------------------------------- media ---------------------------------- #
def create_media(
    db: Session, uploader_id: str, storage_key: str, content_type: str
) -> BlogMedia:
    media = BlogMedia(
        uploader_id=uploader_id, storage_key=storage_key, content_type=content_type
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def get_media(db: Session, media_id: str) -> BlogMedia | None:
    return db.get(BlogMedia, media_id)
