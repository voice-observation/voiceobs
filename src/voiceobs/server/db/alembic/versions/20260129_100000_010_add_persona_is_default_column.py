"""Add is_default column to personas table.

Revision ID: 010
Revises: 009
Create Date: 2026-01-29 10:00:00.000000

This migration adds an is_default boolean column to identify the fallback persona.
Only one persona can be the default at a time.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: str = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    Adds is_default (Boolean) column to the personas table with default false.
    """
    op.add_column(
        "personas",
        sa.Column(
            "is_default",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade database schema.

    Removes is_default column from the personas table.
    """
    op.drop_column("personas", "is_default")
