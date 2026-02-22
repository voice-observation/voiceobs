"""Agent model for database operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class AgentRow:
    """Represents an agent row in the database."""

    id: UUID
    org_id: UUID  # Organization this agent belongs to
    name: str
    goal: str
    agent_type: str = "phone"  # "phone", "web", "email", etc.
    contact_info: dict[str, Any] = field(default_factory=dict)  # JSONB contact information
    supported_intents: list[str] = field(default_factory=list)
    context: str | None = None  # Domain-specific context about what the agent does
    connection_status: str = "pending"  # pending, saved, connecting, verified, failed
    verification_attempts: int = 0
    last_verification_at: datetime | None = None
    verification_error: str | None = None
    verification_transcript: list[dict[str, str]] | None = None
    verification_reasoning: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    is_active: bool = True

    # Convenience properties for common contact methods
    @property
    def phone_number(self) -> str | None:
        """Get phone number from contact_info (for phone agents)."""
        return self.contact_info.get("phone_number") if self.agent_type == "phone" else None

    @property
    def web_url(self) -> str | None:
        """Get web URL from contact_info (for web agents)."""
        return self.contact_info.get("web_url") if self.agent_type == "web" else None
