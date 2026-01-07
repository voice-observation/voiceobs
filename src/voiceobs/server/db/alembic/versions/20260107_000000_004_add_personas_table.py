"""Add personas table and update test_scenarios.

Revision ID: 004
Revises: 003
Create Date: 2026-01-07 00:00:00.000000

This migration creates the personas table, adds persona_id column (NOT NULL)
to test_scenarios, and removes the persona_json column.
Since there are no existing test scenarios, persona_id can be NOT NULL from the start.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    Creates personas table with all required columns, constraints, and indexes.
    Adds persona_id column to test_scenarios and removes persona_json column.
    """
    # Create personas table
    op.create_table(
        "personas",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("aggression", sa.Float(), nullable=False),
        sa.Column("patience", sa.Float(), nullable=False),
        sa.Column("verbosity", sa.Float(), nullable=False),
        sa.Column(
            "traits",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
        sa.Column("tts_provider", sa.String(50), nullable=False),
        sa.Column(
            "tts_config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column("preview_audio_url", sa.String(512), nullable=True),
        sa.Column("preview_audio_text", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.CheckConstraint(
            "aggression >= 0 AND aggression <= 1",
            name="check_aggression_range",
        ),
        sa.CheckConstraint(
            "patience >= 0 AND patience <= 1",
            name="check_patience_range",
        ),
        sa.CheckConstraint(
            "verbosity >= 0 AND verbosity <= 1",
            name="check_verbosity_range",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes on personas table
    op.create_index("idx_personas_name", "personas", ["name"])
    op.create_index("idx_personas_is_active", "personas", ["is_active"])
    op.create_index("idx_personas_created_at", "personas", ["created_at"])
    op.create_index("idx_personas_tts_provider", "personas", ["tts_provider"])

    # Add persona_id column to test_scenarios (required)
    op.add_column(
        "test_scenarios",
        sa.Column("persona_id", postgresql.UUID(as_uuid=True), nullable=False),
    )

    # Create foreign key constraint
    op.create_foreign_key(
        "fk_test_scenarios_persona_id",
        "test_scenarios",
        "personas",
        ["persona_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # Create index on persona_id
    op.create_index("idx_test_scenarios_persona_id", "test_scenarios", ["persona_id"])

    # Drop persona_json column
    op.drop_column("test_scenarios", "persona_json")


def downgrade() -> None:
    """Downgrade database schema.

    Restores persona_json column to test_scenarios and removes persona_id.
    Drops personas table and all related indexes and constraints.
    """
    # Restore persona_json column
    op.add_column(
        "test_scenarios",
        sa.Column(
            "persona_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
    )

    # Drop index on persona_id
    op.drop_index("idx_test_scenarios_persona_id", "test_scenarios")

    # Drop foreign key constraint
    op.drop_constraint("fk_test_scenarios_persona_id", "test_scenarios", type_="foreignkey")

    # Drop persona_id column
    op.drop_column("test_scenarios", "persona_id")

    # Drop indexes on personas table
    op.drop_index("idx_personas_tts_provider", "personas")
    op.drop_index("idx_personas_created_at", "personas")
    op.drop_index("idx_personas_is_active", "personas")
    op.drop_index("idx_personas_name", "personas")

    # Drop personas table
    op.drop_table("personas")
