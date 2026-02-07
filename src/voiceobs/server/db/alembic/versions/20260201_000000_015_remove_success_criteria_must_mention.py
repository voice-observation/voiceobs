"""Remove success_criteria and must_mention from test_scenarios table.

Revision ID: 015
Revises: 014
Create Date: 2026-02-01 00:00:00.000000

Removes success_criteria and must_mention columns as they are no longer needed.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015"
down_revision: str = "014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove success_criteria and must_mention columns."""
    op.drop_column("test_scenarios", "success_criteria")
    op.drop_column("test_scenarios", "must_mention")


def downgrade() -> None:
    """Re-add success_criteria and must_mention columns."""
    op.add_column(
        "test_scenarios",
        sa.Column("success_criteria", sa.Text(), nullable=True),
    )
    op.add_column(
        "test_scenarios",
        sa.Column(
            "must_mention",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
    )
