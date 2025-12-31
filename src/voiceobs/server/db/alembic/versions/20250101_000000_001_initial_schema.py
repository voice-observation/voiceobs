"""Initial schema for voiceobs

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

This migration creates the initial database schema for voiceobs,
including tables for conversations, spans, turns, and failures.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("conversation_id", sa.String(255), nullable=False),
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
        sa.UniqueConstraint("conversation_id"),
    )
    op.create_index(
        "idx_conversations_conversation_id",
        "conversations",
        ["conversation_id"],
    )
    op.create_index(
        "idx_conversations_created_at",
        "conversations",
        ["created_at"],
    )

    # Create spans table
    op.create_table(
        "spans",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column(
            "attributes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("trace_id", sa.String(64), nullable=True),
        sa.Column("span_id", sa.String(64), nullable=True),
        sa.Column("parent_span_id", sa.String(64), nullable=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_spans_name", "spans", ["name"])
    op.create_index("idx_spans_trace_id", "spans", ["trace_id"])
    op.create_index("idx_spans_conversation_id", "spans", ["conversation_id"])
    op.create_index("idx_spans_created_at", "spans", ["created_at"])
    op.create_index(
        "idx_spans_attributes",
        "spans",
        ["attributes"],
        postgresql_using="gin",
    )

    # Create turns table
    op.create_table(
        "turns",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("turn_id", sa.String(255), nullable=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("span_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor", sa.String(50), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column(
            "attributes",
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
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["span_id"],
            ["spans.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_turns_conversation_id", "turns", ["conversation_id"])
    op.create_index("idx_turns_turn_id", "turns", ["turn_id"])
    op.create_index("idx_turns_actor", "turns", ["actor"])
    op.create_index("idx_turns_turn_index", "turns", ["turn_index"])

    # Create failures table
    op.create_table(
        "failures",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("failure_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("turn_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("turn_index", sa.Integer(), nullable=True),
        sa.Column("signal_name", sa.String(100), nullable=True),
        sa.Column("signal_value", sa.Float(), nullable=True),
        sa.Column("threshold", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["turn_id"],
            ["turns.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_failures_failure_type", "failures", ["failure_type"])
    op.create_index("idx_failures_severity", "failures", ["severity"])
    op.create_index("idx_failures_conversation_id", "failures", ["conversation_id"])
    op.create_index("idx_failures_created_at", "failures", ["created_at"])

    # Create function for updating updated_at timestamp
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
        """
    )

    # Create trigger for auto-updating updated_at on conversations
    op.execute(
        """
        CREATE TRIGGER update_conversations_updated_at
            BEFORE UPDATE ON conversations
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
        """
    )


def downgrade() -> None:
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop tables in reverse order
    op.drop_table("failures")
    op.drop_table("turns")
    op.drop_table("spans")
    op.drop_table("conversations")
