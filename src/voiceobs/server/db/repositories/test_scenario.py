"""Test scenario repository for database operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import TestScenarioRow


class TestScenarioRepository:
    """Repository for test scenario operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the test scenario repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    async def create(
        self,
        suite_id: UUID,
        name: str,
        goal: str,
        persona_json: dict[str, Any] | None = None,
        max_turns: int | None = None,
        timeout: int | None = None,
    ) -> TestScenarioRow:
        """Create a new test scenario.

        Args:
            suite_id: Parent test suite UUID.
            name: Test scenario name.
            goal: Test scenario goal.
            persona_json: Persona configuration.
            max_turns: Maximum number of turns.
            timeout: Timeout in seconds.

        Returns:
            The created test scenario row.
        """
        scenario_id = uuid4()
        await self._db.execute(
            """
            INSERT INTO test_scenarios (id, suite_id, name, goal, persona_json, max_turns, timeout)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            scenario_id,
            suite_id,
            name,
            goal,
            persona_json or {},
            max_turns,
            timeout,
        )

        row = await self._db.fetchrow(
            """
            SELECT id, suite_id, name, goal, persona_json, max_turns, timeout
            FROM test_scenarios WHERE id = $1
            """,
            scenario_id,
        )

        if row is None:
            raise RuntimeError("Failed to create test scenario")

        return TestScenarioRow(
            id=row["id"],
            suite_id=row["suite_id"],
            name=row["name"],
            goal=row["goal"],
            persona_json=row["persona_json"] or {},
            max_turns=row["max_turns"],
            timeout=row["timeout"],
        )

    async def get(self, scenario_id: UUID) -> TestScenarioRow | None:
        """Get a test scenario by UUID.

        Args:
            scenario_id: The test scenario UUID.

        Returns:
            The test scenario row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, suite_id, name, goal, persona_json, max_turns, timeout
            FROM test_scenarios WHERE id = $1
            """,
            scenario_id,
        )

        if row is None:
            return None

        return TestScenarioRow(
            id=row["id"],
            suite_id=row["suite_id"],
            name=row["name"],
            goal=row["goal"],
            persona_json=row["persona_json"] or {},
            max_turns=row["max_turns"],
            timeout=row["timeout"],
        )

    async def list_all(
        self,
        suite_id: UUID | None = None,
    ) -> list[TestScenarioRow]:
        """List test scenarios with optional filtering.

        Args:
            suite_id: Filter by test suite UUID.

        Returns:
            List of test scenarios.
        """
        if suite_id is not None:
            rows = await self._db.fetch(
                """
                SELECT id, suite_id, name, goal, persona_json, max_turns, timeout
                FROM test_scenarios
                WHERE suite_id = $1
                ORDER BY name
                """,
                suite_id,
            )
        else:
            rows = await self._db.fetch(
                """
                SELECT id, suite_id, name, goal, persona_json, max_turns, timeout
                FROM test_scenarios
                ORDER BY name
                """
            )

        return [
            TestScenarioRow(
                id=row["id"],
                suite_id=row["suite_id"],
                name=row["name"],
                goal=row["goal"],
                persona_json=row["persona_json"] or {},
                max_turns=row["max_turns"],
                timeout=row["timeout"],
            )
            for row in rows
        ]

    async def update(
        self,
        scenario_id: UUID,
        name: str | None = None,
        goal: str | None = None,
        persona_json: dict[str, Any] | None = None,
        max_turns: int | None = None,
        timeout: int | None = None,
    ) -> TestScenarioRow | None:
        """Update a test scenario.

        Args:
            scenario_id: The test scenario UUID.
            name: New name (optional).
            goal: New goal (optional).
            persona_json: New persona configuration (optional).
            max_turns: New max turns (optional).
            timeout: New timeout (optional).

        Returns:
            The updated test scenario row, or None if not found.
        """
        updates = []
        params: list[Any] = []
        param_idx = 1

        if name is not None:
            updates.append(f"name = ${param_idx}")
            params.append(name)
            param_idx += 1

        if goal is not None:
            updates.append(f"goal = ${param_idx}")
            params.append(goal)
            param_idx += 1

        if persona_json is not None:
            updates.append(f"persona_json = ${param_idx}")
            params.append(persona_json)
            param_idx += 1

        if max_turns is not None:
            updates.append(f"max_turns = ${param_idx}")
            params.append(max_turns)
            param_idx += 1

        if timeout is not None:
            updates.append(f"timeout = ${param_idx}")
            params.append(timeout)
            param_idx += 1

        if not updates:
            # No updates, just return the existing scenario
            return await self.get(scenario_id)

        params.append(scenario_id)
        await self._db.execute(
            f"""
            UPDATE test_scenarios
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
            """,
            *params,
        )

        return await self.get(scenario_id)

    async def delete(self, scenario_id: UUID) -> bool:
        """Delete a test scenario.

        Args:
            scenario_id: The test scenario UUID.

        Returns:
            True if deleted, False if not found.
        """
        result = await self._db.execute(
            """
            DELETE FROM test_scenarios WHERE id = $1
            """,
            scenario_id,
        )
        return result == "DELETE 1"
