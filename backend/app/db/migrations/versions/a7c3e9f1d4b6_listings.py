"""marketplace listings + listing media

Revision ID: a7c3e9f1d4b6
Revises: f4a8c1d6b2e9
Create Date: 2026-07-11

Adds the marketplace listings catalog (M2): sellers list a priced clone of
one of their own assets; likes/comments tables land later in M6.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "a7c3e9f1d4b6"
down_revision: str | None = "f4a8c1d6b2e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "listing_media",
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
    op.create_index(
        op.f("ix_listing_media_uploader_id"), "listing_media", ["uploader_id"]
    )

    op.create_table(
        "listings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("seller_id", sa.String(length=36), nullable=False),
        sa.Column("source_asset_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("price_credits", sa.Integer(), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "ACTIVE", "SOLD", "DELISTED", name="listingstatus"),
            nullable=False,
        ),
        sa.Column("cover_media_id", sa.String(length=36), nullable=True),
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
        sa.ForeignKeyConstraint(["seller_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_asset_id"], ["assets.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["cover_media_id"], ["listing_media.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_listings_seller_id"), "listings", ["seller_id"])
    op.create_index(op.f("ix_listings_category"), "listings", ["category"])
    op.create_index(op.f("ix_listings_status"), "listings", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_listings_status"), table_name="listings")
    op.drop_index(op.f("ix_listings_category"), table_name="listings")
    op.drop_index(op.f("ix_listings_seller_id"), table_name="listings")
    op.drop_table("listings")
    sa.Enum(name="listingstatus").drop(op.get_bind(), checkfirst=True)

    op.drop_index(op.f("ix_listing_media_uploader_id"), table_name="listing_media")
    op.drop_table("listing_media")
