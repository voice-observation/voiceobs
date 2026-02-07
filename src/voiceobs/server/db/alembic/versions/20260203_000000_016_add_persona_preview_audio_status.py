"""Add preview_audio_status and preview_audio_error columns to personas table.

Revision ID: 016
Revises: 015
Create Date: 2026-02-03 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add preview_audio_status and preview_audio_error columns."""
    op.add_column(
        "personas",
        sa.Column("preview_audio_status", sa.String(20), nullable=True),
    )
    op.add_column(
        "personas",
        sa.Column("preview_audio_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove preview_audio_status and preview_audio_error columns."""
    op.drop_column("personas", "preview_audio_error")
    op.drop_column("personas", "preview_audio_status")
