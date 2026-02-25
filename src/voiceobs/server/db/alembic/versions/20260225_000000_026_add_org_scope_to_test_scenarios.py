"""Add org_id to test_scenarios table.

Revision ID: 026
Revises: 025
Create Date: 2026-02-25 00:00:00.000000

This migration:
1. Adds org_id column to test_scenarios (nullable initially)
2. Deletes all existing test scenario rows (clean slate)
3. Makes org_id NOT NULL
4. Adds FK constraint with CASCADE on delete
5. Adds index on org_id
6. Adds unique constraint on (org_id, name)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "026"
down_revision: str = "025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add org_id column to test_scenarios."""
    # Step 1: Add nullable org_id column
    op.add_column("test_scenarios", sa.Column("org_id", sa.Uuid(), nullable=True))

    # Step 2: Delete all existing test scenario rows (clean slate)
    op.execute("DELETE FROM test_scenarios")

    # Step 3: Make org_id NOT NULL
    op.alter_column("test_scenarios", "org_id", nullable=False)

    # Step 4: Add FK constraint with CASCADE on delete
    op.create_foreign_key(
        "fk_test_scenarios_org_id",
        "test_scenarios",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Step 5: Add index on org_id
    op.create_index("idx_test_scenarios_org_id", "test_scenarios", ["org_id"])

    # Step 6: Add unique constraint on (org_id, name)
    op.create_unique_constraint(
        "uq_test_scenarios_org_id_name", "test_scenarios", ["org_id", "name"]
    )


def downgrade() -> None:
    """Remove org_id column from test_scenarios."""
    op.drop_constraint("uq_test_scenarios_org_id_name", "test_scenarios", type_="unique")
    op.drop_index("idx_test_scenarios_org_id", table_name="test_scenarios")
    op.drop_constraint("fk_test_scenarios_org_id", "test_scenarios", type_="foreignkey")
    op.drop_column("test_scenarios", "org_id")
