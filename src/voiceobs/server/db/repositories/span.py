"""Span repository for database operations."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import SpanRow


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    """Parse a datetime value from string or datetime object.

    Args:
        value: ISO 8601 string, datetime object, or None.

    Returns:
        datetime object or None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    # Parse ISO 8601 string
    return datetime.fromisoformat(value)


class SpanRepository:
    """Repository for span operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the span repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    async def add(
        self,
        name: str,
        start_time: str | datetime | None = None,
        end_time: str | datetime | None = None,
        duration_ms: float | None = None,
        attributes: dict[str, Any] | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        conversation_id: UUID | None = None,
    ) -> UUID:
        """Add a span to the database.

        Args:
            name: Span name.
            start_time: Start time as ISO 8601 string or datetime object.
            end_time: End time as ISO 8601 string or datetime object.
            duration_ms: Duration in milliseconds.
            attributes: Span attributes.
            trace_id: OpenTelemetry trace ID.
            span_id: OpenTelemetry span ID.
            parent_span_id: Parent span ID.
            conversation_id: Associated conversation UUID.

        Returns:
            The UUID of the stored span.
        """
        span_uuid = uuid4()
        attrs = attributes or {}

        await self._db.execute(
            """
            INSERT INTO spans (
                id, name, start_time, end_time, duration_ms,
                attributes, trace_id, span_id, parent_span_id, conversation_id
            ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, $10)
            """,
            span_uuid,
            name,
            _parse_datetime(start_time),
            _parse_datetime(end_time),
            duration_ms,
            json.dumps(attrs),
            trace_id,
            span_id,
            parent_span_id,
            conversation_id,
        )

        return span_uuid

    async def get(self, span_id: UUID) -> SpanRow | None:
        """Get a span by ID.

        Args:
            span_id: The span UUID.

        Returns:
            The span row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, name, start_time, end_time, duration_ms,
                   attributes, trace_id, span_id, parent_span_id,
                   conversation_id, created_at
            FROM spans WHERE id = $1
            """,
            span_id,
        )

        if row is None:
            return None

        attrs = row["attributes"]
        # Parse JSONB if it's a string (asyncpg might return it as string)
        if isinstance(attrs, str):
            attrs = json.loads(attrs) if attrs else {}
        elif attrs is None:
            attrs = {}

        return SpanRow(
            id=row["id"],
            name=row["name"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            duration_ms=row["duration_ms"],
            attributes=attrs,
            trace_id=row["trace_id"],
            span_id=row["span_id"],
            parent_span_id=row["parent_span_id"],
            conversation_id=row["conversation_id"],
            created_at=row["created_at"],
        )

    async def get_all(self) -> list[SpanRow]:
        """Get all spans.

        Returns:
            List of all spans.
        """
        rows = await self._db.fetch(
            """
            SELECT id, name, start_time, end_time, duration_ms,
                   attributes, trace_id, span_id, parent_span_id,
                   conversation_id, created_at
            FROM spans ORDER BY created_at DESC
            """
        )

        result = []
        for row in rows:
            attrs = row["attributes"]
            # Parse JSONB if it's a string (asyncpg might return it as string)
            if isinstance(attrs, str):
                attrs = json.loads(attrs) if attrs else {}
            elif attrs is None:
                attrs = {}

            result.append(
                SpanRow(
                    id=row["id"],
                    name=row["name"],
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    duration_ms=row["duration_ms"],
                    attributes=attrs,
                    trace_id=row["trace_id"],
                    span_id=row["span_id"],
                    parent_span_id=row["parent_span_id"],
                    conversation_id=row["conversation_id"],
                    created_at=row["created_at"],
                )
            )

        return result

    async def get_as_dicts(self) -> list[dict[str, Any]]:
        """Get all spans as dictionaries (for analysis).

        Returns:
            List of span dictionaries compatible with analyzer.
        """
        rows = await self._db.fetch(
            """
            SELECT name, duration_ms, attributes
            FROM spans ORDER BY created_at DESC
            """
        )

        result = []
        for row in rows:
            attrs = row["attributes"]
            # Parse JSONB if it's a string (asyncpg might return it as string)
            if isinstance(attrs, str):
                attrs = json.loads(attrs) if attrs else {}
            elif attrs is None:
                attrs = {}

            result.append(
                {
                    "name": row["name"],
                    "duration_ms": row["duration_ms"],
                    "attributes": attrs,
                }
            )

        return result

    async def get_by_conversation(self, conversation_id: UUID) -> list[SpanRow]:
        """Get all spans for a conversation.

        Args:
            conversation_id: The conversation UUID.

        Returns:
            List of spans for the conversation.
        """
        rows = await self._db.fetch(
            """
            SELECT id, name, start_time, end_time, duration_ms,
                   attributes, trace_id, span_id, parent_span_id,
                   conversation_id, created_at
            FROM spans WHERE conversation_id = $1
            ORDER BY created_at
            """,
            conversation_id,
        )

        return [
            SpanRow(
                id=row["id"],
                name=row["name"],
                start_time=row["start_time"],
                end_time=row["end_time"],
                duration_ms=row["duration_ms"],
                attributes=row["attributes"] or {},
                trace_id=row["trace_id"],
                span_id=row["span_id"],
                parent_span_id=row["parent_span_id"],
                conversation_id=row["conversation_id"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def clear(self) -> int:
        """Delete all spans.

        Returns:
            Number of spans deleted.
        """
        count = await self._db.fetchval("SELECT COUNT(*) FROM spans")
        await self._db.execute("DELETE FROM spans")
        return count

    async def count(self) -> int:
        """Get the number of spans.

        Returns:
            Number of spans.
        """
        return await self._db.fetchval("SELECT COUNT(*) FROM spans")
