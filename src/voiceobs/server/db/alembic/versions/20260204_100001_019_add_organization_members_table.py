"""Add organization_members table.

Revision ID: 019
Revises: 018
Create Date: 2026-02-04 10:00:01.000000

This migration creates the organization_members join table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "019"
down_revision: str = "018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create organization_members table."""
    op.create_table(
        "organization_members",
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
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(50),
            nullable=False,
            server_default="member",
        ),
        sa.Column(
            "invited_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name="fk_organization_members_org_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_organization_members_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["invited_by"],
            ["users.id"],
            name="fk_organization_members_invited_by",
        ),
        sa.UniqueConstraint("org_id", "user_id", name="uq_organization_members_org_user"),
    )

    # Create indexes
    op.create_index("idx_organization_members_org_id", "organization_members", ["org_id"])
    op.create_index("idx_organization_members_user_id", "organization_members", ["user_id"])
    op.create_index("idx_organization_members_role", "organization_members", ["role"])


def downgrade() -> None:
    """Drop organization_members table."""
    op.drop_index("idx_organization_members_role", "organization_members")
    op.drop_index("idx_organization_members_user_id", "organization_members")
    op.drop_index("idx_organization_members_org_id", "organization_members")
    op.drop_table("organization_members")
