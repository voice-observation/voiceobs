"""Agent request models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentCreateRequest(BaseModel):
    """Request model for creating an agent.

    Supports flexible contact_info structure based on agent_type.
    For convenience, phone_number and web_url can be provided directly,
    which will be converted to contact_info internally.
    """

    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    agent_type: str = Field(default="phone", description="Agent type: 'phone', 'web', etc.")
    # Convenience fields - will be converted to contact_info
    phone_number: str | None = Field(
        None, description="Agent phone number (E.164 format, for phone agents)"
    )
    web_url: str | None = Field(None, description="Agent web URL (for web agents)")
    # Direct contact_info - alternative to convenience fields
    contact_info: dict[str, Any] | None = Field(
        None, description="Contact information (alternative to phone_number/web_url)"
    )
    goal: str = Field(..., min_length=1, description="What the agent is supposed to achieve")
    supported_intents: list[str] = Field(
        ..., min_length=1, description="List of supported agent intents"
    )
    context: str | None = Field(
        None, description="Domain-specific context about what the agent does"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_by: str | None = Field(None, description="User creating the agent")

    @model_validator(mode="after")
    def validate_and_build_contact_info(self) -> AgentCreateRequest:
        """Validate contact method and build contact_info from convenience fields."""
        # Build contact_info from convenience fields if provided
        if self.contact_info is None:
            self.contact_info = {}

        # Add convenience fields to contact_info if provided
        if self.phone_number:
            self.contact_info["phone_number"] = self.phone_number
        if self.web_url:
            self.contact_info["web_url"] = self.web_url

        # Validate required fields based on agent_type
        if self.agent_type == "phone":
            if "phone_number" not in self.contact_info or not self.contact_info["phone_number"]:
                raise ValueError("phone_number is required for phone agents")
        elif self.agent_type == "web":
            if "web_url" not in self.contact_info or not self.contact_info["web_url"]:
                raise ValueError("web_url is required for web agents")
        # Future agent types can be validated here

        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Customer Support Agent",
                    "phone_number": "+1234567890",
                    "agent_type": "phone",
                    "goal": "Help customers with product inquiries and support requests",
                    "supported_intents": ["product_inquiry", "support_request", "billing_question"],
                    "metadata": {"department": "support", "priority": "high"},
                    "created_by": "user@example.com",
                },
                {
                    "name": "Web Chat Agent",
                    "web_url": "https://api.example.com/agent",
                    "agent_type": "web",
                    "goal": "Handle customer inquiries via web interface",
                    "supported_intents": ["product_inquiry", "support_request"],
                    "metadata": {"department": "support"},
                    "created_by": "user@example.com",
                },
                {
                    "name": "Custom Agent",
                    "agent_type": "custom",
                    "contact_info": {
                        "custom_endpoint": "https://custom.example.com",
                        "api_key": "secret",
                    },
                    "goal": "Custom agent with flexible contact info",
                    "supported_intents": ["custom_intent"],
                    "created_by": "user@example.com",
                },
            ]
        }
    )


class AgentUpdateRequest(BaseModel):
    """Request model for updating an agent."""

    name: str | None = Field(None, min_length=1, max_length=255, description="Agent name")
    agent_type: str | None = Field(None, description="Agent type: 'phone', 'web', etc.")
    # Convenience fields
    phone_number: str | None = Field(None, description="Agent phone number (for phone agents)")
    web_url: str | None = Field(None, description="Agent web URL (for web agents)")
    # Direct contact_info update
    contact_info: dict[str, Any] | None = Field(
        None, description="Contact information (will merge with existing)"
    )
    goal: str | None = Field(None, min_length=1, description="Agent goal")
    supported_intents: list[str] | None = Field(None, description="Supported intents")
    context: str | None = Field(None, description="Domain-specific agent context")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")
    is_active: bool | None = Field(None, description="Whether agent is active")

    @model_validator(mode="after")
    def validate_contact_method(self) -> AgentUpdateRequest:
        """Validate contact method if agent_type is specified."""
        if self.agent_type:
            # Build contact_info from convenience fields if provided
            contact_info = self.contact_info or {}
            if self.phone_number:
                contact_info["phone_number"] = self.phone_number
            if self.web_url:
                contact_info["web_url"] = self.web_url

            # Validate required fields
            if self.agent_type == "phone" and "phone_number" not in contact_info:
                raise ValueError("phone_number is required for phone agents")
            if self.agent_type == "web" and "web_url" not in contact_info:
                raise ValueError("web_url is required for web agents")
        return self


class AgentVerificationRequest(BaseModel):
    """Request model for manually triggering agent verification."""

    force: bool = Field(False, description="Force re-verification even if already verified")
