"""Blog admin console: moderation dashboard (all posts/authors/statuses)
and comment moderation. Post/comment CRUD itself goes through the existing
author-scoped routes in `blog.py`, which now bypass ownership for
moderators/admins — see `_owned_post` there. Content moderation is open to
both moderators and admins (see `ModeratorUser` in `app.api.deps`)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession, ModeratorUser
from app.db.models import BlogComment, BlogStatus
from app.schemas.admin import BulkActionResult, BulkIdsRequest
from app.schemas.blog import (
    BlogCommentAdminUpdate,
    BlogCommentRead,
    BlogListResponse,
    BlogPostSummary,
)
from app.services import audit_service, blog_service

router = APIRouter(prefix="/admin/blog", tags=["admin"])


@router.get("/posts", response_model=BlogListResponse)
def list_all_posts(
    moderator: ModeratorUser,
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
    post_id: str, moderator: ModeratorUser, db: DbSession
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
    moderator: ModeratorUser,
    db: DbSession,
) -> BlogCommentRead:
    comment: BlogComment | None = blog_service.get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if data.body is not None:
        comment = blog_service.update_comment_body(db, comment, data.body)
    if data.is_hidden is not None:
        comment = blog_service.set_comment_hidden(db, comment, data.is_hidden)
    audit_service.record(
        db,
        actor_id=moderator.id,
        action="blog_comment.moderate",
        target_type="blog_comment",
        target_id=comment.id,
        metadata=data.model_dump(exclude_none=True),
    )
    return BlogCommentRead.model_validate(comment)


@router.post("/posts/bulk-delete", response_model=BulkActionResult)
def bulk_delete_posts(
    data: BulkIdsRequest, moderator: ModeratorUser, db: DbSession
) -> BulkActionResult:
    succeeded: list[str] = []
    failed: list[str] = []
    for post_id in data.ids:
        post = blog_service.get_by_id(db, post_id)
        if post is None:
            failed.append(post_id)
            continue
        blog_service.delete_post(db, post)
        succeeded.append(post_id)

    if succeeded:
        audit_service.record(
            db,
            actor_id=moderator.id,
            action="post.bulk_delete",
            target_type="blog_post",
            target_id=None,
            metadata={"ids": succeeded, "count": len(succeeded)},
        )
    return BulkActionResult(succeeded=succeeded, failed=failed)


@router.post("/comments/bulk-hide", response_model=BulkActionResult)
def bulk_hide_comments(
    data: BulkIdsRequest, moderator: ModeratorUser, db: DbSession
) -> BulkActionResult:
    succeeded: list[str] = []
    failed: list[str] = []
    for comment_id in data.ids:
        comment = blog_service.get_comment(db, comment_id)
        if comment is None:
            failed.append(comment_id)
            continue
        blog_service.set_comment_hidden(db, comment, True)
        succeeded.append(comment_id)

    if succeeded:
        audit_service.record(
            db,
            actor_id=moderator.id,
            action="blog_comment.bulk_hide",
            target_type="blog_comment",
            target_id=None,
            metadata={"ids": succeeded, "count": len(succeeded)},
        )
    return BulkActionResult(succeeded=succeeded, failed=failed)
