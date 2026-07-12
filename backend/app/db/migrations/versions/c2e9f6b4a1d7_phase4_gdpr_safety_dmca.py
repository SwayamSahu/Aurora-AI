"""phase 4: gdpr erasure, content-safety flags, dmca requests

Revision ID: c2e9f6b4a1d7
Revises: b7d4f2a8c1e5
Create Date: 2026-08-09

Three additive, independent changes:
- `users.erased_at` — set by GDPR right-to-erasure (self-service or admin).
- `blog_media`/`listing_media` gain `is_flagged`/`flag_categories` for the
  automated content-safety scan run at upload time.
- `dmca_requests` — formal copyright takedown notices (separate from the
  generic `reports` table; see `app/db/models/dmca.py`).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c2e9f6b4a1d7"
down_revision: str | None = "b7d4f2a8c1e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("erased_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.add_column(
        "blog_media",
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "blog_media",
        sa.Column("flag_categories", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "listing_media",
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "listing_media",
        sa.Column("flag_categories", sa.JSON(), nullable=False, server_default="[]"),
    )

    dmca_status = postgresql.ENUM(
        "OPEN", "CONTENT_REMOVED", "REJECTED", name="dmcastatus"
    )
    dmca_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "dmca_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("claimant_name", sa.String(length=200), nullable=False),
        sa.Column("claimant_email", sa.String(length=320), nullable=False),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("work_description", sa.Text(), nullable=False),
        sa.Column("good_faith_statement", sa.Boolean(), nullable=False),
        sa.Column("signature", sa.String(length=200), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "OPEN", "CONTENT_REMOVED", "REJECTED", name="dmcastatus", create_type=False
            ),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("resolved_by_id", sa.String(length=36), nullable=True),
        sa.Column("resolution_note", sa.String(length=500), nullable=True),
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
        sa.ForeignKeyConstraint(["resolved_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_dmca_requests_target_type"), "dmca_requests", ["target_type"])
    op.create_index(op.f("ix_dmca_requests_target_id"), "dmca_requests", ["target_id"])
    op.create_index(op.f("ix_dmca_requests_status"), "dmca_requests", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_dmca_requests_status"), table_name="dmca_requests")
    op.drop_index(op.f("ix_dmca_requests_target_id"), table_name="dmca_requests")
    op.drop_index(op.f("ix_dmca_requests_target_type"), table_name="dmca_requests")
    op.drop_table("dmca_requests")
    postgresql.ENUM(name="dmcastatus").drop(op.get_bind(), checkfirst=True)

    op.drop_column("listing_media", "flag_categories")
    op.drop_column("listing_media", "is_flagged")
    op.drop_column("blog_media", "flag_categories")
    op.drop_column("blog_media", "is_flagged")

    op.drop_column("users", "erased_at")
