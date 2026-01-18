"""Failure model for database operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class FailureRow:
    """Represents a failure row in the database."""

    id: UUID
    failure_type: str
    severity: str
    message: str
    conversation_id: UUID | None
    turn_id: UUID | None
    turn_index: int | None
    signal_name: str | None
    signal_value: float | None
    threshold: float | None
    created_at: datetime | None = None

