"""Add users table for authentication.

Revision ID: 017
Revises: 016
Create Date: 2026-02-04 00:00:00.000000

This migration creates the users table that stores user profiles.
The id column is the Supabase user ID (from JWT sub claim).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "017"
down_revision: str = "016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create users table."""
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Supabase user ID from JWT sub claim",
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column(
            "auth_provider",
            sa.String(50),
            nullable=True,
            comment="email, google, or github",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Create indexes
    op.create_index("idx_users_created_at", "users", ["created_at"])
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_is_active", "users", ["is_active"])


def downgrade() -> None:
    """Drop users table."""
    op.drop_index("idx_users_created_at", "users")
    op.drop_index("idx_users_is_active", "users")
    op.drop_index("idx_users_email", "users")
    op.drop_table("users")
