"""Persona response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PersonaResponse(BaseModel):
    """Response model for a persona."""

    id: str = Field(..., description="Persona UUID")
    name: str = Field(..., description="Persona name")
    description: str | None = Field(None, description="Persona description")
    aggression: float = Field(..., description="Aggression level (0.0-1.0)")
    patience: float = Field(..., description="Patience level (0.0-1.0)")
    verbosity: float = Field(..., description="Verbosity level (0.0-1.0)")
    traits: list[str] = Field(default_factory=list, description="List of personality traits")
    tts_provider: str = Field(..., description="TTS provider (openai, elevenlabs, deepgram)")
    tts_config: dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific TTS configuration"
    )
    preview_audio_url: str | None = Field(None, description="URL to pregenerated preview audio")
    preview_audio_text: str | None = Field(
        None, description="Text used for preview audio generation"
    )
    preview_audio_status: str | None = Field(
        None, description="Preview audio generation status (null, generating, ready, failed)"
    )
    preview_audio_error: str | None = Field(
        None, description="Error message if preview audio generation failed"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    created_by: str | None = Field(None, description="User who created the persona")
    is_active: bool = Field(True, description="Whether the persona is active")
    is_default: bool = Field(False, description="Whether this is the default fallback persona")
    persona_type: str = Field("custom", description="Persona type: 'system' or 'custom'")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Angry Customer",
                "description": "An aggressive customer persona for testing conflict resolution",
                "aggression": 0.8,
                "patience": 0.2,
                "verbosity": 0.6,
                "traits": ["impatient", "demanding", "direct"],
                "tts_provider": "openai",
                "tts_config": {"model": "tts-1", "voice": "alloy", "speed": 1.0},
                "preview_audio_url": "https://storage.example.com/audio/personas/preview/abc123.mp3",
                "preview_audio_text": "Hello, this is how I sound.",
                "metadata": {"category": "customer", "difficulty": "hard"},
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T11:00:00Z",
                "created_by": "user@example.com",
                "is_active": True,
                "is_default": False,
            }
        }
    )


class PersonaListItem(BaseModel):
    """Simplified persona model for list responses (excludes sensitive fields)."""

    id: str = Field(..., description="Persona UUID")
    name: str = Field(..., description="Persona name")
    description: str | None = Field(None, description="Persona description")
    aggression: float = Field(..., description="Aggression level (0.0-1.0)")
    patience: float = Field(..., description="Patience level (0.0-1.0)")
    verbosity: float = Field(..., description="Verbosity level (0.0-1.0)")
    traits: list[str] = Field(default_factory=list, description="List of personality traits")
    preview_audio_url: str | None = Field(None, description="URL to pregenerated preview audio")
    preview_audio_text: str | None = Field(
        None, description="Text used for preview audio generation"
    )
    preview_audio_status: str | None = Field(
        None, description="Preview audio generation status (null, generating, ready, failed)"
    )
    is_active: bool = Field(True, description="Whether the persona is active")
    is_default: bool = Field(False, description="Whether this is the default fallback persona")
    persona_type: str = Field("custom", description="Persona type: 'system' or 'custom'")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Angry Customer",
                "description": "An aggressive customer persona",
                "aggression": 0.8,
                "patience": 0.2,
                "verbosity": 0.6,
                "traits": ["impatient", "demanding"],
                "preview_audio_url": "https://storage.example.com/preview1.mp3",
                "preview_audio_text": "Hello, this is how I sound.",
                "preview_audio_status": "ready",
                "is_active": True,
                "is_default": False,
            }
        }
    )


class PersonasListResponse(BaseModel):
    """Response model for listing personas."""

    count: int = Field(..., description="Number of personas in response")
    personas: list[PersonaListItem] = Field(..., description="List of personas")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "count": 2,
                "personas": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Angry Customer",
                        "description": "An aggressive customer persona",
                        "aggression": 0.8,
                        "patience": 0.2,
                        "verbosity": 0.6,
                        "traits": ["impatient", "demanding"],
                        "preview_audio_url": "https://storage.example.com/preview1.mp3",
                        "preview_audio_text": "Hello, this is how I sound.",
                        "is_active": True,
                        "is_default": True,
                    },
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "Polite Customer",
                        "description": "A patient customer persona",
                        "aggression": 0.2,
                        "patience": 0.9,
                        "verbosity": 0.5,
                        "traits": ["polite", "patient"],
                        "preview_audio_url": "https://storage.example.com/preview2.mp3",
                        "preview_audio_text": "Hello, this is how I sound.",
                        "is_active": True,
                        "is_default": False,
                    },
                ],
            }
        }
    )


class PersonaAudioPreviewResponse(BaseModel):
    """Response model for persona audio preview."""

    audio_url: str = Field(..., description="URL to pregenerated preview audio")
    text: str = Field(..., description="Text that was used for audio generation")
    format: str = Field(..., description="Audio format (e.g., 'audio/mpeg', 'audio/wav')")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "audio_url": "https://storage.example.com/audio/personas/preview/abc123.mp3",
                "text": "Hello, this is how I sound.",
                "format": "audio/mpeg",
            }
        }
    )


class PreviewAudioStatusResponse(BaseModel):
    """Response model for preview audio generation status."""

    status: str | None = Field(
        None, description="Generation status: null, generating, ready, or failed"
    )
    audio_url: str | None = Field(None, description="URL to preview audio when ready")
    error_message: str | None = Field(None, description="Error message if generation failed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "audio_url": "https://storage.example.com/audio/personas/preview/abc123.mp3",
                "error_message": None,
            }
        }
    )
