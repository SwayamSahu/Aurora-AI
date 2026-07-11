"""listing likes + comments

Revision ID: c8d4b2e6a9f1
Revises: b9e2f5c8a1d3
Create Date: 2026-07-11

Adds real engagement (M6) for marketplace listings: likes and comments,
mirroring the blog's BlogLike/BlogComment tables. Listing.like_count/
comment_count already existed from M2 and are kept in sync by the service
layer, same as blog's.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "c8d4b2e6a9f1"
down_revision: str | None = "b9e2f5c8a1d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "listing_likes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("listing_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "listing_id", "user_id", name="uq_listing_like_listing_user"
        ),
    )
    op.create_index(op.f("ix_listing_likes_listing_id"), "listing_likes", ["listing_id"])
    op.create_index(op.f("ix_listing_likes_user_id"), "listing_likes", ["user_id"])

    op.create_table(
        "listing_comments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("listing_id", sa.String(length=36), nullable=False),
        sa.Column("author_id", sa.String(length=36), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_listing_comments_listing_id"), "listing_comments", ["listing_id"]
    )
    op.create_index(
        op.f("ix_listing_comments_author_id"), "listing_comments", ["author_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_listing_comments_author_id"), table_name="listing_comments")
    op.drop_index(op.f("ix_listing_comments_listing_id"), table_name="listing_comments")
    op.drop_table("listing_comments")

    op.drop_index(op.f("ix_listing_likes_user_id"), table_name="listing_likes")
    op.drop_index(op.f("ix_listing_likes_listing_id"), table_name="listing_likes")
    op.drop_table("listing_likes")
