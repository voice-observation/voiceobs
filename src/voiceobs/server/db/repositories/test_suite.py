"""Test suite repository for database operations."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import TestSuiteRow

# Fields that require JSONB casting in PostgreSQL
_JSONB_FIELDS = frozenset({"test_scopes", "edge_cases"})


def _parse_jsonb(value: Any) -> Any:
    """Parse JSONB value if it's returned as a string."""
    if isinstance(value, str):
        return json.loads(value)
    return value


class TestSuiteRepository:
    """Repository for test suite operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the test suite repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    async def create(
        self,
        name: str,
        description: str | None = None,
        agent_id: UUID | None = None,
        test_scopes: list[str] | None = None,
        thoroughness: int | None = None,
        edge_cases: list[str] | None = None,
        evaluation_strictness: str | None = None,
    ) -> TestSuiteRow:
        """Create a new test suite.

        Args:
            name: Test suite name.
            description: Test suite description.
            agent_id: Agent UUID (immutable after creation).
            test_scopes: Test scopes to include.
            thoroughness: Test thoroughness level (0-2).
            edge_cases: Edge cases to include.
            evaluation_strictness: Evaluation strictness level.

        Returns:
            The created test suite row.
        """
        suite_id = uuid4()
        # Use defaults if not provided
        scopes = test_scopes if test_scopes is not None else ["core_flows", "common_mistakes"]
        thorough = thoroughness if thoroughness is not None else 1
        edges = edge_cases if edge_cases is not None else []
        strictness = evaluation_strictness if evaluation_strictness is not None else "balanced"

        await self._db.execute(
            """
            INSERT INTO test_suites (
                id, name, description, status, agent_id,
                test_scopes, thoroughness, edge_cases, evaluation_strictness
            )
            VALUES ($1, $2, $3, 'pending', $4, $5::jsonb, $6, $7::jsonb, $8)
            """,
            suite_id,
            name,
            description,
            agent_id,
            json.dumps(scopes),
            thorough,
            json.dumps(edges),
            strictness,
        )

        row = await self._db.fetchrow(
            """
            SELECT id, name, description, status, generation_error, agent_id, test_scopes,
                   thoroughness, edge_cases, evaluation_strictness, created_at
            FROM test_suites WHERE id = $1
            """,
            suite_id,
        )

        if row is None:
            raise RuntimeError("Failed to create test suite")

        return TestSuiteRow(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
            generation_error=row["generation_error"],
            agent_id=row["agent_id"],
            test_scopes=_parse_jsonb(row["test_scopes"]),
            thoroughness=row["thoroughness"],
            edge_cases=_parse_jsonb(row["edge_cases"]),
            evaluation_strictness=row["evaluation_strictness"],
            created_at=row["created_at"],
        )

    async def get(self, suite_id: UUID) -> TestSuiteRow | None:
        """Get a test suite by UUID.

        Args:
            suite_id: The test suite UUID.

        Returns:
            The test suite row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, name, description, status, generation_error, agent_id, test_scopes,
                   thoroughness, edge_cases, evaluation_strictness, created_at
            FROM test_suites WHERE id = $1
            """,
            suite_id,
        )

        if row is None:
            return None

        return TestSuiteRow(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
            generation_error=row["generation_error"],
            agent_id=row["agent_id"],
            test_scopes=_parse_jsonb(row["test_scopes"]),
            thoroughness=row["thoroughness"],
            edge_cases=_parse_jsonb(row["edge_cases"]),
            evaluation_strictness=row["evaluation_strictness"],
            created_at=row["created_at"],
        )

    async def list_all(self) -> list[TestSuiteRow]:
        """List all test suites.

        Returns:
            List of test suites.
        """
        rows = await self._db.fetch(
            """
            SELECT id, name, description, status, generation_error, agent_id, test_scopes,
                   thoroughness, edge_cases, evaluation_strictness, created_at
            FROM test_suites
            ORDER BY created_at DESC
            """
        )

        return [
            TestSuiteRow(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                status=row["status"],
                generation_error=row["generation_error"],
                agent_id=row["agent_id"],
                test_scopes=_parse_jsonb(row["test_scopes"]),
                thoroughness=row["thoroughness"],
                edge_cases=_parse_jsonb(row["edge_cases"]),
                evaluation_strictness=row["evaluation_strictness"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def update(
        self,
        suite_id: UUID,
        updates: dict[str, Any],
    ) -> TestSuiteRow | None:
        """Update a test suite.

        Args:
            suite_id: The test suite UUID.
            updates: Dictionary of fields to update (from model_dump(exclude_unset=True)).

        Returns:
            The updated test suite row, or None if not found.
        """
        if not updates:
            return await self.get(suite_id)

        set_clauses = []
        params: list[Any] = []

        for idx, (column, value) in enumerate(updates.items(), start=1):
            if column in _JSONB_FIELDS:
                set_clauses.append(f"{column} = ${idx}::jsonb")
                params.append(json.dumps(value))
            else:
                set_clauses.append(f"{column} = ${idx}")
                params.append(value)

        params.append(suite_id)
        await self._db.execute(
            f"""
            UPDATE test_suites
            SET {", ".join(set_clauses)}
            WHERE id = ${len(params)}
            """,
            *params,
        )

        return await self.get(suite_id)

    async def delete(self, suite_id: UUID) -> bool:
        """Delete a test suite.

        Args:
            suite_id: The test suite UUID.

        Returns:
            True if deleted, False if not found.
        """
        result = await self._db.execute(
            """
            DELETE FROM test_suites WHERE id = $1
            """,
            suite_id,
        )
        return result == "DELETE 1"
