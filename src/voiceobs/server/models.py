"""Pydantic models for the voiceobs server API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class SpanAttributes(BaseModel):
    """Attributes for a span."""

    # Allow any additional attributes
    model_config = ConfigDict(extra="allow")


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
    duration_ms: float | None = Field(None, description="Span duration in milliseconds")
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

    spans: list[SpanInput] = Field(..., description="List of spans to ingest")

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


class HealthResponse(BaseModel):
    """Response model for health check.

    Indicates the server is running and healthy.
    """

    status: str = Field(default="healthy", description="Server health status")
    version: str = Field(..., description="voiceobs version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Current server time"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "0.0.2",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }
    )


class ErrorResponse(BaseModel):
    """Response model for errors.

    Returned when an API request fails.
    """

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Additional error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "not_found",
                "message": "Resource not found",
                "detail": "Span with ID 550e8400-e29b-41d4-a716-446655440000 not found",
            }
        }
    )


# Analysis response models


class StageMetricsResponse(BaseModel):
    """Response model for stage metrics (ASR/LLM/TTS).

    Contains latency percentiles for a specific voice pipeline stage.
    """

    stage_type: str = Field(..., description="Stage type (asr, llm, tts)")
    count: int = Field(..., description="Number of spans for this stage")
    mean_ms: float | None = Field(None, description="Mean duration in milliseconds")
    p50_ms: float | None = Field(None, description="Median (p50) duration")
    p95_ms: float | None = Field(None, description="95th percentile duration")
    p99_ms: float | None = Field(None, description="99th percentile duration")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "stage_type": "asr",
                "count": 15,
                "mean_ms": 145.5,
                "p50_ms": 132.0,
                "p95_ms": 210.5,
                "p99_ms": 285.0,
            }
        }
    )


class TurnMetricsResponse(BaseModel):
    """Response model for turn metrics.

    Tracks conversation flow metrics including silence timing and interruptions.
    """

    silence_samples: int = Field(..., description="Number of silence measurements")
    silence_mean_ms: float | None = Field(None, description="Mean silence after user turn")
    silence_p95_ms: float | None = Field(None, description="95th percentile silence")
    total_agent_turns: int = Field(..., description="Total number of agent turns")
    interruptions: int = Field(..., description="Number of detected interruptions")
    interruption_rate: float | None = Field(None, description="Interruption rate percentage")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "silence_samples": 10,
                "silence_mean_ms": 850.0,
                "silence_p95_ms": 1200.0,
                "total_agent_turns": 8,
                "interruptions": 1,
                "interruption_rate": 12.5,
            }
        }
    )


class EvalMetricsResponse(BaseModel):
    """Response model for semantic evaluation metrics.

    Contains intent accuracy and relevance scoring metrics.
    """

    total_evals: int = Field(..., description="Number of evaluated turns")
    intent_correct_count: int = Field(..., description="Turns with correct intent")
    intent_incorrect_count: int = Field(..., description="Turns with incorrect intent")
    intent_correct_rate: float | None = Field(None, description="Intent correctness percentage")
    intent_failure_rate: float | None = Field(None, description="Intent failure percentage")
    avg_relevance_score: float | None = Field(None, description="Average relevance score")
    min_relevance_score: float | None = Field(None, description="Minimum relevance score")
    max_relevance_score: float | None = Field(None, description="Maximum relevance score")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_evals": 10,
                "intent_correct_count": 9,
                "intent_incorrect_count": 1,
                "intent_correct_rate": 90.0,
                "intent_failure_rate": 10.0,
                "avg_relevance_score": 0.85,
                "min_relevance_score": 0.65,
                "max_relevance_score": 0.98,
            }
        }
    )


class AnalysisSummary(BaseModel):
    """Summary section of analysis response."""

    total_spans: int = Field(..., description="Total number of spans")
    total_conversations: int = Field(..., description="Number of unique conversations")
    total_turns: int = Field(..., description="Number of voice turns")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_spans": 50,
                "total_conversations": 3,
                "total_turns": 20,
            }
        }
    )


class StagesResponse(BaseModel):
    """Response model for all stage metrics."""

    asr: StageMetricsResponse = Field(..., description="ASR stage metrics")
    llm: StageMetricsResponse = Field(..., description="LLM stage metrics")
    tts: StageMetricsResponse = Field(..., description="TTS stage metrics")


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""

    summary: AnalysisSummary = Field(..., description="Analysis summary")
    stages: StagesResponse = Field(..., description="Stage latency metrics")
    turns: TurnMetricsResponse = Field(..., description="Turn timing metrics")
    eval: EvalMetricsResponse = Field(..., description="Semantic evaluation metrics")


# Conversation response models


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
    analysis: AnalysisResponse | None = Field(
        None, description="Analysis for this conversation"
    )


class ConversationsListResponse(BaseModel):
    """Response model for listing conversations."""

    count: int = Field(..., description="Number of conversations")
    conversations: list[ConversationSummary] = Field(
        ..., description="List of conversations"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "count": 2,
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


# Failure response models


class FailureResponse(BaseModel):
    """Response model for a detected failure.

    Represents a quality issue detected in the voice conversation.
    """

    id: str = Field(..., description="Failure ID")
    type: str = Field(..., description="Failure type")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    message: str = Field(..., description="Failure description")
    conversation_id: str | None = Field(None, description="Associated conversation ID")
    turn_id: str | None = Field(None, description="Associated turn ID")
    turn_index: int | None = Field(None, description="Turn index")
    signal_name: str | None = Field(None, description="Signal that triggered failure")
    signal_value: float | None = Field(None, description="Signal value")
    threshold: float | None = Field(None, description="Threshold that was exceeded")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "0",
                "type": "high_latency",
                "severity": "high",
                "message": "High latency detected in LLM stage",
                "conversation_id": "conv-123",
                "turn_id": "turn-003",
                "turn_index": 2,
                "signal_name": "llm_latency_ms",
                "signal_value": 3500.0,
                "threshold": 2000.0,
            }
        }
    )


class FailuresListResponse(BaseModel):
    """Response model for listing failures.

    Includes failure counts grouped by severity and type.
    """

    count: int = Field(..., description="Number of failures")
    failures: list[FailureResponse] = Field(..., description="List of failures")
    by_severity: dict[str, int] = Field(
        default_factory=dict, description="Count of failures by severity"
    )
    by_type: dict[str, int] = Field(
        default_factory=dict, description="Count of failures by type"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "count": 2,
                "failures": [
                    {
                        "id": "0",
                        "type": "high_latency",
                        "severity": "high",
                        "message": "High latency detected in LLM stage",
                        "conversation_id": "conv-123",
                        "turn_id": "turn-003",
                        "turn_index": 2,
                        "signal_name": "llm_latency_ms",
                        "signal_value": 3500.0,
                        "threshold": 2000.0,
                    },
                    {
                        "id": "1",
                        "type": "interruption",
                        "severity": "medium",
                        "message": "User interrupted agent response",
                        "conversation_id": "conv-123",
                        "turn_id": "turn-005",
                        "turn_index": 4,
                        "signal_name": None,
                        "signal_value": None,
                        "threshold": None,
                    },
                ],
                "by_severity": {"high": 1, "medium": 1},
                "by_type": {"high_latency": 1, "interruption": 1},
            }
        }
    )


# Span list and detail response models


class SpanListItem(BaseModel):
    """Summary of a span in the list response."""

    id: str = Field(..., description="Span UUID")
    name: str = Field(..., description="Span name")
    duration_ms: float | None = Field(None, description="Duration in milliseconds")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Span attributes"
    )

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
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Span attributes"
    )
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
