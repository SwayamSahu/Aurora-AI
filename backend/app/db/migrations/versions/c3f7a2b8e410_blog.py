"""blog posts, likes, comments

Revision ID: c3f7a2b8e410
Revises: b2e1a4c7d9f0
Create Date: 2026-07-11

Adds the community blog (B1): user-authored posts with likes and comments.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "c3f7a2b8e410"
down_revision: str | None = "b2e1a4c7d9f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "blog_posts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("author_id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=280), nullable=False),
        sa.Column("title", sa.String(length=280), nullable=False),
        sa.Column("subtitle", sa.String(length=400), nullable=True),
        sa.Column("excerpt", sa.String(length=500), nullable=True),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("body_json", sa.JSON(), nullable=False),
        sa.Column("cover_asset_id", sa.String(length=36), nullable=True),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "PUBLISHED", name="blogstatus"),
            nullable=False,
        ),
        sa.Column("read_minutes", sa.Integer(), nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False),
        sa.Column("comment_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["cover_asset_id"], ["assets.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_blog_posts_author_id"), "blog_posts", ["author_id"])
    op.create_index(op.f("ix_blog_posts_category"), "blog_posts", ["category"])
    op.create_index(op.f("ix_blog_posts_status"), "blog_posts", ["status"])
    op.create_index(
        op.f("ix_blog_posts_slug"), "blog_posts", ["slug"], unique=True
    )

    op.create_table(
        "blog_likes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("post_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["post_id"], ["blog_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_blog_like_post_user"),
    )
    op.create_index(op.f("ix_blog_likes_post_id"), "blog_likes", ["post_id"])
    op.create_index(op.f("ix_blog_likes_user_id"), "blog_likes", ["user_id"])

    op.create_table(
        "blog_comments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("post_id", sa.String(length=36), nullable=False),
        sa.Column("author_id", sa.String(length=36), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["post_id"], ["blog_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_blog_comments_post_id"), "blog_comments", ["post_id"])
    op.create_index(
        op.f("ix_blog_comments_author_id"), "blog_comments", ["author_id"]
    )


def downgrade() -> None:
    op.drop_table("blog_comments")
    op.drop_table("blog_likes")
    op.drop_index(op.f("ix_blog_posts_slug"), table_name="blog_posts")
    op.drop_index(op.f("ix_blog_posts_status"), table_name="blog_posts")
    op.drop_index(op.f("ix_blog_posts_category"), table_name="blog_posts")
    op.drop_index(op.f("ix_blog_posts_author_id"), table_name="blog_posts")
    op.drop_table("blog_posts")
    sa.Enum(name="blogstatus").drop(op.get_bind(), checkfirst=True)
