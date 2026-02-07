"""Add CRUD fields to test_scenarios table.

Revision ID: 014
Revises: 013
Create Date: 2026-01-30 00:00:00.000000

Adds caller_behaviors, success_criteria, must_mention, tags, and status columns.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014"
down_revision: str = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add new columns for scenario CRUD."""
    # caller_behaviors: list of test steps
    op.add_column(
        "test_scenarios",
        sa.Column(
            "caller_behaviors",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
    )
    # success_criteria: what defines passing
    op.add_column(
        "test_scenarios",
        sa.Column("success_criteria", sa.Text(), nullable=True),
    )
    # must_mention: required phrases
    op.add_column(
        "test_scenarios",
        sa.Column(
            "must_mention",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
    )
    # tags: categorization
    op.add_column(
        "test_scenarios",
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
    )
    # status: ready or draft (auto-computed)
    op.add_column(
        "test_scenarios",
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
    )
    # Add indexes for filtering
    op.create_index("idx_test_scenarios_status", "test_scenarios", ["status"])
    op.create_index("idx_test_scenarios_tags", "test_scenarios", ["tags"], postgresql_using="gin")


def downgrade() -> None:
    """Remove new columns."""
    op.drop_index("idx_test_scenarios_tags", "test_scenarios")
    op.drop_index("idx_test_scenarios_status", "test_scenarios")
    op.drop_column("test_scenarios", "status")
    op.drop_column("test_scenarios", "tags")
    op.drop_column("test_scenarios", "must_mention")
    op.drop_column("test_scenarios", "success_criteria")
    op.drop_column("test_scenarios", "caller_behaviors")
