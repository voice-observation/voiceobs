"""Test suite model for database operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class TestSuiteRow:
    """Represents a test suite row in the database."""

    id: UUID
    org_id: UUID  # Organization this test suite belongs to
    name: str
    description: str | None = None
    status: str = "pending"  # pending, generating, ready, generation_failed, running, completed
    generation_error: str | None = None  # Error message if generation failed
    agent_id: UUID | None = None
    test_scopes: list[str] | None = None
    thoroughness: int = 1  # 0: Light, 1: Standard, 2: Exhaustive
    edge_cases: list[str] | None = None
    evaluation_strictness: str = "balanced"  # strict, balanced, flexible
    created_at: datetime | None = None
