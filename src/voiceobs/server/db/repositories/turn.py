"""Turn repository for database operations."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import TurnRow


class TurnRepository:
    """Repository for turn operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the turn repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    async def add(
        self,
        conversation_id: UUID,
        span_id: UUID,
        actor: str,
        turn_id: str | None = None,
        turn_index: int | None = None,
        duration_ms: float | None = None,
        transcript: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> UUID:
        """Add a turn to the database.

        Args:
            conversation_id: Associated conversation UUID.
            span_id: Associated span UUID.
            actor: Turn actor ('user', 'agent', 'system').
            turn_id: External turn ID.
            turn_index: Turn index in conversation.
            duration_ms: Turn duration in milliseconds.
            transcript: Turn transcript.
            attributes: Turn attributes.

        Returns:
            The UUID of the stored turn.
        """
        turn_uuid = uuid4()
        attrs = attributes or {}

        await self._db.execute(
            """
            INSERT INTO turns (
                id, turn_id, conversation_id, span_id, actor,
                turn_index, duration_ms, transcript, attributes
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)
            """,
            turn_uuid,
            turn_id,
            conversation_id,
            span_id,
            actor,
            turn_index,
            duration_ms,
            transcript,
            json.dumps(attrs),
        )

        return turn_uuid

    async def get(self, turn_id: UUID) -> TurnRow | None:
        """Get a turn by UUID.

        Args:
            turn_id: The turn UUID.

        Returns:
            The turn row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, turn_id, conversation_id, span_id, actor,
                   turn_index, duration_ms, transcript, attributes, created_at
            FROM turns WHERE id = $1
            """,
            turn_id,
        )

        if row is None:
            return None

        return TurnRow(
            id=row["id"],
            turn_id=row["turn_id"],
            conversation_id=row["conversation_id"],
            span_id=row["span_id"],
            actor=row["actor"],
            turn_index=row["turn_index"],
            duration_ms=row["duration_ms"],
            transcript=row["transcript"],
            attributes=row["attributes"] or {},
            created_at=row["created_at"],
        )

    async def get_by_conversation(self, conversation_id: UUID) -> list[TurnRow]:
        """Get all turns for a conversation.

        Args:
            conversation_id: The conversation UUID.

        Returns:
            List of turns for the conversation, ordered by turn_index.
        """
        rows = await self._db.fetch(
            """
            SELECT id, turn_id, conversation_id, span_id, actor,
                   turn_index, duration_ms, transcript, attributes, created_at
            FROM turns WHERE conversation_id = $1
            ORDER BY turn_index NULLS LAST, created_at
            """,
            conversation_id,
        )

        return [
            TurnRow(
                id=row["id"],
                turn_id=row["turn_id"],
                conversation_id=row["conversation_id"],
                span_id=row["span_id"],
                actor=row["actor"],
                turn_index=row["turn_index"],
                duration_ms=row["duration_ms"],
                transcript=row["transcript"],
                attributes=row["attributes"] or {},
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def clear(self) -> int:
        """Delete all turns.

        Returns:
            Number of turns deleted.
        """
        count = await self._db.fetchval("SELECT COUNT(*) FROM turns")
        await self._db.execute("DELETE FROM turns")
        return count

    async def count(self) -> int:
        """Get the number of turns.

        Returns:
            Number of turns.
        """
        return await self._db.fetchval("SELECT COUNT(*) FROM turns")
