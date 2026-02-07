"""Add test suite configuration columns.

Revision ID: 008
Revises: 007
Create Date: 2026-01-28 00:00:00.000000

This migration adds columns to store test suite configuration:
test_scopes, thoroughness, edge_cases, and evaluation_strictness.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: str = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    Adds test_scopes (JSONB array), thoroughness (Integer), edge_cases (JSONB array),
    and evaluation_strictness (String) columns to the test_suites table.
    """
    op.add_column(
        "test_suites",
        sa.Column(
            "test_scopes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'["core_flows", "common_mistakes"]\'::jsonb'),
            nullable=False,
        ),
    )
    op.add_column(
        "test_suites",
        sa.Column(
            "thoroughness",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
    )
    op.add_column(
        "test_suites",
        sa.Column(
            "edge_cases",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "test_suites",
        sa.Column(
            "evaluation_strictness",
            sa.String(20),
            server_default="balanced",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade database schema.

    Removes test_scopes, thoroughness, edge_cases, and evaluation_strictness
    columns from the test_suites table.
    """
    op.drop_column("test_suites", "evaluation_strictness")
    op.drop_column("test_suites", "edge_cases")
    op.drop_column("test_suites", "thoroughness")
    op.drop_column("test_suites", "test_scopes")
