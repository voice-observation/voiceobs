"""Add agent_id column to test_suites table.

Revision ID: 011
Revises: 010
Create Date: 2026-01-29 20:00:00.000000

This migration adds an agent_id foreign key column to associate test suites
with agents. The column is nullable to support existing rows.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "011"
down_revision: str = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    Adds agent_id (UUID) column to the test_suites table with foreign key
    constraint to agents table and an index for efficient lookups.
    """
    # Add nullable column first for existing rows
    op.add_column(
        "test_suites",
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    # Add foreign key constraint
    op.create_foreign_key(
        "fk_test_suites_agent_id",
        "test_suites",
        "agents",
        ["agent_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # Add index for efficient lookups
    op.create_index("idx_test_suites_agent_id", "test_suites", ["agent_id"])


def downgrade() -> None:
    """Downgrade database schema.

    Removes agent_id column from the test_suites table.
    """
    op.drop_index("idx_test_suites_agent_id", "test_suites")
    op.drop_constraint("fk_test_suites_agent_id", "test_suites", type_="foreignkey")
    op.drop_column("test_suites", "agent_id")
