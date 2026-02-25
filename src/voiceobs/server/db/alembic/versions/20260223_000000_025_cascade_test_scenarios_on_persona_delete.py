"""Change test_scenarios.persona_id FK to CASCADE for org delete cascade.

Revision ID: 025
Revises: 024
Create Date: 2026-02-23 00:00:00.000000

When an organization is deleted, personas are CASCADE deleted. test_scenarios
reference personas with RESTRICT, which blocked the org delete. Changing to
CASCADE allows org deletion to cascade through: org -> personas -> test_scenarios.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "025"
down_revision: str = "024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Change persona_id FK from RESTRICT to CASCADE."""
    op.drop_constraint("fk_test_scenarios_persona_id", "test_scenarios", type_="foreignkey")
    op.create_foreign_key(
        "fk_test_scenarios_persona_id",
        "test_scenarios",
        "personas",
        ["persona_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Restore persona_id FK to RESTRICT."""
    op.drop_constraint("fk_test_scenarios_persona_id", "test_scenarios", type_="foreignkey")
    op.create_foreign_key(
        "fk_test_scenarios_persona_id",
        "test_scenarios",
        "personas",
        ["persona_id"],
        ["id"],
        ondelete="RESTRICT",
    )
