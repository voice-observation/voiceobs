"""Add search indexes for conversation search and filtering.

Revision ID: 002
Revises: 001
Create Date: 2025-01-02 00:00:00.000000

This migration adds indexes to support full-text search and filtering:
- GIN index on turn transcripts for full-text search
- Indexes on spans start_time for time range filtering
- Index on conversations for failure filtering
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add GIN index on turn transcripts for full-text search
    # Using to_tsvector for PostgreSQL full-text search
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_turns_transcript_gin
        ON turns USING GIN(to_tsvector('english', COALESCE(transcript, '')))
        """
    )

    # Add index on spans start_time for time range filtering
    op.create_index(
        "idx_spans_start_time",
        "spans",
        ["start_time"],
    )

    # Add index on conversations created_at (already exists, but ensure it's there)
    # This is for time-based filtering of conversations
    op.create_index(
        "idx_conversations_created_at_filter",
        "conversations",
        ["created_at"],
        if_not_exists=True,
    )

    # Add composite index for failure filtering (conversation_id + failure_type)
    op.create_index(
        "idx_failures_conversation_type",
        "failures",
        ["conversation_id", "failure_type"],
    )


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index("idx_failures_conversation_type", "failures")
    op.drop_index("idx_conversations_created_at_filter", "conversations")
    op.drop_index("idx_spans_start_time", "spans")
    op.execute("DROP INDEX IF EXISTS idx_turns_transcript_gin")
