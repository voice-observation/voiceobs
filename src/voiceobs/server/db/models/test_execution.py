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
    org_id: UUID
    suite_run_id: UUID
    scenario_id: UUID
    conversation_id: UUID | None = None
    status: str = "pending"  # pending, queued, calling, evaluating, completed, failed
    attempt: int = 1
    max_attempts: int = 3
    audio_url: str | None = None
    transcript: list[dict[str, Any]] | None = None
    evaluation_result: dict[str, Any] | None = None
    error_message: str | None = None
    duration_seconds: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result_json: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> TestExecutionRow:
        """Create a TestExecutionRow from a database row."""
        from voiceobs.server.utils.json_utils import parse_jsonb_dict, parse_jsonb_list

        return cls(
            id=row["id"],
            org_id=row["org_id"],
            suite_run_id=row["suite_run_id"],
            scenario_id=row["scenario_id"],
            conversation_id=row.get("conversation_id"),
            status=row["status"],
            attempt=row.get("attempt", 1),
            max_attempts=row.get("max_attempts", 3),
            audio_url=row.get("audio_url"),
            transcript=parse_jsonb_list(row.get("transcript")),
            evaluation_result=parse_jsonb_dict(row.get("evaluation_result")),
            error_message=row.get("error_message"),
            duration_seconds=row.get("duration_seconds"),
            started_at=row.get("started_at"),
            completed_at=row.get("completed_at"),
            result_json=parse_jsonb_dict(row.get("result_json")) or {},
            created_at=row.get("created_at"),
        )
