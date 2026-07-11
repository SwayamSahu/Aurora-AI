from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BlogAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str | None = None


class BlogPostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=280)
    subtitle: str | None = Field(default=None, max_length=400)
    excerpt: str | None = Field(default=None, max_length=500)
    category: str | None = None
    tags: list[str] | None = None
    body_html: str | None = None
    body_json: dict | None = None
    cover_media_id: str | None = None
    status: Literal["draft", "published"] | None = None


class BlogPostUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=280)
    subtitle: str | None = Field(default=None, max_length=400)
    excerpt: str | None = Field(default=None, max_length=500)
    category: str | None = None
    tags: list[str] | None = None
    body_html: str | None = None
    body_json: dict | None = None
    cover_media_id: str | None = None
    status: Literal["draft", "published"] | None = None


class BlogCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class BlogCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    body: str
    author: BlogAuthor
    created_at: datetime
    is_hidden: bool = False


class BlogCommentAdminUpdate(BaseModel):
    body: str | None = Field(default=None, min_length=1, max_length=2000)
    is_hidden: bool | None = None


class BlogLikeToggle(BaseModel):
    liked: bool


class BlogPostSummary(BaseModel):
    """List-card shape — no heavy body."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    title: str
    subtitle: str | None
    excerpt: str | None
    category: str
    tags: list[str]
    status: str
    read_minutes: int
    like_count: int
    comment_count: int
    cover_media_id: str | None
    cover_url: str | None = None
    author: BlogAuthor
    created_at: datetime
    updated_at: datetime


class BlogPostDetail(BlogPostSummary):
    """Full post — includes the rendered body and viewer-specific flags."""

    body_html: str
    body_json: dict
    liked_by_me: bool = False


class BlogMediaRead(BaseModel):
    id: str
    url: str


class BlogListResponse(BaseModel):
    items: list[BlogPostSummary]
    total: int
    next_offset: int | None = None
