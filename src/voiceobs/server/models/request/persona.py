"""Persona request models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PersonaCreateRequest(BaseModel):
    """Request model for creating a persona."""

    name: str = Field(..., min_length=1, max_length=255, description="Persona name")
    description: str | None = Field(None, description="Persona description")
    aggression: float | None = Field(
        None, ge=0.0, le=1.0, description="Aggression level (0.0-1.0, optional)"
    )
    patience: float | None = Field(
        None, ge=0.0, le=1.0, description="Patience level (0.0-1.0, optional)"
    )
    verbosity: float | None = Field(
        None, ge=0.0, le=1.0, description="Verbosity level (0.0-1.0, optional)"
    )
    traits: list[str] = Field(default_factory=list, description="List of personality traits")
    tts_provider: str | None = Field(
        None, description="TTS provider: 'openai', 'elevenlabs', 'deepgram', etc. (optional)"
    )
    tts_config: dict[str, Any] | None = Field(
        None, description="Provider-specific TTS configuration (optional)"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_by: str | None = Field(None, description="User creating the persona")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Polite Customer",
                "description": "A patient and polite customer persona",
                "aggression": 0.2,
                "patience": 0.9,
                "verbosity": 0.5,
                "traits": ["polite", "patient", "helpful"],
                "tts_provider": "openai",
                "tts_config": {"model": "tts-1", "voice": "nova", "speed": 1.0},
                "metadata": {"category": "customer", "difficulty": "easy"},
                "created_by": "user@example.com",
            }
        }
    )


class PersonaUpdateRequest(BaseModel):
    """Request model for updating a persona."""

    name: str | None = Field(None, min_length=1, max_length=255, description="Persona name")
    description: str | None = Field(None, description="Persona description")
    aggression: float | None = Field(None, ge=0.0, le=1.0, description="Aggression level (0.0-1.0)")
    patience: float | None = Field(None, ge=0.0, le=1.0, description="Patience level (0.0-1.0)")
    verbosity: float | None = Field(None, ge=0.0, le=1.0, description="Verbosity level (0.0-1.0)")
    traits: list[str] | None = Field(None, description="List of personality traits")
    tts_provider: str | None = Field(None, description="TTS provider identifier")
    tts_config: dict[str, Any] | None = Field(
        None, description="Provider-specific TTS configuration"
    )
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Persona Name",
                "description": "Updated description",
                "aggression": 0.5,
                "patience": 0.7,
                "verbosity": 0.6,
                "traits": ["updated_trait"],
                "tts_provider": "elevenlabs",
                "tts_config": {
                    "voice_id": "pNInz6obpgDQGcFmaJgB",
                    "model_id": "eleven_monolingual_v1",
                },
                "metadata": {"updated": True},
            }
        }
    )
