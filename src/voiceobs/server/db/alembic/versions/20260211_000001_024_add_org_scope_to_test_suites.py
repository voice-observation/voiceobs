"""Add org_id to test_suites table.

Revision ID: 024
Revises: 023
Create Date: 2026-02-11 00:00:01.000000

This migration:
1. Adds org_id column to test_suites
2. Deletes all existing test suite rows (already done by agents migration CASCADE)
3. Makes org_id NOT NULL
4. Adds FK constraint, indexes, and unique constraint
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "024"
down_revision: str = "023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add org scope to test_suites table."""
    # 1. Add org_id column (nullable initially for the transition)
    op.add_column(
        "test_suites",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # 2. Existing test suites already deleted by agents migration CASCADE
    # But delete any remaining rows to be safe
    op.execute("DELETE FROM test_suites")

    # 3. Make org_id NOT NULL now that table is empty
    op.alter_column("test_suites", "org_id", nullable=False)

    # 4. Add FK constraint
    op.create_foreign_key(
        "fk_test_suites_org_id",
        "test_suites",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 5. Add index
    op.create_index("idx_test_suites_org_id", "test_suites", ["org_id"])

    # 6. Add unique constraint on (org_id, name)
    op.create_unique_constraint("uq_test_suites_org_id_name", "test_suites", ["org_id", "name"])


def downgrade() -> None:
    """Remove org scope from test_suites table."""
    # Remove unique constraint
    op.drop_constraint("uq_test_suites_org_id_name", "test_suites", type_="unique")

    # Remove index
    op.drop_index("idx_test_suites_org_id", "test_suites")

    # Remove FK
    op.drop_constraint("fk_test_suites_org_id", "test_suites", type_="foreignkey")

    # Remove column
    op.drop_column("test_suites", "org_id")
