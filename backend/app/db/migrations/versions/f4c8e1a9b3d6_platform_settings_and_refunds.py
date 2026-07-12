"""platform settings, partial refunds

Revision ID: f4c8e1a9b3d6
Revises: a1e5c8b3f7d2
Create Date: 2026-07-19

Adds a generic `platform_settings` key/value table (starts with the
marketplace platform fee, previously a static config value), and the
columns needed for item-level partial refunds: `order_items.is_refunded`
and a `platform_fee_credits` snapshot per item so historical revenue never
shifts when the fee is edited later.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "f4c8e1a9b3d6"
down_revision: str | None = "a1e5c8b3f7d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_settings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=60), nullable=False),
        sa.Column("value", sa.String(length=200), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_platform_settings_key"), "platform_settings", ["key"], unique=True
    )

    op.execute("ALTER TYPE orderstatus ADD VALUE 'PARTIALLY_REFUNDED'")

    op.add_column(
        "order_items",
        sa.Column(
            "platform_fee_credits", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "order_items",
        sa.Column(
            "is_refunded", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )

    # Best-effort backfill for existing rows: historical fee rate isn't
    # recorded anywhere, so approximate with the static default that was in
    # effect before this migration (10%) — only used for pre-existing data,
    # every future sale snapshots its actual fee at checkout time.
    op.execute(
        "UPDATE order_items SET platform_fee_credits = ROUND(price_credits * 0.10)"
    )
    # Orders already fully refunded before item-level tracking existed —
    # mark their items refunded so "remaining refundable" logic is correct.
    op.execute(
        """
        UPDATE order_items
        SET is_refunded = true
        FROM orders
        WHERE order_items.order_id = orders.id AND orders.status = 'REFUNDED'
        """
    )


def downgrade() -> None:
    op.drop_column("order_items", "is_refunded")
    op.drop_column("order_items", "platform_fee_credits")
    # Postgres doesn't support removing enum values; PARTIALLY_REFUNDED
    # stays in the type on downgrade (harmless — nothing references it once
    # the columns above are gone).
    op.drop_index(op.f("ix_platform_settings_key"), table_name="platform_settings")
    op.drop_table("platform_settings")
