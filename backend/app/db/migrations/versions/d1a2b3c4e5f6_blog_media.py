"""blog media (public-servable images)

Revision ID: d1a2b3c4e5f6
Revises: c3f7a2b8e410
Create Date: 2026-07-11

Adds `blog_media` — a public-servable image table for blog covers/inline
images (separate from the project-scoped `assets` table, which requires
auth+ownership and is incompatible with a public blog). Repoints
`blog_posts.cover_asset_id` -> `blog_posts.cover_media_id`.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "d1a2b3c4e5f6"
down_revision: str | None = "c3f7a2b8e410"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "blog_media",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("uploader_id", sa.String(length=36), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
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
        sa.ForeignKeyConstraint(["uploader_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_blog_media_uploader_id"), "blog_media", ["uploader_id"])

    with op.batch_alter_table("blog_posts") as batch:
        batch.drop_constraint("blog_posts_cover_asset_id_fkey", type_="foreignkey")
        batch.alter_column("cover_asset_id", new_column_name="cover_media_id")
        batch.create_foreign_key(
            "blog_posts_cover_media_id_fkey",
            "blog_media",
            ["cover_media_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("blog_posts") as batch:
        batch.drop_constraint("blog_posts_cover_media_id_fkey", type_="foreignkey")
        batch.alter_column("cover_media_id", new_column_name="cover_asset_id")
        batch.create_foreign_key(
            "blog_posts_cover_asset_id_fkey",
            "assets",
            ["cover_asset_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.drop_index(op.f("ix_blog_media_uploader_id"), table_name="blog_media")
    op.drop_table("blog_media")
