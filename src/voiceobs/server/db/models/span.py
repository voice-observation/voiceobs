"""Span model for database operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class SpanRow:
    """Represents a span row in the database."""

    id: UUID
    name: str
    start_time: datetime | None
    end_time: datetime | None
    duration_ms: float | None
    attributes: dict[str, Any]
    trace_id: str | None
    span_id: str | None
    parent_span_id: str | None
    conversation_id: UUID | None
    created_at: datetime | None = None

