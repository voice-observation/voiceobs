"""Agent response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class AgentResponse(BaseModel):
    """Response model for agent details."""

    id: str = Field(..., description="Agent UUID")
    name: str = Field(..., description="Agent name")
    agent_type: str = Field(default="phone", description="Agent type: phone, web, etc.")
    contact_info: dict[str, Any] = Field(..., description="Contact information (JSONB)")
    # Convenience fields for backward compatibility and ease of use
    phone_number: str | None = Field(None, description="Phone number from contact_info (for phone agents)")
    web_url: str | None = Field(None, description="Web URL from contact_info (for web agents)")
    goal: str = Field(..., description="Agent goal")
    supported_intents: list[str] = Field(..., description="Supported intents")
    connection_status: str = Field(..., description="Connection status")
    verification_attempts: int = Field(..., description="Number of verification attempts")
    last_verification_at: datetime | None = Field(None, description="Last verification timestamp")
    verification_error: str | None = Field(None, description="Verification error if failed")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    created_by: str | None = Field(None, description="Creator identifier")
    is_active: bool = Field(..., description="Whether agent is active")

    @model_validator(mode='after')
    def populate_convenience_fields(self) -> 'AgentResponse':
        """Populate convenience fields from contact_info."""
        self.phone_number = self.contact_info.get("phone_number")
        self.web_url = self.contact_info.get("web_url")
        return self


class AgentListItem(BaseModel):
    """Simplified agent model for list responses."""

    id: str = Field(..., description="Agent UUID")
    name: str = Field(..., description="Agent name")
    agent_type: str = Field(..., description="Agent type")
    # Convenience fields extracted from contact_info
    phone_number: str | None = Field(None, description="Phone number from contact_info (for phone agents)")
    web_url: str | None = Field(None, description="Web URL from contact_info (for web agents)")
    goal: str = Field(..., description="Agent goal")
    connection_status: str = Field(..., description="Connection status")
    is_active: bool = Field(..., description="Whether agent is active")
    created_at: datetime | None = Field(None, description="Creation timestamp")


class AgentsListResponse(BaseModel):
    """Response model for listing agents."""

    count: int = Field(..., description="Total number of agents")
    agents: list[AgentListItem] = Field(..., description="List of agents")

