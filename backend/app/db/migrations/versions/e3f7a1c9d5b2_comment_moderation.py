"""comment moderation: is_hidden on blog/listing comments

Revision ID: e3f7a1c9d5b2
Revises: c8d4b2e6a9f1
Create Date: 2026-07-12

Admin comment moderation: a soft-hide flag on blog_comments and
listing_comments. Hidden comments are excluded from public reads and from
the denormalized comment_count, but the row stays (unlike a hard delete).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "e3f7a1c9d5b2"
down_revision: str | None = "c8d4b2e6a9f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "blog_comments",
        sa.Column(
            "is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "listing_comments",
        sa.Column(
            "is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )


def downgrade() -> None:
    op.drop_column("listing_comments", "is_hidden")
    op.drop_column("blog_comments", "is_hidden")
