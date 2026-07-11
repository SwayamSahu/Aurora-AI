from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status

from app.api.deps import CurrentUser, DbSession, OptionalUser
from app.core.config import settings
from app.db.models import BlogComment, BlogPost
from app.schemas.blog import (
    BlogCommentCreate,
    BlogCommentRead,
    BlogLikeToggle,
    BlogListResponse,
    BlogMediaRead,
    BlogPostCreate,
    BlogPostDetail,
    BlogPostSummary,
    BlogPostUpdate,
)
from app.services import blog_service
from app.storage import get_storage

router = APIRouter(prefix="/blog", tags=["blog"])

# Inline/cover images are capped to keep memory bounded.
MAX_MEDIA_BYTES = 20 * 1024 * 1024  # 20 MB


def _media_url(media_id: str) -> str:
    return f"{settings.api_v1_prefix}/blog/media/{media_id}"


def _cover_url(post: BlogPost) -> str | None:
    return _media_url(post.cover_media_id) if post.cover_media_id else None


def _summary(post: BlogPost) -> BlogPostSummary:
    data = BlogPostSummary.model_validate(post)
    data.cover_url = _cover_url(post)
    return data


# --------------------------------------------------------------------------- #
# Public reads
# --------------------------------------------------------------------------- #
@router.get("/posts", response_model=BlogListResponse)
def list_posts(
    db: DbSession,
    category: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
    sort: Annotated[str, Query()] = "recent",
    limit: Annotated[int, Query(ge=1, le=48)] = 24,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> BlogListResponse:
    posts, total = blog_service.list_published(
        db, category=category, query=q, sort=sort, limit=limit, offset=offset
    )
    next_offset = offset + limit if offset + limit < total else None
    return BlogListResponse(
        items=[_summary(p) for p in posts], total=total, next_offset=next_offset
    )


@router.get("/featured", response_model=list[BlogPostSummary])
def featured_posts(db: DbSession) -> list[BlogPostSummary]:
    return [_summary(p) for p in blog_service.featured(db)]


@router.get("/categories", response_model=dict[str, int])
def category_counts(db: DbSession) -> dict[str, int]:
    return blog_service.category_counts(db)


@router.get("/me/posts", response_model=list[BlogPostSummary])
def my_posts(current_user: CurrentUser, db: DbSession) -> list[BlogPostSummary]:
    return [_summary(p) for p in blog_service.list_for_author(db, current_user.id)]


@router.get("/posts/{slug}", response_model=BlogPostDetail)
def get_post(slug: str, db: DbSession, current_user: OptionalUser) -> BlogPostDetail:
    post = blog_service.get_by_slug(db, slug)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    # Drafts are visible only to their author.
    if post.status.value == "draft" and (
        current_user is None or current_user.id != post.author_id
    ):
        raise HTTPException(status_code=404, detail="Post not found.")

    data = BlogPostDetail.model_validate(post)
    data.cover_url = _cover_url(post)
    data.liked_by_me = blog_service.is_liked_by(
        db, post.id, current_user.id if current_user else None
    )
    return data


@router.get("/posts/{slug}/comments", response_model=list[BlogCommentRead])
def get_comments(slug: str, db: DbSession) -> list[BlogCommentRead]:
    post = blog_service.get_by_slug(db, slug)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    return [
        BlogCommentRead.model_validate(c)
        for c in blog_service.list_comments(db, post.id)
    ]


# --------------------------------------------------------------------------- #
# Authoring (auth-gated, author-only mutations)
# --------------------------------------------------------------------------- #
def _owned_post(db: DbSession, user_id: str, post_id: str) -> BlogPost:
    post = blog_service.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.author_id != user_id:
        raise HTTPException(status_code=403, detail="Not your post.")
    return post


@router.post("/posts", response_model=BlogPostDetail, status_code=201)
def create_post(
    data: BlogPostCreate, current_user: CurrentUser, db: DbSession
) -> BlogPostDetail:
    post = blog_service.create(db, current_user.id, data)
    out = BlogPostDetail.model_validate(post)
    out.cover_url = _cover_url(post)
    return out


@router.patch("/posts/{post_id}", response_model=BlogPostDetail)
def update_post(
    post_id: str,
    data: BlogPostUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> BlogPostDetail:
    post = _owned_post(db, current_user.id, post_id)
    post = blog_service.update(db, post, data)
    out = BlogPostDetail.model_validate(post)
    out.cover_url = _cover_url(post)
    out.liked_by_me = blog_service.is_liked_by(db, post.id, current_user.id)
    return out


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: str, current_user: CurrentUser, db: DbSession) -> Response:
    post = _owned_post(db, current_user.id, post_id)
    blog_service.delete_post(db, post)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------- #
# Engagement
# --------------------------------------------------------------------------- #
@router.post("/posts/{post_id}/like", response_model=BlogPostDetail)
def toggle_like(
    post_id: str,
    data: BlogLikeToggle,
    current_user: CurrentUser,
    db: DbSession,
) -> BlogPostDetail:
    post = blog_service.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    post = blog_service.set_like(db, post, current_user.id, data.liked)
    out = BlogPostDetail.model_validate(post)
    out.cover_url = _cover_url(post)
    out.liked_by_me = data.liked
    return out


@router.post(
    "/posts/{post_id}/comments", response_model=BlogCommentRead, status_code=201
)
def create_comment(
    post_id: str,
    data: BlogCommentCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> BlogCommentRead:
    post = blog_service.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    comment = blog_service.add_comment(db, post, current_user.id, data.body)
    return BlogCommentRead.model_validate(comment)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: str, current_user: CurrentUser, db: DbSession
) -> Response:
    comment: BlogComment | None = blog_service.get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your comment.")
    blog_service.delete_comment(db, comment)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------- #
# Media (cover + inline editor images) — public read, auth-gated upload.
# Deliberately NOT the project-scoped /assets pipeline: blog reads (and thus
# blog images) must be visible to anonymous readers.
# --------------------------------------------------------------------------- #
@router.post("/media", response_model=BlogMediaRead, status_code=201)
async def upload_media(
    current_user: CurrentUser,
    db: DbSession,
    file: Annotated[UploadFile, File()],
) -> BlogMediaRead:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(data) > MAX_MEDIA_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 20MB).")
    content_type = file.content_type or "application/octet-stream"
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=422, detail="Only image uploads are allowed.")

    # A uuid prefix disambiguates concurrent uploads with the same filename.
    key = f"blog/{current_user.id}/{uuid.uuid4()}-{file.filename or 'upload'}"
    get_storage().put(key, data, content_type)
    media = blog_service.create_media(db, current_user.id, key, content_type)
    return BlogMediaRead(id=media.id, url=_media_url(media.id))


@router.get("/media/{media_id}")
def get_media(media_id: str, db: DbSession) -> Response:
    media = blog_service.get_media(db, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found.")
    try:
        body = get_storage().get(media.storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Media bytes missing.") from exc
    return Response(
        content=body,
        media_type=media.content_type,
        # Public + long-lived: blog media is immutable once uploaded.
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
