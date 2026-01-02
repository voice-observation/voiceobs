"""Add test tables and audio columns to conversations.

Revision ID: 003
Revises: 002
Create Date: 2025-01-03 00:00:00.000000

This migration creates tables for test suites, scenarios, and executions,
and adds audio_path and audio_metadata columns to the conversations table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create test_suites table
    op.create_table(
        "test_suites",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_test_suites_name", "test_suites", ["name"])
    op.create_index("idx_test_suites_status", "test_suites", ["status"])
    op.create_index("idx_test_suites_created_at", "test_suites", ["created_at"])

    # Create test_scenarios table
    op.create_table(
        "test_scenarios",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("suite_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column(
            "persona_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column("max_turns", sa.Integer(), nullable=True),
        sa.Column("timeout", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["suite_id"],
            ["test_suites.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_test_scenarios_suite_id", "test_scenarios", ["suite_id"])
    op.create_index("idx_test_scenarios_name", "test_scenarios", ["name"])

    # Create test_executions table
    op.create_table(
        "test_executions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "result_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["scenario_id"],
            ["test_scenarios.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_test_executions_scenario_id", "test_executions", ["scenario_id"])
    op.create_index("idx_test_executions_conversation_id", "test_executions", ["conversation_id"])
    op.create_index("idx_test_executions_status", "test_executions", ["status"])
    op.create_index("idx_test_executions_started_at", "test_executions", ["started_at"])

    # Add audio_path and audio_metadata columns to conversations table
    op.add_column(
        "conversations",
        sa.Column("audio_path", sa.String(512), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "audio_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
    )
    op.create_index("idx_conversations_audio_path", "conversations", ["audio_path"])


def downgrade() -> None:
    # Drop indexes for conversations audio columns
    op.drop_index("idx_conversations_audio_path", "conversations")

    # Drop audio columns from conversations
    op.drop_column("conversations", "audio_metadata")
    op.drop_column("conversations", "audio_path")

    # Drop test_executions table and its indexes
    op.drop_index("idx_test_executions_started_at", "test_executions")
    op.drop_index("idx_test_executions_status", "test_executions")
    op.drop_index("idx_test_executions_conversation_id", "test_executions")
    op.drop_index("idx_test_executions_scenario_id", "test_executions")
    op.drop_table("test_executions")

    # Drop test_scenarios table and its indexes
    op.drop_index("idx_test_scenarios_name", "test_scenarios")
    op.drop_index("idx_test_scenarios_suite_id", "test_scenarios")
    op.drop_table("test_scenarios")

    # Drop test_suites table and its indexes
    op.drop_index("idx_test_suites_created_at", "test_suites")
    op.drop_index("idx_test_suites_status", "test_suites")
    op.drop_index("idx_test_suites_name", "test_suites")
    op.drop_table("test_suites")
