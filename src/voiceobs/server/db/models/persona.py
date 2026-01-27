"""Persona model for database operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class PersonaRow:
    """Represents a persona row in the database."""

    id: UUID
    name: str
    aggression: float
    patience: float
    verbosity: float
    tts_provider: str
    description: str | None = None
    traits: list[str] = field(default_factory=list)
    tts_config: dict[str, Any] = field(default_factory=dict)
    preview_audio_url: str | None = None
    preview_audio_text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    is_active: bool = True
