"""Add generation_error column to test_suites table.

Revision ID: 013
Revises: 012
Create Date: 2026-01-29 40:00:00.000000

This migration adds the generation_error column to the test_suites table
to store error messages when test suite generation fails.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "013"
down_revision: str = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    Adds generation_error (Text, nullable) column to the test_suites table
    to store error messages when generation fails.
    """
    op.add_column(
        "test_suites",
        sa.Column("generation_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade database schema.

    Removes the generation_error column from the test_suites table.
    """
    op.drop_column("test_suites", "generation_error")
