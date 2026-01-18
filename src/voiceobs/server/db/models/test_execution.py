"""Test execution model for database operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class TestExecutionRow:
    """Represents a test execution row in the database."""

    id: UUID
    scenario_id: UUID
    conversation_id: UUID | None = None
    status: str = "pending"  # pending, running, completed, failed
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result_json: dict[str, Any] = field(default_factory=dict)

