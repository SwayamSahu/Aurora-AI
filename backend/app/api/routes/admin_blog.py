"""Blog admin console: moderation dashboard (all posts/authors/statuses)
and comment moderation. Post/comment CRUD itself goes through the existing
author-scoped routes in `blog.py`, which now bypass ownership for
`is_superuser` — see `_owned_post` there. Every route here requires
`is_superuser` (see `AdminUser` in `app.api.deps`)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, DbSession
from app.db.models import BlogComment, BlogStatus
from app.schemas.blog import (
    BlogCommentAdminUpdate,
    BlogCommentRead,
    BlogListResponse,
    BlogPostSummary,
)
from app.services import blog_service

router = APIRouter(prefix="/admin/blog", tags=["admin"])


@router.get("/posts", response_model=BlogListResponse)
def list_all_posts(
    admin: AdminUser,
    db: DbSession,
    status: Annotated[str | None, Query()] = None,
    author_id: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 24,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> BlogListResponse:
    stmt_status = BlogStatus(status) if status else None
    posts, total = blog_service.list_for_admin(
        db,
        status=stmt_status,
        author_id=author_id,
        query=q,
        limit=limit,
        offset=offset,
    )
    next_offset = offset + limit if offset + limit < total else None
    return BlogListResponse(
        items=[blog_service.to_read(BlogPostSummary, p) for p in posts],
        total=total,
        next_offset=next_offset,
    )


@router.get("/posts/{post_id}/comments", response_model=list[BlogCommentRead])
def list_post_comments(
    post_id: str, admin: AdminUser, db: DbSession
) -> list[BlogCommentRead]:
    post = blog_service.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found.")
    return [
        BlogCommentRead.model_validate(c)
        for c in blog_service.list_comments(db, post.id, include_hidden=True)
    ]


@router.patch("/comments/{comment_id}", response_model=BlogCommentRead)
def moderate_comment(
    comment_id: str,
    data: BlogCommentAdminUpdate,
    admin: AdminUser,
    db: DbSession,
) -> BlogCommentRead:
    comment: BlogComment | None = blog_service.get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if data.body is not None:
        comment = blog_service.update_comment_body(db, comment, data.body)
    if data.is_hidden is not None:
        comment = blog_service.set_comment_hidden(db, comment, data.is_hidden)
    return BlogCommentRead.model_validate(comment)
