"""Test execution repository for database operations."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import TestExecutionRow

_JSONB_COLUMNS = frozenset({"transcript", "evaluation_result"})
_COLUMNS = (
    "id, org_id, suite_run_id, scenario_id, conversation_id, status, attempt, "
    "max_attempts, audio_url, transcript, evaluation_result, error_message, "
    "duration_seconds, started_at, completed_at, result_json, created_at"
)


class TestExecutionRepository:
    """Repository for test execution operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the test execution repository."""
        self._db = db

    async def create(
        self,
        org_id: UUID,
        suite_run_id: UUID,
        scenario_id: UUID,
        status: str = "pending",
    ) -> TestExecutionRow:
        """Create a new test execution."""
        execution_id = uuid4()
        started_at = datetime.utcnow() if status == "running" else None

        await self._db.execute(
            """
            INSERT INTO test_executions (
                id, org_id, suite_run_id, scenario_id, status, started_at
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            execution_id,
            org_id,
            suite_run_id,
            scenario_id,
            status,
            started_at,
        )

        row = await self._db.fetchrow(
            f"SELECT {_COLUMNS} FROM test_executions WHERE id = $1",
            execution_id,
        )

        if row is None:
            raise RuntimeError("Failed to create test execution")

        return TestExecutionRow.from_row(dict(row))

    async def get(self, execution_id: UUID, org_id: UUID) -> TestExecutionRow | None:
        """Get a test execution by ID and org_id."""
        row = await self._db.fetchrow(
            f"SELECT {_COLUMNS} FROM test_executions WHERE id = $1 AND org_id = $2",
            execution_id,
            org_id,
        )
        return TestExecutionRow.from_row(dict(row)) if row else None

    async def get_by_id(self, execution_id: UUID) -> TestExecutionRow | None:
        """Get a test execution by ID (legacy, no org filter)."""
        row = await self._db.fetchrow(
            f"SELECT {_COLUMNS} FROM test_executions WHERE id = $1",
            execution_id,
        )
        return TestExecutionRow.from_row(dict(row)) if row else None

    async def update(
        self, execution_id: UUID, org_id: UUID, updates: dict[str, Any]
    ) -> TestExecutionRow | None:
        """Update a test execution."""
        allowed = {
            "status",
            "conversation_id",
            "audio_url",
            "transcript",
            "evaluation_result",
            "error_message",
            "duration_seconds",
            "started_at",
            "completed_at",
        }
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return await self.get(execution_id, org_id)

        set_clauses = []
        params: list[Any] = []
        for idx, (key, value) in enumerate(filtered.items(), start=1):
            if key in _JSONB_COLUMNS and value is not None:
                set_clauses.append(f"{key} = ${idx}::jsonb")
                params.append(json.dumps(value))
            else:
                set_clauses.append(f"{key} = ${idx}")
                params.append(value)

        idx_exec = len(params) + 1
        idx_org = len(params) + 2
        params.append(execution_id)
        params.append(org_id)

        query = (
            f"UPDATE test_executions SET {', '.join(set_clauses)} "
            f"WHERE id = ${idx_exec} AND org_id = ${idx_org}"
        )
        await self._db.execute(query, *params)

        return await self.get(execution_id, org_id)

    async def list_by_suite_run(self, org_id: UUID, suite_run_id: UUID) -> list[TestExecutionRow]:
        """List all executions for a suite run."""
        rows = await self._db.fetch(
            f"SELECT {_COLUMNS} FROM test_executions "
            f"WHERE org_id = $1 AND suite_run_id = $2 ORDER BY created_at ASC",
            org_id,
            suite_run_id,
        )
        return [TestExecutionRow.from_row(dict(row)) for row in rows]

    async def list_by_scenario(
        self, org_id: UUID, scenario_id: UUID, limit: int = 50
    ) -> list[TestExecutionRow]:
        """List executions for a scenario, newest first (for run history)."""
        rows = await self._db.fetch(
            f"SELECT {_COLUMNS} FROM test_executions "
            f"WHERE org_id = $1 AND scenario_id = $2 ORDER BY created_at DESC LIMIT $3",
            org_id,
            scenario_id,
            limit,
        )
        return [TestExecutionRow.from_row(dict(row)) for row in rows]

    async def get_summary(
        self,
        suite_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Get test summary statistics.

        Uses evaluation_result->>'passed' when available, else result_json->>'passed'.
        """
        passed_expr = (
            "COALESCE((te.evaluation_result->>'passed')::boolean, "
            "(te.result_json->>'passed')::boolean)"
        )
        if suite_id is not None:
            rows = await self._db.fetch(
                f"""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (
                        WHERE te.status = 'completed'
                        AND {passed_expr} = true
                    ) as passed,
                    COUNT(*) FILTER (
                        WHERE te.status = 'completed'
                        AND {passed_expr} = false
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
                        AND COALESCE((evaluation_result->>'passed')::boolean,
                            (result_json->>'passed')::boolean) = true
                    ) as passed,
                    COUNT(*) FILTER (
                        WHERE status = 'completed'
                        AND COALESCE((evaluation_result->>'passed')::boolean,
                            (result_json->>'passed')::boolean) = false
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
