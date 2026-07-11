"""wallet, credit ledger, plan catalog

Revision ID: f4a8c1d6b2e9
Revises: d1a2b3c4e5f6
Create Date: 2026-07-11

Adds the marketplace credit economy (M1): wallets, an append-only
credit_transactions ledger, the credit_plans catalog, and plan_purchases.
Seeds a default Free/Creator/Pro plan catalog so the pricing page has
something to render immediately.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "f4a8c1d6b2e9"
down_revision: str | None = "d1a2b3c4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "credit_plans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("credits_granted", sa.Integer(), nullable=False),
        sa.Column("listing_quota", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
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

    op.create_table(
        "wallets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("balance_credits", sa.Integer(), nullable=False),
        sa.Column("listing_quota", sa.Integer(), nullable=False),
        sa.Column("active_plan_id", sa.String(length=36), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["active_plan_id"], ["credit_plans.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_wallets_user_id"),
    )

    op.create_table(
        "credit_transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("wallet_id", sa.String(length=36), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "TOPUP",
                "PLAN_PURCHASE",
                "PURCHASE_SPEND",
                "SALE_EARNING",
                "PLATFORM_FEE",
                "REFUND",
                "ADMIN_ADJUST",
                name="transactiontype",
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=280), nullable=True),
        sa.Column("related_order_id", sa.String(length=36), nullable=True),
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
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_credit_transactions_wallet_id"), "credit_transactions", ["wallet_id"]
    )
    op.create_index(
        op.f("ix_credit_transactions_type"), "credit_transactions", ["type"]
    )

    op.create_table(
        "plan_purchases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PAID", "FAILED", name="purchasestatus"),
            nullable=False,
        ),
        sa.Column("payment_provider", sa.String(length=40), nullable=False),
        sa.Column("provider_ref", sa.String(length=120), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("credits_granted", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["credit_plans.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plan_purchases_user_id"), "plan_purchases", ["user_id"])
    op.create_index(op.f("ix_plan_purchases_status"), "plan_purchases", ["status"])

    # Seed a default catalog so the pricing page has something to show.
    credit_plans = sa.table(
        "credit_plans",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("price_cents", sa.Integer),
        sa.column("credits_granted", sa.Integer),
        sa.column("listing_quota", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(
        credit_plans,
        [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "name": "Free",
                "price_cents": 0,
                "credits_granted": 0,
                "listing_quota": 1,
                "is_active": True,
                "sort_order": 0,
            },
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "name": "Creator",
                "price_cents": 999,
                "credits_granted": 500,
                "listing_quota": 10,
                "is_active": True,
                "sort_order": 1,
            },
            {
                "id": "00000000-0000-0000-0000-000000000003",
                "name": "Pro",
                "price_cents": 2999,
                "credits_granted": 2000,
                "listing_quota": 50,
                "is_active": True,
                "sort_order": 2,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_plan_purchases_status"), table_name="plan_purchases")
    op.drop_index(op.f("ix_plan_purchases_user_id"), table_name="plan_purchases")
    op.drop_table("plan_purchases")
    sa.Enum(name="purchasestatus").drop(op.get_bind(), checkfirst=True)

    op.drop_index(op.f("ix_credit_transactions_type"), table_name="credit_transactions")
    op.drop_index(
        op.f("ix_credit_transactions_wallet_id"), table_name="credit_transactions"
    )
    op.drop_table("credit_transactions")
    sa.Enum(name="transactiontype").drop(op.get_bind(), checkfirst=True)

    op.drop_table("wallets")
    op.drop_table("credit_plans")
