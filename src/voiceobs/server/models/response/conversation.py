"""Conversation response models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from voiceobs.server.models.response.analysis import AnalysisResponse


class TurnResponse(BaseModel):
    """Response model for a conversation turn.

    Represents a single turn (user or agent utterance) in a conversation.
    """

    id: str = Field(..., description="Turn ID")
    actor: str = Field(..., description="Actor (user, agent, system)")
    turn_index: int | None = Field(None, description="Turn index in conversation")
    duration_ms: float | None = Field(None, description="Turn duration")
    transcript: str | None = Field(None, description="Turn transcript if available")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Turn attributes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "turn-001",
                "actor": "user",
                "turn_index": 0,
                "duration_ms": 2500.0,
                "transcript": "Hello, I need help with my order",
                "attributes": {
                    "voice.conversation.id": "conv-123",
                    "voice.turn.id": "turn-001",
                },
            }
        }
    )


class ConversationSummary(BaseModel):
    """Summary model for a conversation."""

    id: str = Field(..., description="Conversation ID")
    turn_count: int = Field(..., description="Number of turns")
    span_count: int = Field(..., description="Number of spans")
    has_failures: bool = Field(False, description="Whether failures were detected")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "conv-123",
                "turn_count": 8,
                "span_count": 24,
                "has_failures": False,
            }
        }
    )


class ConversationDetail(BaseModel):
    """Detailed model for a conversation.

    Includes all turns and optional analysis results.
    """

    id: str = Field(..., description="Conversation ID")
    turns: list[TurnResponse] = Field(..., description="List of turns")
    span_count: int = Field(..., description="Total spans in conversation")
    analysis: AnalysisResponse | None = Field(None, description="Analysis for this conversation")


class ConversationsListResponse(BaseModel):
    """Response model for listing conversations."""

    count: int = Field(..., description="Number of conversations in this page")
    total: int = Field(..., description="Total number of conversations matching filters")
    conversations: list[ConversationSummary] = Field(..., description="List of conversations")
    limit: int = Field(default=50, description="Maximum number of results per page")
    offset: int = Field(default=0, description="Number of results skipped")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "count": 2,
                "total": 2,
                "limit": 50,
                "offset": 0,
                "conversations": [
                    {
                        "id": "conv-123",
                        "turn_count": 8,
                        "span_count": 24,
                        "has_failures": False,
                    },
                    {
                        "id": "conv-456",
                        "turn_count": 5,
                        "span_count": 15,
                        "has_failures": True,
                    },
                ],
            }
        }
    )

