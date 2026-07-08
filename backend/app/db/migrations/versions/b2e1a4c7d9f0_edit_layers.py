"""edit layers

Revision ID: b2e1a4c7d9f0
Revises: 08715871faa8
Create Date: 2026-07-08

Adds the `edit_layers` table backing the AI Edit workspace (E2): each row is a
non-destructive AI edit attached to a timeline clip, producing a derived asset.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "b2e1a4c7d9f0"
down_revision: str | None = "08715871faa8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "edit_layers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("clip_id", sa.String(length=64), nullable=False),
        sa.Column("engine", sa.String(length=40), nullable=False),
        sa.Column("preset_id", sa.String(length=80), nullable=True),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("mask_storage_key", sa.String(length=512), nullable=True),
        sa.Column("source_asset_id", sa.String(length=36), nullable=True),
        sa.Column("result_asset_id", sa.String(length=36), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "RUNNING",
                "SUCCEEDED",
                "FAILED",
                name="editlayerstatus",
            ),
            nullable=False,
        ),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_asset_id"], ["assets.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["result_asset_id"], ["assets.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_edit_layers_project_id"), "edit_layers", ["project_id"], unique=False
    )
    op.create_index(
        op.f("ix_edit_layers_clip_id"), "edit_layers", ["clip_id"], unique=False
    )
    op.create_index(
        op.f("ix_edit_layers_status"), "edit_layers", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_edit_layers_status"), table_name="edit_layers")
    op.drop_index(op.f("ix_edit_layers_clip_id"), table_name="edit_layers")
    op.drop_index(op.f("ix_edit_layers_project_id"), table_name="edit_layers")
    op.drop_table("edit_layers")
    sa.Enum(name="editlayerstatus").drop(op.get_bind(), checkfirst=True)
