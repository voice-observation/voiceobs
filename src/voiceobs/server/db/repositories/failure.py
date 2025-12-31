"""Failure repository for database operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import FailureRow


class FailureRepository:
    """Repository for failure operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the failure repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    async def add(
        self,
        failure_type: str,
        severity: str,
        message: str,
        conversation_id: UUID | None = None,
        turn_id: UUID | None = None,
        turn_index: int | None = None,
        signal_name: str | None = None,
        signal_value: float | None = None,
        threshold: float | None = None,
    ) -> UUID:
        """Add a failure to the database.

        Args:
            failure_type: Type of failure.
            severity: Severity level.
            message: Failure message.
            conversation_id: Associated conversation UUID.
            turn_id: Associated turn UUID.
            turn_index: Turn index.
            signal_name: Signal that triggered the failure.
            signal_value: Signal value.
            threshold: Threshold that was exceeded.

        Returns:
            The UUID of the stored failure.
        """
        failure_uuid = uuid4()

        await self._db.execute(
            """
            INSERT INTO failures (
                id, failure_type, severity, message,
                conversation_id, turn_id, turn_index,
                signal_name, signal_value, threshold
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            failure_uuid,
            failure_type,
            severity,
            message,
            conversation_id,
            turn_id,
            turn_index,
            signal_name,
            signal_value,
            threshold,
        )

        return failure_uuid

    async def get(self, failure_id: UUID) -> FailureRow | None:
        """Get a failure by UUID.

        Args:
            failure_id: The failure UUID.

        Returns:
            The failure row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, failure_type, severity, message,
                   conversation_id, turn_id, turn_index,
                   signal_name, signal_value, threshold, created_at
            FROM failures WHERE id = $1
            """,
            failure_id,
        )

        if row is None:
            return None

        return FailureRow(
            id=row["id"],
            failure_type=row["failure_type"],
            severity=row["severity"],
            message=row["message"],
            conversation_id=row["conversation_id"],
            turn_id=row["turn_id"],
            turn_index=row["turn_index"],
            signal_name=row["signal_name"],
            signal_value=row["signal_value"],
            threshold=row["threshold"],
            created_at=row["created_at"],
        )

    async def get_all(
        self,
        severity: str | None = None,
        failure_type: str | None = None,
    ) -> list[FailureRow]:
        """Get all failures with optional filters.

        Args:
            severity: Filter by severity.
            failure_type: Filter by type.

        Returns:
            List of failures.
        """
        conditions = []
        params: list[Any] = []

        if severity is not None:
            params.append(severity)
            conditions.append(f"severity = ${len(params)}")

        if failure_type is not None:
            params.append(failure_type)
            conditions.append(f"failure_type = ${len(params)}")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        rows = await self._db.fetch(
            f"""
            SELECT id, failure_type, severity, message,
                   conversation_id, turn_id, turn_index,
                   signal_name, signal_value, threshold, created_at
            FROM failures {where_clause}
            ORDER BY created_at DESC
            """,
            *params,
        )

        return [
            FailureRow(
                id=row["id"],
                failure_type=row["failure_type"],
                severity=row["severity"],
                message=row["message"],
                conversation_id=row["conversation_id"],
                turn_id=row["turn_id"],
                turn_index=row["turn_index"],
                signal_name=row["signal_name"],
                signal_value=row["signal_value"],
                threshold=row["threshold"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def get_by_conversation(self, conversation_id: UUID) -> list[FailureRow]:
        """Get all failures for a conversation.

        Args:
            conversation_id: The conversation UUID.

        Returns:
            List of failures for the conversation.
        """
        rows = await self._db.fetch(
            """
            SELECT id, failure_type, severity, message,
                   conversation_id, turn_id, turn_index,
                   signal_name, signal_value, threshold, created_at
            FROM failures WHERE conversation_id = $1
            ORDER BY created_at
            """,
            conversation_id,
        )

        return [
            FailureRow(
                id=row["id"],
                failure_type=row["failure_type"],
                severity=row["severity"],
                message=row["message"],
                conversation_id=row["conversation_id"],
                turn_id=row["turn_id"],
                turn_index=row["turn_index"],
                signal_name=row["signal_name"],
                signal_value=row["signal_value"],
                threshold=row["threshold"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def get_counts_by_severity(self) -> dict[str, int]:
        """Get failure counts grouped by severity.

        Returns:
            Dictionary of severity to count.
        """
        rows = await self._db.fetch(
            """
            SELECT severity, COUNT(*) as count
            FROM failures GROUP BY severity
            """
        )

        return {row["severity"]: row["count"] for row in rows}

    async def get_counts_by_type(self) -> dict[str, int]:
        """Get failure counts grouped by type.

        Returns:
            Dictionary of type to count.
        """
        rows = await self._db.fetch(
            """
            SELECT failure_type, COUNT(*) as count
            FROM failures GROUP BY failure_type
            """
        )

        return {row["failure_type"]: row["count"] for row in rows}

    async def clear(self) -> int:
        """Delete all failures.

        Returns:
            Number of failures deleted.
        """
        count = await self._db.fetchval("SELECT COUNT(*) FROM failures")
        await self._db.execute("DELETE FROM failures")
        return count

    async def count(self) -> int:
        """Get the number of failures.

        Returns:
            Number of failures.
        """
        return await self._db.fetchval("SELECT COUNT(*) FROM failures")
