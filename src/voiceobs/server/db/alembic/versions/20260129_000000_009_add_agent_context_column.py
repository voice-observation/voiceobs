"""Add context column to agents table.

Revision ID: 009
Revises: 008
Create Date: 2026-01-29 00:00:00.000000

This migration adds a context column to store domain-specific information
about what the agent does.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: str = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    Adds context (Text) column to the agents table.
    """
    op.add_column(
        "agents",
        sa.Column(
            "context",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade database schema.

    Removes context column from the agents table.
    """
    op.drop_column("agents", "context")
