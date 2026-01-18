"""Turn model for database operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class TurnRow:
    """Represents a turn row in the database."""

    id: UUID
    turn_id: str | None
    conversation_id: UUID
    span_id: UUID
    actor: str
    turn_index: int | None
    duration_ms: float | None
    transcript: str | None
    attributes: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None

