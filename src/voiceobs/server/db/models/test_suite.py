"""Test suite model for database operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class TestSuiteRow:
    """Represents a test suite row in the database."""

    id: UUID
    name: str
    description: str | None = None
    status: str = "pending"  # pending, running, completed
    created_at: datetime | None = None

