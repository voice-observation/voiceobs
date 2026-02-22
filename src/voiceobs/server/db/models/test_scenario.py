"""Test scenario model for database operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class TestScenarioRow:
    """Represents a test scenario row in the database."""

    id: UUID
    suite_id: UUID
    name: str
    goal: str
    persona_id: UUID
    persona_name: str | None = None  # Resolved from personas table for display
    max_turns: int | None = None
    timeout: int | None = None
    intent: str | None = None  # LLM-identified intent
    persona_traits: list[str] = field(default_factory=list)  # Desired persona traits
    persona_match_score: float | None = None  # How well persona matches traits
    # New CRUD fields
    caller_behaviors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    status: str = "draft"
    is_manual: bool = False  # True for manually created scenarios, False for AI-generated
