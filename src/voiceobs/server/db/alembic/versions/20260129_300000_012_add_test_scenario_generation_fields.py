"""Add generation fields to test_scenarios table.

Revision ID: 012
Revises: 011
Create Date: 2026-01-29 30:00:00.000000

This migration adds intent, persona_traits, and persona_match_score columns
to the test_scenarios table for scenario generation tracking.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: str = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    Adds intent (String), persona_traits (JSONB), and persona_match_score (Float)
    columns to the test_scenarios table with an index on intent for filtering.
    """
    # Add intent column for LLM-identified intent
    op.add_column(
        "test_scenarios",
        sa.Column("intent", sa.String(255), nullable=True),
    )
    # Add persona_traits column as JSONB array
    op.add_column(
        "test_scenarios",
        sa.Column(
            "persona_traits",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
    )
    # Add persona_match_score column for trait matching score (0-1)
    op.add_column(
        "test_scenarios",
        sa.Column("persona_match_score", sa.Float(), nullable=True),
    )
    # Add index on intent for efficient filtering
    op.create_index("idx_test_scenarios_intent", "test_scenarios", ["intent"])


def downgrade() -> None:
    """Downgrade database schema.

    Removes intent, persona_traits, and persona_match_score columns
    from the test_scenarios table.
    """
    op.drop_index("idx_test_scenarios_intent", "test_scenarios")
    op.drop_column("test_scenarios", "persona_match_score")
    op.drop_column("test_scenarios", "persona_traits")
    op.drop_column("test_scenarios", "intent")
