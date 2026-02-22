"""Add org_id to agents table.

Revision ID: 023
Revises: 022
Create Date: 2026-02-11 00:00:00.000000

This migration:
1. Adds org_id column to agents
2. Deletes all existing agent rows (clean slate)
3. Makes org_id NOT NULL
4. Adds FK constraint, indexes, and unique constraint
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "023"
down_revision: str = "022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add org scope to agents table."""
    # 1. Add org_id column (nullable initially for the transition)
    op.add_column(
        "agents",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # 2. Delete all existing agent rows (clean slate).
    # Must also delete test_suites and test_scenarios due to FK CASCADE.
    op.execute("DELETE FROM test_scenarios")
    op.execute("DELETE FROM test_suites")
    op.execute("DELETE FROM agents")

    # 3. Make org_id NOT NULL now that table is empty
    op.alter_column("agents", "org_id", nullable=False)

    # 4. Add FK constraint
    op.create_foreign_key(
        "fk_agents_org_id",
        "agents",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 5. Add index
    op.create_index("idx_agents_org_id", "agents", ["org_id"])

    # 6. Add unique constraint on (org_id, name)
    op.create_unique_constraint("uq_agents_org_id_name", "agents", ["org_id", "name"])


def downgrade() -> None:
    """Remove org scope from agents table."""
    # Remove unique constraint
    op.drop_constraint("uq_agents_org_id_name", "agents", type_="unique")

    # Remove index
    op.drop_index("idx_agents_org_id", "agents")

    # Remove FK
    op.drop_constraint("fk_agents_org_id", "agents", type_="foreignkey")

    # Remove column
    op.drop_column("agents", "org_id")
