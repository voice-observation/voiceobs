"""Add test_suite_runs table and update test_executions.

Revision ID: 027
Revises: 026
Create Date: 2026-02-26 00:00:00.000000

This migration:
1. Creates test_suite_runs table
2. Adds new columns to test_executions (suite_run_id, org_id, attempt,
   max_attempts, audio_url, transcript, evaluation_result, error_message,
   duration_seconds)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "027"
down_revision: str = "026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create test_suite_runs table and update test_executions."""
    # Create test_suite_runs table
    op.create_table(
        "test_suite_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("suite_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("total_scenarios", sa.Integer(), nullable=False),
        sa.Column("completed_scenarios", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_scenarios", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("triggered_by", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["suite_id"], ["test_suites.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_test_suite_runs_org_id", "test_suite_runs", ["org_id"])
    op.create_index("idx_test_suite_runs_suite_id", "test_suite_runs", ["suite_id"])
    op.create_index("idx_test_suite_runs_status", "test_suite_runs", ["status"])
    op.create_index("idx_test_suite_runs_created_at", "test_suite_runs", ["created_at"])

    # Delete existing test_executions (clean slate for schema change)
    op.execute("DELETE FROM test_executions")

    # Add new columns to test_executions
    op.add_column(
        "test_executions",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "test_executions",
        sa.Column("suite_run_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "test_executions",
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "test_executions",
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "test_executions",
        sa.Column("audio_url", sa.String(512), nullable=True),
    )
    op.add_column(
        "test_executions",
        sa.Column(
            "transcript",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "test_executions",
        sa.Column(
            "evaluation_result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "test_executions",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "test_executions",
        sa.Column("duration_seconds", sa.Float(), nullable=True),
    )
    op.add_column(
        "test_executions",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
    )

    # Make org_id NOT NULL (after clean slate)
    op.alter_column("test_executions", "org_id", nullable=False)
    op.alter_column("test_executions", "suite_run_id", nullable=False)

    # Widen status column to accommodate longer statuses like "evaluating"
    op.alter_column("test_executions", "status", type_=sa.String(30), existing_type=sa.String(20))

    # Add FK constraints
    op.create_foreign_key(
        "fk_test_executions_org_id",
        "test_executions",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_test_executions_suite_run_id",
        "test_executions",
        "test_suite_runs",
        ["suite_run_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add indexes
    op.create_index("idx_test_executions_org_id", "test_executions", ["org_id"])
    op.create_index("idx_test_executions_suite_run_id", "test_executions", ["suite_run_id"])


def downgrade() -> None:
    """Remove test_suite_runs table and revert test_executions changes."""
    # Remove new indexes and constraints from test_executions
    op.drop_index("idx_test_executions_suite_run_id", table_name="test_executions")
    op.drop_index("idx_test_executions_org_id", table_name="test_executions")
    op.drop_constraint("fk_test_executions_suite_run_id", "test_executions", type_="foreignkey")
    op.drop_constraint("fk_test_executions_org_id", "test_executions", type_="foreignkey")

    # Revert status column width
    op.alter_column("test_executions", "status", type_=sa.String(20), existing_type=sa.String(30))

    # Remove new columns from test_executions
    op.drop_column("test_executions", "created_at")
    op.drop_column("test_executions", "duration_seconds")
    op.drop_column("test_executions", "error_message")
    op.drop_column("test_executions", "evaluation_result")
    op.drop_column("test_executions", "transcript")
    op.drop_column("test_executions", "audio_url")
    op.drop_column("test_executions", "max_attempts")
    op.drop_column("test_executions", "attempt")
    op.drop_column("test_executions", "suite_run_id")
    op.drop_column("test_executions", "org_id")

    # Drop test_suite_runs table
    op.drop_index("idx_test_suite_runs_created_at", table_name="test_suite_runs")
    op.drop_index("idx_test_suite_runs_status", table_name="test_suite_runs")
    op.drop_index("idx_test_suite_runs_suite_id", table_name="test_suite_runs")
    op.drop_index("idx_test_suite_runs_org_id", table_name="test_suite_runs")
    op.drop_table("test_suite_runs")
