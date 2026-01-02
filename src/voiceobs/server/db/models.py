"""Database models for voiceobs server.

These dataclasses represent rows in the PostgreSQL database tables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass
class ConversationRow:
    """Represents a conversation row in the database."""

    id: UUID
    conversation_id: str  # External conversation ID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    audio_path: str | None = None
    audio_metadata: dict[str, Any] = field(default_factory=dict)


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


@dataclass
class TestSuiteRow:
    """Represents a test suite row in the database."""

    id: UUID
    name: str
    description: str | None = None
    status: str = "pending"  # pending, running, completed
    created_at: datetime | None = None


@dataclass
class TestScenarioRow:
    """Represents a test scenario row in the database."""

    id: UUID
    suite_id: UUID
    name: str
    goal: str
    persona_json: dict[str, Any] = field(default_factory=dict)
    max_turns: int | None = None
    timeout: int | None = None


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
