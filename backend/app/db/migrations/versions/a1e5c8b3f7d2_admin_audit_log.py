"""admin audit log

Revision ID: a1e5c8b3f7d2
Revises: d7b3f9a2c1e8
Create Date: 2026-07-12

Append-only log of privileged admin/moderator actions. actor_id is SET NULL
on user deletion so history survives the actor's account removal.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "a1e5c8b3f7d2"
down_revision: str | None = "d7b3f9a2c1e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_actions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=True),
        sa.Column("action_metadata", sa.JSON(), nullable=False),
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
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_actions_actor_id"), "admin_actions", ["actor_id"])
    op.create_index(op.f("ix_admin_actions_action"), "admin_actions", ["action"])
    op.create_index(
        op.f("ix_admin_actions_target_type"), "admin_actions", ["target_type"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_actions_target_type"), table_name="admin_actions")
    op.drop_index(op.f("ix_admin_actions_action"), table_name="admin_actions")
    op.drop_index(op.f("ix_admin_actions_actor_id"), table_name="admin_actions")
    op.drop_table("admin_actions")
