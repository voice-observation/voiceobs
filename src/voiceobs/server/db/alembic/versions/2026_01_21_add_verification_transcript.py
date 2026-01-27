"""Add verification transcript and reasoning columns to agents table.

Revision ID: 007
Revises: 006
Create Date: 2026-01-21 00:00:00.000000

This migration adds columns to store the verification conversation transcript
and the reasoning for the verification result.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    Adds verification_transcript (JSONB) and verification_reasoning (Text)
    columns to the agents table.
    """
    op.add_column(
        "agents",
        sa.Column(
            "verification_transcript",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "agents",
        sa.Column(
            "verification_reasoning",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade database schema.

    Removes verification_transcript and verification_reasoning columns
    from the agents table.
    """
    op.drop_column("agents", "verification_reasoning")
    op.drop_column("agents", "verification_transcript")
