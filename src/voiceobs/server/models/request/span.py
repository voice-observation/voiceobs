"""Span request models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SpanInput(BaseModel):
    """Input model for a single span.

    Represents a single observability span from a voice AI pipeline.
    Spans track timing and metadata for individual operations like
    speech recognition (ASR), language model inference (LLM), or
    text-to-speech (TTS).
    """

    name: str = Field(..., description="Span name (e.g., 'voice.turn', 'voice.asr')")
    start_time: datetime | None = Field(None, description="Span start time (ISO 8601)")
    end_time: datetime | None = Field(None, description="Span end time (ISO 8601)")
    duration_ms: float | None = Field(
        None, ge=0, description="Span duration in milliseconds (must be non-negative)"
    )
    attributes: dict[str, Any] = Field(default_factory=dict, description="Span attributes")
    trace_id: str | None = Field(None, description="OpenTelemetry trace ID")
    span_id: str | None = Field(None, description="OpenTelemetry span ID")
    parent_span_id: str | None = Field(None, description="Parent span ID")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "voice.turn",
                    "start_time": "2024-01-15T10:30:00Z",
                    "end_time": "2024-01-15T10:30:02.500Z",
                    "duration_ms": 2500.0,
                    "attributes": {
                        "voice.conversation.id": "conv-123",
                        "voice.turn.id": "turn-001",
                        "voice.turn.index": 0,
                        "voice.actor": "user",
                        "voice.transcript": "Hello, how can I help you?",
                    },
                    "trace_id": "abc123def456",
                    "span_id": "span-001",
                },
                {
                    "name": "voice.asr",
                    "duration_ms": 150.5,
                    "attributes": {
                        "voice.conversation.id": "conv-123",
                        "voice.stage.type": "asr",
                    },
                },
            ]
        }
    )


class SpanBatchInput(BaseModel):
    """Input model for a batch of spans.

    Use this model to ingest multiple spans in a single request
    for better efficiency.
    """

    spans: list[SpanInput] = Field(
        ..., min_length=1, description="List of spans to ingest (at least 1 required)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "spans": [
                    {
                        "name": "voice.turn",
                        "duration_ms": 2500.0,
                        "attributes": {
                            "voice.conversation.id": "conv-123",
                            "voice.turn.id": "turn-001",
                            "voice.actor": "user",
                        },
                    },
                    {
                        "name": "voice.asr",
                        "duration_ms": 150.5,
                        "attributes": {
                            "voice.conversation.id": "conv-123",
                            "voice.stage.type": "asr",
                        },
                    },
                ]
            }
        }
    )

