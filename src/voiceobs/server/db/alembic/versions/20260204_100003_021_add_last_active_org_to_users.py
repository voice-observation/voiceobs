"""Add last_active_org_id to users table.

Revision ID: 021
Revises: 020
Create Date: 2026-02-04 10:00:03.000000

This migration adds the last_active_org_id column to users for tracking
which organization the user was last active in.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "021"
down_revision: str = "020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add last_active_org_id column to users table."""
    op.add_column(
        "users",
        sa.Column(
            "last_active_org_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_users_last_active_org_id",
        "users",
        "organizations",
        ["last_active_org_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_users_last_active_org_id", "users", ["last_active_org_id"])


def downgrade() -> None:
    """Remove last_active_org_id column from users table."""
    op.drop_index("idx_users_last_active_org_id", "users")
    op.drop_constraint("fk_users_last_active_org_id", "users", type_="foreignkey")
    op.drop_column("users", "last_active_org_id")
