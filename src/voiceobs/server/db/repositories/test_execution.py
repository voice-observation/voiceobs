"""Test execution repository for database operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import TestExecutionRow


class TestExecutionRepository:
    """Repository for test execution operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the test execution repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    async def create(
        self,
        scenario_id: UUID,
        conversation_id: UUID | None = None,
        status: str = "pending",
    ) -> TestExecutionRow:
        """Create a new test execution.

        Args:
            scenario_id: Test scenario UUID.
            conversation_id: Associated conversation UUID.
            status: Execution status.

        Returns:
            The created test execution row.
        """
        execution_id = uuid4()
        started_at = datetime.utcnow() if status == "running" else None

        await self._db.execute(
            """
            INSERT INTO test_executions (id, scenario_id, conversation_id, status, started_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            execution_id,
            scenario_id,
            conversation_id,
            status,
            started_at,
        )

        row = await self._db.fetchrow(
            """
            SELECT id, scenario_id, conversation_id, status, started_at, completed_at, result_json
            FROM test_executions WHERE id = $1
            """,
            execution_id,
        )

        if row is None:
            raise RuntimeError("Failed to create test execution")

        return TestExecutionRow(
            id=row["id"],
            scenario_id=row["scenario_id"],
            conversation_id=row["conversation_id"],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            result_json=row["result_json"] or {},
        )

    async def get(self, execution_id: UUID) -> TestExecutionRow | None:
        """Get a test execution by UUID.

        Args:
            execution_id: The test execution UUID.

        Returns:
            The test execution row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, scenario_id, conversation_id, status, started_at, completed_at, result_json
            FROM test_executions WHERE id = $1
            """,
            execution_id,
        )

        if row is None:
            return None

        return TestExecutionRow(
            id=row["id"],
            scenario_id=row["scenario_id"],
            conversation_id=row["conversation_id"],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            result_json=row["result_json"] or {},
        )

    async def get_summary(
        self,
        suite_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Get test summary statistics.

        Args:
            suite_id: Filter by test suite UUID.

        Returns:
            Dictionary with summary statistics.
        """
        if suite_id is not None:
            # Get executions for scenarios in this suite
            rows = await self._db.fetch(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (
                        WHERE te.status = 'completed'
                        AND (te.result_json->>'passed')::boolean = true
                    ) as passed,
                    COUNT(*) FILTER (
                        WHERE te.status = 'completed'
                        AND (te.result_json->>'passed')::boolean = false
                    ) as failed,
                    AVG(
                        EXTRACT(EPOCH FROM (te.completed_at - te.started_at)) * 1000
                    ) FILTER (WHERE te.completed_at IS NOT NULL) as avg_duration_ms,
                    AVG((te.result_json->>'avg_latency_ms')::float) FILTER (
                        WHERE te.result_json->>'avg_latency_ms' IS NOT NULL
                    ) as avg_latency_ms
                FROM test_executions te
                JOIN test_scenarios ts ON te.scenario_id = ts.id
                WHERE ts.suite_id = $1 AND te.status = 'completed'
                """,
                suite_id,
            )
        else:
            rows = await self._db.fetch(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (
                        WHERE status = 'completed'
                        AND (result_json->>'passed')::boolean = true
                    ) as passed,
                    COUNT(*) FILTER (
                        WHERE status = 'completed'
                        AND (result_json->>'passed')::boolean = false
                    ) as failed,
                    AVG(
                        EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000
                    ) FILTER (WHERE completed_at IS NOT NULL) as avg_duration_ms,
                    AVG((result_json->>'avg_latency_ms')::float) FILTER (
                        WHERE result_json->>'avg_latency_ms' IS NOT NULL
                    ) as avg_latency_ms
                FROM test_executions
                WHERE status = 'completed'
                """
            )

        if not rows or rows[0]["total"] is None or rows[0]["total"] == 0:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": None,
                "avg_duration_ms": None,
                "avg_latency_ms": None,
            }

        row = rows[0]
        total = row["total"] or 0
        passed = row["passed"] or 0
        failed = row["failed"] or 0
        pass_rate = passed / total if total > 0 else None

        avg_duration = float(row["avg_duration_ms"]) if row["avg_duration_ms"] is not None else None
        avg_latency = float(row["avg_latency_ms"]) if row["avg_latency_ms"] is not None else None

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
            "avg_duration_ms": avg_duration,
            "avg_latency_ms": avg_latency,
        }
