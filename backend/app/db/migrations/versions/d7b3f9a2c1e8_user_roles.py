"""user roles: replace is_superuser boolean with a role enum

Revision ID: d7b3f9a2c1e8
Revises: e3f7a1c9d5b2
Create Date: 2026-07-12

Introduces the three-tier role system (user/moderator/admin). Existing
`is_superuser = true` users are backfilled to role=ADMIN, then the boolean
column is dropped — the model keeps `is_superuser` as a back-compat hybrid
property (== role admin).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "d7b3f9a2c1e8"
down_revision: str | None = "e3f7a1c9d5b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    userrole = sa.Enum("USER", "MODERATOR", "ADMIN", name="userrole")
    userrole.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column("role", userrole, nullable=False, server_default="USER"),
    )
    op.create_index(op.f("ix_users_role"), "users", ["role"])
    # Preserve existing admins before the boolean column goes away.
    op.execute("UPDATE users SET role = 'ADMIN' WHERE is_superuser = true")
    op.drop_column("users", "is_superuser")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_superuser",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.execute("UPDATE users SET is_superuser = true WHERE role = 'ADMIN'")
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_column("users", "role")
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
