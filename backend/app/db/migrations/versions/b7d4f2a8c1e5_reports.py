"""content reports

Revision ID: b7d4f2a8c1e5
Revises: f4c8e1a9b3d6
Create Date: 2026-07-26

User-submitted reports against blog posts/comments and marketplace
listings/comments, reviewed by moderators. Targets are referenced by
`(target_type, target_id)` rather than a foreign key, matching the
`admin_actions` audit log pattern — the target may later be deleted while
the report record stays.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b7d4f2a8c1e5"
down_revision: str | None = "f4c8e1a9b3d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Provision the enum types explicitly, then reference them with
    # `create_type=False` in the column defs below — otherwise
    # `create_table` tries to CREATE TYPE a second time and fails.
    report_reason = postgresql.ENUM(
        "SPAM", "ABUSE", "INAPPROPRIATE", "COPYRIGHT", "OTHER", name="reportreason"
    )
    report_status = postgresql.ENUM("OPEN", "RESOLVED", "DISMISSED", name="reportstatus")
    report_reason.create(op.get_bind(), checkfirst=True)
    report_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("reporter_id", sa.String(length=36), nullable=True),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column(
            "reason",
            postgresql.ENUM(
                "SPAM",
                "ABUSE",
                "INAPPROPRIATE",
                "COPYRIGHT",
                "OTHER",
                name="reportreason",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "OPEN", "RESOLVED", "DISMISSED", name="reportstatus", create_type=False
            ),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("resolved_by_id", sa.String(length=36), nullable=True),
        sa.Column("resolution_note", sa.String(length=500), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resolved_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_reporter_id"), "reports", ["reporter_id"])
    op.create_index(op.f("ix_reports_target_type"), "reports", ["target_type"])
    op.create_index(op.f("ix_reports_target_id"), "reports", ["target_id"])
    op.create_index(op.f("ix_reports_status"), "reports", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_reports_status"), table_name="reports")
    op.drop_index(op.f("ix_reports_target_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_target_type"), table_name="reports")
    op.drop_index(op.f("ix_reports_reporter_id"), table_name="reports")
    op.drop_table("reports")
    postgresql.ENUM(name="reportstatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="reportreason").drop(op.get_bind(), checkfirst=True)
