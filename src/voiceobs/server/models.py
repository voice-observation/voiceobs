"""Pydantic models for the voiceobs server API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SpanAttributes(BaseModel):
    """Attributes for a span."""

    # Allow any additional attributes
    model_config = {"extra": "allow"}


class SpanInput(BaseModel):
    """Input model for a single span."""

    name: str = Field(..., description="Span name (e.g., 'voice.turn', 'voice.asr')")
    start_time: datetime | None = Field(None, description="Span start time (ISO 8601)")
    end_time: datetime | None = Field(None, description="Span end time (ISO 8601)")
    duration_ms: float | None = Field(None, description="Span duration in milliseconds")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Span attributes"
    )
    trace_id: str | None = Field(None, description="OpenTelemetry trace ID")
    span_id: str | None = Field(None, description="OpenTelemetry span ID")
    parent_span_id: str | None = Field(None, description="Parent span ID")


class SpanBatchInput(BaseModel):
    """Input model for a batch of spans."""

    spans: list[SpanInput] = Field(..., description="List of spans to ingest")


class SpanResponse(BaseModel):
    """Response model for a single ingested span."""

    id: UUID = Field(default_factory=uuid4, description="Internal span ID")
    name: str = Field(..., description="Span name")
    status: str = Field(default="accepted", description="Ingestion status")


class IngestResponse(BaseModel):
    """Response model for span ingestion."""

    accepted: int = Field(..., description="Number of spans accepted")
    span_ids: list[UUID] = Field(..., description="IDs of ingested spans")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(default="healthy", description="Server health status")
    version: str = Field(..., description="voiceobs version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Current server time"
    )


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Additional error details")
