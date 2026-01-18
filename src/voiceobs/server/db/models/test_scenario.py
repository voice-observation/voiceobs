"""Test scenario model for database operations."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass
class TestScenarioRow:
    """Represents a test scenario row in the database."""

    id: UUID
    suite_id: UUID
    name: str
    goal: str
    persona_id: UUID
    max_turns: int | None = None
    timeout: int | None = None

