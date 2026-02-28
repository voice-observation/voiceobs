"""Test suite run repository for database operations."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import TestSuiteRunRow

logger = logging.getLogger(__name__)

_COLUMNS = (
    "id, org_id, suite_id, status, total_scenarios, completed_scenarios, "
    "failed_scenarios, triggered_by, started_at, completed_at, created_at"
)


class TestSuiteRunRepository:
    """Repository for test suite run operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the test suite run repository."""
        self._db = db

    async def create(
        self,
        org_id: UUID,
        suite_id: UUID,
        total_scenarios: int,
        triggered_by: str | None = None,
    ) -> TestSuiteRunRow:
        """Create a new test suite run."""
        run_id = uuid4()

        await self._db.execute(
            """
            INSERT INTO test_suite_runs (id, org_id, suite_id, total_scenarios, triggered_by)
            VALUES ($1, $2, $3, $4, $5)
            """,
            run_id,
            org_id,
            suite_id,
            total_scenarios,
            triggered_by,
        )

        row = await self._db.fetchrow(
            f"SELECT {_COLUMNS} FROM test_suite_runs WHERE id = $1",
            run_id,
        )

        if row is None:
            raise RuntimeError("Failed to create test suite run")

        return TestSuiteRunRow.from_row(dict(row))

    async def get(self, run_id: UUID, org_id: UUID) -> TestSuiteRunRow | None:
        """Get a test suite run by ID and org_id."""
        row = await self._db.fetchrow(
            f"SELECT {_COLUMNS} FROM test_suite_runs WHERE id = $1 AND org_id = $2",
            run_id,
            org_id,
        )
        return TestSuiteRunRow.from_row(dict(row)) if row else None

    async def update(
        self, run_id: UUID, org_id: UUID, updates: dict[str, Any]
    ) -> TestSuiteRunRow | None:
        """Update a test suite run."""
        allowed = {
            "status",
            "completed_scenarios",
            "failed_scenarios",
            "started_at",
            "completed_at",
        }
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return await self.get(run_id, org_id)

        set_clauses = []
        params: list[Any] = []
        for idx, (key, value) in enumerate(filtered.items(), start=1):
            set_clauses.append(f"{key} = ${idx}")
            params.append(value)

        idx_run = len(params) + 1
        idx_org = len(params) + 2
        params.append(run_id)
        params.append(org_id)

        query = (
            f"UPDATE test_suite_runs SET {', '.join(set_clauses)} "
            f"WHERE id = ${idx_run} AND org_id = ${idx_org}"
        )
        await self._db.execute(query, *params)

        return await self.get(run_id, org_id)

    async def increment_completed(self, run_id: UUID, org_id: UUID) -> TestSuiteRunRow | None:
        """Atomically increment completed_scenarios."""
        await self._db.execute(
            "UPDATE test_suite_runs SET completed_scenarios = completed_scenarios + 1 "
            "WHERE id = $1 AND org_id = $2",
            run_id,
            org_id,
        )
        return await self.get(run_id, org_id)

    async def increment_failed(self, run_id: UUID, org_id: UUID) -> TestSuiteRunRow | None:
        """Atomically increment failed_scenarios."""
        await self._db.execute(
            "UPDATE test_suite_runs SET failed_scenarios = failed_scenarios + 1 "
            "WHERE id = $1 AND org_id = $2",
            run_id,
            org_id,
        )
        return await self.get(run_id, org_id)

    async def list_by_suite(self, org_id: UUID, suite_id: UUID) -> list[TestSuiteRunRow]:
        """List all suite runs for a suite."""
        rows = await self._db.fetch(
            f"SELECT {_COLUMNS} FROM test_suite_runs "
            f"WHERE org_id = $1 AND suite_id = $2 ORDER BY created_at DESC",
            org_id,
            suite_id,
        )
        return [TestSuiteRunRow.from_row(dict(row)) for row in rows]
