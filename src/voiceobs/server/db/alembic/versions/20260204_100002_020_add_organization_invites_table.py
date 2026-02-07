"""Add organization_invites table.

Revision ID: 020
Revises: 019
Create Date: 2026-02-04 10:00:02.000000

This migration creates the organization_invites table for pending invites.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "020"
down_revision: str = "019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create organization_invites table."""
    op.create_table(
        "organization_invites",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "invited_by",
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
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name="fk_organization_invites_org_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["invited_by"],
            ["users.id"],
            name="fk_organization_invites_invited_by",
        ),
        sa.UniqueConstraint("token", name="uq_organization_invites_token"),
    )

    # Create indexes
    op.create_index("idx_organization_invites_org_id", "organization_invites", ["org_id"])
    op.create_index("idx_organization_invites_email", "organization_invites", ["email"])
    op.create_index("idx_organization_invites_token", "organization_invites", ["token"])
    op.create_index("idx_organization_invites_status", "organization_invites", ["status"])


def downgrade() -> None:
    """Drop organization_invites table."""
    op.drop_index("idx_organization_invites_status", "organization_invites")
    op.drop_index("idx_organization_invites_token", "organization_invites")
    op.drop_index("idx_organization_invites_email", "organization_invites")
    op.drop_index("idx_organization_invites_org_id", "organization_invites")
    op.drop_table("organization_invites")
