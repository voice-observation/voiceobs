"""Add org_id and persona_type to personas table.

Revision ID: 022
Revises: 021
Create Date: 2026-02-08 00:00:00.000000

This migration:
1. Adds org_id (nullable initially) and persona_type columns to personas
2. Deletes all existing persona rows (clean slate)
3. Makes org_id NOT NULL
4. Adds FK constraint, indexes, and unique constraint
5. Removes old idx_personas_name index (replaced by composite unique)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "022"
down_revision: str = "021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add org scope to personas table."""
    # 1. Add columns (org_id nullable initially for the transition)
    op.add_column(
        "personas",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "personas",
        sa.Column(
            "persona_type",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'custom'"),
        ),
    )

    # 2. Delete all existing persona rows (clean slate).
    # Must also delete test_scenarios that reference personas due to FK RESTRICT.
    op.execute("DELETE FROM test_scenarios")
    op.execute("DELETE FROM personas")

    # 3. Make org_id NOT NULL now that table is empty
    op.alter_column("personas", "org_id", nullable=False)

    # 4. Add FK constraint
    op.create_foreign_key(
        "fk_personas_org_id",
        "personas",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 5. Add indexes
    op.create_index("idx_personas_org_id", "personas", ["org_id"])

    # 6. Add unique constraint on (org_id, name)
    op.create_unique_constraint("uq_personas_org_id_name", "personas", ["org_id", "name"])

    # 7. Remove old global name index (replaced by composite unique)
    op.drop_index("idx_personas_name", "personas")

    # 8. Add CHECK constraint for persona_type
    op.create_check_constraint(
        "check_persona_type",
        "personas",
        "persona_type IN ('system', 'custom')",
    )


def downgrade() -> None:
    """Remove org scope from personas table."""
    # Remove CHECK constraint
    op.drop_constraint("check_persona_type", "personas", type_="check")

    # Restore old name index
    op.create_index("idx_personas_name", "personas", ["name"])

    # Remove unique constraint
    op.drop_constraint("uq_personas_org_id_name", "personas", type_="unique")

    # Remove index
    op.drop_index("idx_personas_org_id", "personas")

    # Remove FK
    op.drop_constraint("fk_personas_org_id", "personas", type_="foreignkey")

    # Remove columns
    op.drop_column("personas", "persona_type")
    op.drop_column("personas", "org_id")
