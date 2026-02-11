"""Test scenario repository for database operations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import TestScenarioRow

if TYPE_CHECKING:
    from voiceobs.server.db.repositories.persona import PersonaRepository


class TestScenarioRepository:
    """Repository for test scenario operations."""

    def __init__(self, db: Database, persona_repo: PersonaRepository) -> None:
        """Initialize the test scenario repository.

        Args:
            db: Database connection manager.
            persona_repo: Persona repository for validation.
        """
        self._db = db
        self._persona_repo = persona_repo

    @staticmethod
    def _compute_status(name: str, goal: str) -> str:
        """Compute scenario status based on required fields.

        Returns 'ready' if name and goal are both present and non-empty.
        Returns 'draft' otherwise.

        Args:
            name: The scenario name.
            goal: The scenario goal.

        Returns:
            'ready' if both name and goal are present, 'draft' otherwise.
        """
        if name and name.strip() and goal and goal.strip():
            return "ready"
        return "draft"

    def _row_to_model(self, row: Any) -> TestScenarioRow:
        """Convert a database row to a TestScenarioRow model.

        Args:
            row: Database row with scenario data.

        Returns:
            TestScenarioRow model instance.
        """

        def parse_json_list(value: Any) -> list[str]:
            """Parse a JSON list from string or return as-is if already a list."""
            if value is None:
                return []
            if isinstance(value, str):
                return json.loads(value)
            return value

        persona_traits = parse_json_list(row.get("persona_traits"))
        # Auto-detect is_manual: True if no persona_traits (manually created)
        is_manual = len(persona_traits) == 0

        return TestScenarioRow(
            id=row["id"],
            suite_id=row["suite_id"],
            name=row["name"],
            goal=row["goal"],
            persona_id=row["persona_id"],
            max_turns=row["max_turns"],
            timeout=row["timeout"],
            intent=row.get("intent"),
            persona_traits=persona_traits,
            persona_match_score=row.get("persona_match_score"),
            caller_behaviors=parse_json_list(row.get("caller_behaviors")),
            tags=parse_json_list(row.get("tags")),
            status=row.get("status") or "draft",
            is_manual=is_manual,
        )

    async def create(
        self,
        suite_id: UUID,
        name: str,
        goal: str,
        persona_id: UUID,
        max_turns: int | None = None,
        timeout: int | None = None,
        intent: str | None = None,
        persona_traits: list[str] | None = None,
        persona_match_score: float | None = None,
        caller_behaviors: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> TestScenarioRow:
        """Create a new test scenario.

        Args:
            suite_id: Parent test suite UUID.
            name: Test scenario name.
            goal: Test scenario goal.
            persona_id: Persona UUID reference.
            max_turns: Maximum number of turns.
            timeout: Timeout in seconds.
            intent: LLM-identified intent for this scenario.
            persona_traits: Desired persona traits for this scenario.
            persona_match_score: How well the assigned persona matches desired traits.
            caller_behaviors: Test steps for caller.
            tags: Tags for categorization.

        Returns:
            The created test scenario row.

        Raises:
            ValueError: If persona_id does not reference an existing active persona.
        """
        # Validate that persona exists and is active
        # TODO: Once test scenarios are org-scoped, pass org_id here
        persona = await self._persona_repo._get_by_id_unchecked(persona_id)
        if persona is None:
            raise ValueError(f"Persona {persona_id} not found")
        if not persona.is_active:
            raise ValueError(f"Persona {persona_id} is not active")

        scenario_id = uuid4()
        traits_json = json.dumps(persona_traits or [])
        caller_behaviors_json = json.dumps(caller_behaviors or [])
        tags_json = json.dumps(tags or [])
        # Compute status: ready if name and goal are present
        status = self._compute_status(name, goal)

        await self._db.execute(
            """
            INSERT INTO test_scenarios (
                id, suite_id, name, goal, persona_id, max_turns, timeout,
                intent, persona_traits, persona_match_score,
                caller_behaviors, tags, status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            scenario_id,
            suite_id,
            name,
            goal,
            persona_id,
            max_turns,
            timeout,
            intent,
            traits_json,
            persona_match_score,
            caller_behaviors_json,
            tags_json,
            status,
        )

        row = await self._db.fetchrow(
            """
            SELECT id, suite_id, name, goal, persona_id, max_turns, timeout,
                   intent, persona_traits, persona_match_score,
                   caller_behaviors, tags, status
            FROM test_scenarios WHERE id = $1
            """,
            scenario_id,
        )

        if row is None:
            raise RuntimeError("Failed to create test scenario")

        return self._row_to_model(row)

    async def get(self, scenario_id: UUID) -> TestScenarioRow | None:
        """Get a test scenario by UUID.

        Args:
            scenario_id: The test scenario UUID.

        Returns:
            The test scenario row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, suite_id, name, goal, persona_id, max_turns, timeout,
                   intent, persona_traits, persona_match_score,
                   caller_behaviors, tags, status
            FROM test_scenarios WHERE id = $1
            """,
            scenario_id,
        )

        if row is None:
            return None

        return self._row_to_model(row)

    async def list_all(
        self,
        suite_id: UUID | None = None,
        status: str | None = None,
        tags: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[TestScenarioRow]:
        """List test scenarios with optional filtering and pagination.

        Args:
            suite_id: Filter by test suite UUID.
            status: Filter by status (ready or draft).
            tags: Filter by tags (returns scenarios with ANY of the specified tags).
            limit: Maximum number of results to return.
            offset: Number of results to skip.

        Returns:
            List of test scenarios.
        """
        base_query = """
            SELECT id, suite_id, name, goal, persona_id, max_turns, timeout,
                   intent, persona_traits, persona_match_score,
                   caller_behaviors, tags, status
            FROM test_scenarios
        """
        conditions = []
        params: list[Any] = []
        param_idx = 1

        if suite_id is not None:
            conditions.append(f"suite_id = ${param_idx}")
            params.append(suite_id)
            param_idx += 1

        if status is not None:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        if tags is not None and len(tags) > 0:
            # Use PostgreSQL JSONB overlap operator to find scenarios
            # with ANY of the specified tags
            conditions.append(f"tags ?| ${param_idx}")
            params.append(tags)
            param_idx += 1

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        base_query += " ORDER BY name"

        if limit is not None:
            base_query += f" LIMIT ${param_idx}"
            params.append(limit)
            param_idx += 1

        if offset is not None:
            base_query += f" OFFSET ${param_idx}"
            params.append(offset)
            param_idx += 1

        rows = await self._db.fetch(base_query, *params)

        return [self._row_to_model(row) for row in rows]

    async def count(
        self,
        suite_id: UUID | None = None,
        status: str | None = None,
        tags: list[str] | None = None,
    ) -> int:
        """Count test scenarios with optional filtering.

        Args:
            suite_id: Filter by test suite UUID.
            status: Filter by status (ready or draft).
            tags: Filter by tags (returns scenarios with ANY of the specified tags).

        Returns:
            Total count of matching test scenarios.
        """
        base_query = "SELECT COUNT(*) FROM test_scenarios"
        conditions = []
        params: list[Any] = []
        param_idx = 1

        if suite_id is not None:
            conditions.append(f"suite_id = ${param_idx}")
            params.append(suite_id)
            param_idx += 1

        if status is not None:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        if tags is not None and len(tags) > 0:
            conditions.append(f"tags ?| ${param_idx}")
            params.append(tags)
            param_idx += 1

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        result = await self._db.fetchval(base_query, *params)
        return result or 0

    async def update(
        self,
        scenario_id: UUID,
        suite_id: UUID | None = None,
        name: str | None = None,
        goal: str | None = None,
        persona_id: UUID | None = None,
        max_turns: int | None = None,
        timeout: int | None = None,
        intent: str | None = None,
        persona_traits: list[str] | None = None,
        persona_match_score: float | None = None,
        caller_behaviors: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> TestScenarioRow | None:
        """Update a test scenario.

        Args:
            scenario_id: The test scenario UUID.
            suite_id: New parent test suite UUID (optional, for moving scenario).
            name: New name (optional).
            goal: New goal (optional).
            persona_id: New persona UUID reference (optional).
            max_turns: New max turns (optional).
            timeout: New timeout (optional).
            intent: New intent (optional).
            persona_traits: New persona traits (optional).
            persona_match_score: New persona match score (optional).
            caller_behaviors: New caller behaviors (optional).
            tags: New tags (optional).

        Returns:
            The updated test scenario row, or None if not found.

        Raises:
            ValueError: If persona_id does not reference an existing active persona.
        """
        # Validate persona if provided
        if persona_id is not None:
            # TODO: Once test scenarios are org-scoped, pass org_id here
            persona = await self._persona_repo._get_by_id_unchecked(persona_id)
            if persona is None:
                raise ValueError(f"Persona {persona_id} not found")
            if not persona.is_active:
                raise ValueError(f"Persona {persona_id} is not active")

        # Fetch current scenario if name or goal is being updated (for status computation)
        current_scenario = None
        if name is not None or goal is not None:
            current_scenario = await self.get(scenario_id)
            if current_scenario is None:
                return None

        updates = []
        params: list[Any] = []
        param_idx = 1

        if name is not None:
            updates.append(f"name = ${param_idx}")
            params.append(name)
            param_idx += 1

        if suite_id is not None:
            updates.append(f"suite_id = ${param_idx}")
            params.append(suite_id)
            param_idx += 1

        if goal is not None:
            updates.append(f"goal = ${param_idx}")
            params.append(goal)
            param_idx += 1

        if persona_id is not None:
            updates.append(f"persona_id = ${param_idx}")
            params.append(persona_id)
            param_idx += 1

        if max_turns is not None:
            updates.append(f"max_turns = ${param_idx}")
            params.append(max_turns)
            param_idx += 1

        if timeout is not None:
            updates.append(f"timeout = ${param_idx}")
            params.append(timeout)
            param_idx += 1

        if intent is not None:
            updates.append(f"intent = ${param_idx}")
            params.append(intent)
            param_idx += 1

        if persona_traits is not None:
            updates.append(f"persona_traits = ${param_idx}")
            params.append(json.dumps(persona_traits))
            param_idx += 1

        if persona_match_score is not None:
            updates.append(f"persona_match_score = ${param_idx}")
            params.append(persona_match_score)
            param_idx += 1

        if caller_behaviors is not None:
            updates.append(f"caller_behaviors = ${param_idx}")
            params.append(json.dumps(caller_behaviors))
            param_idx += 1

        if tags is not None:
            updates.append(f"tags = ${param_idx}")
            params.append(json.dumps(tags))
            param_idx += 1

        # Auto-compute status if name or goal changed
        if current_scenario is not None:
            new_name = name if name is not None else current_scenario.name
            new_goal = goal if goal is not None else current_scenario.goal
            new_status = self._compute_status(new_name, new_goal)
            updates.append(f"status = ${param_idx}")
            params.append(new_status)
            param_idx += 1

        if not updates:
            # No updates, just return the existing scenario
            return await self.get(scenario_id)

        params.append(scenario_id)
        await self._db.execute(
            f"""
            UPDATE test_scenarios
            SET {", ".join(updates)}
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
