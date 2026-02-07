"""Add organizations table.

Revision ID: 018
Revises: 017
Create Date: 2026-02-04 10:00:00.000000

This migration creates the organizations table for multi-tenant support.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "018"
down_revision: str = "017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create organizations table."""
    op.create_table(
        "organizations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_organizations_created_by",
        ),
    )

    # Create indexes
    op.create_index("idx_organizations_created_by", "organizations", ["created_by"])
    op.create_index("idx_organizations_created_at", "organizations", ["created_at"])


def downgrade() -> None:
    """Drop organizations table."""
    op.drop_index("idx_organizations_created_at", "organizations")
    op.drop_index("idx_organizations_created_by", "organizations")
    op.drop_table("organizations")
