"""Span response models."""

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class SpanResponse(BaseModel):
    """Response model for a single ingested span."""

    id: UUID = Field(default_factory=uuid4, description="Internal span ID")
    name: str = Field(..., description="Span name")
    status: str = Field(default="accepted", description="Ingestion status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "voice.turn",
                "status": "accepted",
            }
        }
    )


class IngestResponse(BaseModel):
    """Response model for span ingestion.

    Returned after successfully ingesting one or more spans.
    """

    accepted: int = Field(..., description="Number of spans accepted")
    span_ids: list[UUID] = Field(..., description="IDs of ingested spans")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "accepted": 2,
                "span_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "550e8400-e29b-41d4-a716-446655440001",
                ],
            }
        }
    )


class SpanListItem(BaseModel):
    """Summary of a span in the list response."""

    id: str = Field(..., description="Span UUID")
    name: str = Field(..., description="Span name")
    duration_ms: float | None = Field(None, description="Duration in milliseconds")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Span attributes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "voice.turn",
                "duration_ms": 2500.0,
                "attributes": {
                    "voice.conversation.id": "conv-123",
                    "voice.actor": "user",
                },
            }
        }
    )


class SpansListResponse(BaseModel):
    """Response model for listing all spans."""

    count: int = Field(..., description="Total number of spans")
    spans: list[SpanListItem] = Field(..., description="List of spans")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "count": 2,
                "spans": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "voice.turn",
                        "duration_ms": 2500.0,
                        "attributes": {"voice.actor": "user"},
                    },
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "voice.asr",
                        "duration_ms": 150.0,
                        "attributes": {"voice.stage.type": "asr"},
                    },
                ],
            }
        }
    )


class SpanDetailResponse(BaseModel):
    """Response model for a single span with full details."""

    id: str = Field(..., description="Span UUID")
    name: str = Field(..., description="Span name")
    start_time: str | None = Field(None, description="Start time (ISO 8601)")
    end_time: str | None = Field(None, description="End time (ISO 8601)")
    duration_ms: float | None = Field(None, description="Duration in milliseconds")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Span attributes")
    trace_id: str | None = Field(None, description="OpenTelemetry trace ID")
    span_id: str | None = Field(None, description="OpenTelemetry span ID")
    parent_span_id: str | None = Field(None, description="Parent span ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "voice.turn",
                "start_time": "2024-01-15T10:30:00Z",
                "end_time": "2024-01-15T10:30:02.500Z",
                "duration_ms": 2500.0,
                "attributes": {
                    "voice.conversation.id": "conv-123",
                    "voice.turn.id": "turn-001",
                    "voice.actor": "user",
                    "voice.transcript": "Hello, I need help",
                },
                "trace_id": "abc123def456",
                "span_id": "span-001",
                "parent_span_id": None,
            }
        }
    )


class ClearSpansResponse(BaseModel):
    """Response model for clearing all spans."""

    cleared: int = Field(..., description="Number of spans cleared")

    model_config = ConfigDict(json_schema_extra={"example": {"cleared": 15}})

