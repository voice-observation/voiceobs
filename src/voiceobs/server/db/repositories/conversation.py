"""Conversation repository for database operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import ConversationRow


class ConversationRepository:
    """Repository for conversation operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the conversation repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    async def get_or_create(self, conversation_id: str) -> ConversationRow:
        """Get an existing conversation or create a new one.

        Args:
            conversation_id: External conversation ID.

        Returns:
            The conversation row.
        """
        # Try to get existing conversation
        row = await self._db.fetchrow(
            """
            SELECT id, conversation_id, created_at, updated_at
            FROM conversations WHERE conversation_id = $1
            """,
            conversation_id,
        )

        if row is not None:
            return ConversationRow(
                id=row["id"],
                conversation_id=row["conversation_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

        # Create new conversation
        new_id = uuid4()
        await self._db.execute(
            """
            INSERT INTO conversations (id, conversation_id)
            VALUES ($1, $2)
            """,
            new_id,
            conversation_id,
        )

        return ConversationRow(
            id=new_id,
            conversation_id=conversation_id,
        )

    async def get(self, id: UUID) -> ConversationRow | None:
        """Get a conversation by UUID.

        Args:
            id: The conversation UUID.

        Returns:
            The conversation row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, conversation_id, created_at, updated_at
            FROM conversations WHERE id = $1
            """,
            id,
        )

        if row is None:
            return None

        return ConversationRow(
            id=row["id"],
            conversation_id=row["conversation_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_by_external_id(self, conversation_id: str) -> ConversationRow | None:
        """Get a conversation by external ID.

        Args:
            conversation_id: External conversation ID.

        Returns:
            The conversation row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, conversation_id, created_at, updated_at
            FROM conversations WHERE conversation_id = $1
            """,
            conversation_id,
        )

        if row is None:
            return None

        return ConversationRow(
            id=row["id"],
            conversation_id=row["conversation_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_all(self) -> list[ConversationRow]:
        """Get all conversations.

        Returns:
            List of all conversations.
        """
        rows = await self._db.fetch(
            """
            SELECT id, conversation_id, created_at, updated_at
            FROM conversations ORDER BY created_at DESC
            """
        )

        return [
            ConversationRow(
                id=row["id"],
                conversation_id=row["conversation_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    async def get_summary(self) -> list[dict[str, Any]]:
        """Get conversation summaries with counts.

        Returns:
            List of conversation summaries with turn and span counts.
        """
        rows = await self._db.fetch(
            """
            SELECT
                c.id,
                c.conversation_id,
                COUNT(DISTINCT s.id) as span_count,
                COUNT(DISTINCT t.id) as turn_count,
                EXISTS(SELECT 1 FROM failures f WHERE f.conversation_id = c.id) as has_failures
            FROM conversations c
            LEFT JOIN spans s ON s.conversation_id = c.id
            LEFT JOIN turns t ON t.conversation_id = c.id
            GROUP BY c.id, c.conversation_id
            ORDER BY c.created_at DESC
            """
        )

        return [
            {
                "id": row["conversation_id"],
                "span_count": row["span_count"],
                "turn_count": row["turn_count"],
                "has_failures": row["has_failures"],
            }
            for row in rows
        ]

    async def clear(self) -> int:
        """Delete all conversations.

        Returns:
            Number of conversations deleted.
        """
        count = await self._db.fetchval("SELECT COUNT(*) FROM conversations")
        await self._db.execute("DELETE FROM conversations")
        return count

    async def count(self) -> int:
        """Get the number of conversations.

        Returns:
            Number of conversations.
        """
        return await self._db.fetchval("SELECT COUNT(*) FROM conversations")
