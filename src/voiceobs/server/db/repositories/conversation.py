"""Conversation repository for database operations."""

from __future__ import annotations

from datetime import datetime
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

    def _add_query_condition(
        self, query: str, conditions: list[str], params: list[Any], param_idx: int
    ) -> int:
        """Add full-text search condition for query.

        Args:
            query: Search query string.
            conditions: List of SQL conditions to append to.
            params: List of SQL parameters to append to.
            param_idx: Current parameter index.

        Returns:
            Next parameter index.
        """
        next_param = param_idx + 1
        conditions.append(
            f"""
            (c.conversation_id ILIKE ${param_idx}
            OR EXISTS (
                SELECT 1 FROM turns t
                WHERE t.conversation_id = c.id
                AND to_tsvector('english', COALESCE(t.transcript, ''))
                    @@ plainto_tsquery('english', ${next_param})
            ))
            """
        )
        params.append(f"%{query}%")
        params.append(query)
        return param_idx + 2

    def _add_start_time_condition(
        self, start_time: datetime, conditions: list[str], params: list[Any], param_idx: int
    ) -> int:
        """Add start time filter condition.

        Args:
            start_time: Start time threshold.
            conditions: List of SQL conditions to append to.
            params: List of SQL parameters to append to.
            param_idx: Current parameter index.

        Returns:
            Next parameter index.
        """
        conditions.append(
            f"""
            EXISTS (
                SELECT 1 FROM spans s
                WHERE s.conversation_id = c.id
                AND s.start_time >= ${param_idx}
            )
            """
        )
        params.append(start_time)
        return param_idx + 1

    def _add_end_time_condition(
        self, end_time: datetime, conditions: list[str], params: list[Any], param_idx: int
    ) -> int:
        """Add end time filter condition.

        Args:
            end_time: End time threshold.
            conditions: List of SQL conditions to append to.
            params: List of SQL parameters to append to.
            param_idx: Current parameter index.

        Returns:
            Next parameter index.
        """
        conditions.append(
            f"""
            EXISTS (
                SELECT 1 FROM spans s
                WHERE s.conversation_id = c.id
                AND s.start_time <= ${param_idx}
            )
            """
        )
        params.append(end_time)
        return param_idx + 1

    def _add_actor_condition(
        self, actor: str, conditions: list[str], params: list[Any], param_idx: int
    ) -> int:
        """Add actor filter condition.

        Args:
            actor: Actor to filter by.
            conditions: List of SQL conditions to append to.
            params: List of SQL parameters to append to.
            param_idx: Current parameter index.

        Returns:
            Next parameter index.
        """
        conditions.append(
            f"""
            EXISTS (
                SELECT 1 FROM turns t
                WHERE t.conversation_id = c.id
                AND t.actor = ${param_idx}
            )
            """
        )
        params.append(actor)
        return param_idx + 1

    def _add_has_failures_condition(self, has_failures: bool, conditions: list[str]) -> None:
        """Add failure status filter condition.

        Args:
            has_failures: Whether to filter for conversations with failures.
            conditions: List of SQL conditions to append to.
        """
        if has_failures:
            conditions.append("EXISTS (SELECT 1 FROM failures f WHERE f.conversation_id = c.id)")
        else:
            conditions.append(
                "NOT EXISTS (SELECT 1 FROM failures f WHERE f.conversation_id = c.id)"
            )

    def _add_failure_type_condition(
        self, failure_type: str, conditions: list[str], params: list[Any], param_idx: int
    ) -> int:
        """Add failure type filter condition.

        Args:
            failure_type: Failure type to filter by.
            conditions: List of SQL conditions to append to.
            params: List of SQL parameters to append to.
            param_idx: Current parameter index.

        Returns:
            Next parameter index.
        """
        conditions.append(
            f"""
            EXISTS (
                SELECT 1 FROM failures f
                WHERE f.conversation_id = c.id
                AND f.failure_type = ${param_idx}
            )
            """
        )
        params.append(failure_type)
        return param_idx + 1

    def _add_min_latency_condition(
        self, min_latency_ms: float, conditions: list[str], params: list[Any], param_idx: int
    ) -> int:
        """Add minimum latency filter condition.

        Args:
            min_latency_ms: Minimum latency threshold.
            conditions: List of SQL conditions to append to.
            params: List of SQL parameters to append to.
            param_idx: Current parameter index.

        Returns:
            Next parameter index.
        """
        conditions.append(
            f"""
            EXISTS (
                SELECT 1 FROM spans s
                WHERE s.conversation_id = c.id
                AND s.duration_ms >= ${param_idx}
            )
            """
        )
        params.append(min_latency_ms)
        return param_idx + 1

    def _build_search_conditions(
        self,
        query: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
        actor: str | None,
        has_failures: bool | None,
        failure_type: str | None,
        min_latency_ms: float | None,
    ) -> tuple[list[str], list[Any], int]:
        """Build WHERE conditions for search query.

        Args:
            query: Full-text search query.
            start_time: Filter by start time.
            end_time: Filter by end time.
            actor: Filter by actor.
            has_failures: Filter by failure status.
            failure_type: Filter by failure type.
            min_latency_ms: Filter by minimum latency.

        Returns:
            Tuple of (conditions list, params list, next param index).
        """
        conditions: list[str] = []
        params: list[Any] = []
        param_idx = 1

        if query:
            param_idx = self._add_query_condition(query, conditions, params, param_idx)

        if start_time:
            param_idx = self._add_start_time_condition(start_time, conditions, params, param_idx)

        if end_time:
            param_idx = self._add_end_time_condition(end_time, conditions, params, param_idx)

        if actor:
            param_idx = self._add_actor_condition(actor, conditions, params, param_idx)

        if has_failures is not None:
            self._add_has_failures_condition(has_failures, conditions)

        if failure_type:
            param_idx = self._add_failure_type_condition(
                failure_type, conditions, params, param_idx
            )

        if min_latency_ms is not None:
            param_idx = self._add_min_latency_condition(
                min_latency_ms, conditions, params, param_idx
            )

        return conditions, params, param_idx

    def _build_order_by(
        self, sort: str, sort_order: str, query: str | None, query_param_idx: int | None
    ) -> str:
        """Build ORDER BY clause for search query.

        Args:
            sort: Sort field (start_time, latency, relevance).
            sort_order: Sort order (asc, desc).
            query: Search query for relevance sorting.
            query_param_idx: Parameter index for query in relevance sorting.

        Returns:
            ORDER BY clause string.
        """
        if sort == "start_time":
            order_by = "MIN(span_times.start_time)"
        elif sort == "latency":
            order_by = "AVG(span_times.duration_ms)"
        elif sort == "relevance" and query and query_param_idx:
            order_by = f"""
            ts_rank(
                to_tsvector('english', c.conversation_id || ' ' ||
                COALESCE((
                    SELECT string_agg(t.transcript, ' ')
                    FROM turns t
                    WHERE t.conversation_id = c.id
                ), '')),
                plainto_tsquery('english', ${query_param_idx})
            )
            """
        else:
            order_by = "c.created_at"

        order_direction = "ASC" if sort_order.lower() == "asc" else "DESC"
        return f"{order_by} {order_direction}"

    async def search(
        self,
        query: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        actor: str | None = None,
        has_failures: bool | None = None,
        failure_type: str | None = None,
        min_latency_ms: float | None = None,
        sort: str = "start_time",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Search and filter conversations.

        Args:
            query: Full-text search query for transcripts and conversation IDs.
            start_time: Filter conversations starting after this time.
            end_time: Filter conversations starting before this time.
            actor: Filter by actor (user, agent, system).
            has_failures: Filter by failure status.
            failure_type: Filter by specific failure type.
            min_latency_ms: Filter by minimum latency threshold.
            sort: Sort field (start_time, latency, relevance).
            sort_order: Sort order (asc, desc).
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            Tuple of (list of conversation summaries, total count).
        """
        # Build WHERE conditions
        conditions, params, param_idx = self._build_search_conditions(
            query=query,
            start_time=start_time,
            end_time=end_time,
            actor=actor,
            has_failures=has_failures,
            failure_type=failure_type,
            min_latency_ms=min_latency_ms,
        )

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Find query parameter index for relevance sorting
        query_param_idx = 2 if query else None

        # Build ORDER BY clause
        order_by = self._build_order_by(sort, sort_order, query, query_param_idx)

        # Build and execute main query
        base_query = f"""
        SELECT
            c.id,
            c.conversation_id,
            COUNT(DISTINCT s.id) as span_count,
            COUNT(DISTINCT t.id) as turn_count,
            EXISTS(SELECT 1 FROM failures f WHERE f.conversation_id = c.id) as has_failures,
            MIN(span_times.start_time) as min_start_time,
            AVG(span_times.duration_ms) as avg_latency
        FROM conversations c
        LEFT JOIN spans s ON s.conversation_id = c.id
        LEFT JOIN spans span_times ON span_times.conversation_id = c.id
        LEFT JOIN turns t ON t.conversation_id = c.id
        {where_clause}
        GROUP BY c.id, c.conversation_id
        ORDER BY {order_by}
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])

        rows = await self._db.fetch(base_query, *params)

        results = [
            {
                "id": row["conversation_id"],
                "span_count": row["span_count"],
                "turn_count": row["turn_count"],
                "has_failures": row["has_failures"],
            }
            for row in rows
        ]

        # Get total count
        count_query = f"""
        SELECT COUNT(DISTINCT c.id)
        FROM conversations c
        {where_clause}
        """
        count_params = params[:-2]
        total = await self._db.fetchval(count_query, *count_params) or 0

        return results, total
