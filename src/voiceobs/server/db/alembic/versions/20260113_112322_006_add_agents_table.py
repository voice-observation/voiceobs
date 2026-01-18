"""Add agents table.

Revision ID: 006
Revises: 005
Create Date: 2026-01-13 11:23:22.000000

This migration creates the agents table for storing customer voice agent integrations.
Agents can be phone-based or web-based, with flexible contact_info stored as JSONB.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema.

    Creates agents table with all required columns and indexes.
    """
    # Create agents table
    op.create_table(
        "agents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("agent_type", sa.String(20), nullable=False, server_default="phone"),
        sa.Column(
            "contact_info",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column(
            "supported_intents",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "connection_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "verification_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("last_verification_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_error", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
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
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_agents_connection_status", "agents", ["connection_status"])
    op.create_index("idx_agents_created_at", "agents", ["created_at"])
    op.create_index("idx_agents_is_active", "agents", ["is_active"])
    op.create_index(
        "idx_agents_supported_intents",
        "agents",
        ["supported_intents"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Downgrade database schema.

    Drops agents table and all related indexes.
    """
    # Drop indexes
    op.drop_index("idx_agents_supported_intents", "agents")
    op.drop_index("idx_agents_is_active", "agents")
    op.drop_index("idx_agents_created_at", "agents")
    op.drop_index("idx_agents_connection_status", "agents")

    # Drop agents table
    op.drop_table("agents")

