"""generation billing + content-safety on generated assets

Revision ID: a4d9f7c2b8e1
Revises: c2e9f6b4a1d7
Create Date: 2026-08-20

Three additive changes supporting real multi-model video generation:
- `jobs.credits_charged` — the exact amount debited at submit time, snapshotted
  so a later refund (on failure) is always exact even if the model's credit
  price changes in between.
- `assets.is_flagged`/`flag_categories` — same automated content-safety scan
  already run on blog/listing uploads (`c2e9f6b4a1d7`), extended to generated
  video/image assets.
- `transactiontype` gains `GENERATION_SPEND` for the generation billing ledger
  entries (refunds reuse the existing generic `REFUND` value).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "a4d9f7c2b8e1"
down_revision: str | None = "c2e9f6b4a1d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "credits_charged", sa.Integer(), nullable=False, server_default="0"
        ),
    )

    op.add_column(
        "assets",
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "assets",
        sa.Column("flag_categories", sa.JSON(), nullable=False, server_default="[]"),
    )

    op.execute("ALTER TYPE transactiontype ADD VALUE 'GENERATION_SPEND'")


def downgrade() -> None:
    op.drop_column("assets", "flag_categories")
    op.drop_column("assets", "is_flagged")
    op.drop_column("jobs", "credits_charged")
    # Postgres doesn't support removing enum values; GENERATION_SPEND stays
    # in the type on downgrade (harmless — nothing references it once the
    # columns above are gone).
