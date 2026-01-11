"""Add unique index for personas upsert logic.

Revision ID: 005
Revises: 004
Create Date: 2026-01-08 17:32:38.000000

This migration adds a unique index on (tts_provider, metadata->>'base_persona_key')
to enable ON CONFLICT upsert logic in the persona seed script.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    Creates unique index on personas table for upsert logic.
    This index allows ON CONFLICT to work for upserting personas
    by provider and base_persona_key combination.
    """
    # Create unique index for upsert logic: (tts_provider, metadata->>'base_persona_key')
    # This allows ON CONFLICT to work for upserting personas by provider and base_persona_key
    # The WHERE clause ensures the index only applies when base_persona_key is not null
    op.execute(
        """
        CREATE UNIQUE INDEX personas_provider_base_key_uq
        ON personas (tts_provider, (metadata->>'base_persona_key'))
        WHERE metadata->>'base_persona_key' IS NOT NULL;
        """
    )


def downgrade() -> None:
    """Downgrade database schema.

    Drops the unique index on personas table.
    """
    op.execute("DROP INDEX IF EXISTS personas_provider_base_key_uq")

