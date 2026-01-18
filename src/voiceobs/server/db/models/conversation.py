"""Conversation model for database operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class ConversationRow:
    """Represents a conversation row in the database."""

    id: UUID
    conversation_id: str  # External conversation ID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    audio_path: str | None = None
    audio_metadata: dict[str, Any] = field(default_factory=dict)

