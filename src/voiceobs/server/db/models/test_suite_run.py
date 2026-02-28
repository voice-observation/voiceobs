"""Test suite run model for database operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class TestSuiteRunRow:
    """Represents a test suite run row in the database."""

    id: UUID
    org_id: UUID
    suite_id: UUID
    total_scenarios: int
    status: str = "pending"  # pending, running, completed, failed, cancelled
    completed_scenarios: int = 0
    failed_scenarios: int = 0
    triggered_by: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> TestSuiteRunRow:
        """Create a TestSuiteRunRow from a database row."""
        return cls(
            id=row["id"],
            org_id=row["org_id"],
            suite_id=row["suite_id"],
            status=row["status"],
            total_scenarios=row["total_scenarios"],
            completed_scenarios=row["completed_scenarios"],
            failed_scenarios=row["failed_scenarios"],
            triggered_by=row["triggered_by"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            created_at=row["created_at"],
        )
