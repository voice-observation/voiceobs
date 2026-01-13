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
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current server time")

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
    by_type: dict[str, int] = Field(default_factory=dict, description="Count of failures by type")

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


# Metrics response models


class MetricsSummaryResponse(BaseModel):
    """Response model for overall metrics summary."""

    total_conversations: int = Field(..., description="Total number of conversations")
    total_turns: int = Field(..., description="Total number of turns")
    total_duration_ms: float | None = Field(None, description="Total duration in milliseconds")
    avg_latency_p50_ms: float | None = Field(None, description="P50 latency across all stages")
    avg_latency_p95_ms: float | None = Field(None, description="P95 latency across all stages")
    avg_latency_p99_ms: float | None = Field(None, description="P99 latency across all stages")
    failure_rate: float | None = Field(None, description="Failure rate percentage")
    total_failures: int = Field(..., description="Total number of failures")
    silence_mean_ms: float | None = Field(None, description="Mean silence duration")
    overlap_count: int = Field(..., description="Number of overlaps detected")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_conversations": 100,
                "total_turns": 500,
                "total_duration_ms": 125000.0,
                "avg_latency_p50_ms": 150.0,
                "avg_latency_p95_ms": 300.0,
                "avg_latency_p99_ms": 450.0,
                "failure_rate": 2.5,
                "total_failures": 25,
                "silence_mean_ms": 850.0,
                "overlap_count": 10,
            }
        }
    )


class LatencyBreakdownItem(BaseModel):
    """Single item in latency breakdown."""

    group: str = Field(..., description="Group identifier (stage name, etc.)")
    count: int = Field(..., description="Number of samples")
    mean_ms: float | None = Field(None, description="Mean latency")
    p50_ms: float | None = Field(None, description="P50 latency")
    p95_ms: float | None = Field(None, description="P95 latency")
    p99_ms: float | None = Field(None, description="P99 latency")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "group": "asr",
                "count": 100,
                "mean_ms": 145.5,
                "p50_ms": 132.0,
                "p95_ms": 210.5,
                "p99_ms": 285.0,
            }
        }
    )


class LatencyBreakdownResponse(BaseModel):
    """Response model for latency breakdown by group."""

    breakdown: list[LatencyBreakdownItem] = Field(..., description="Latency breakdown items")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "breakdown": [
                    {
                        "group": "asr",
                        "count": 100,
                        "mean_ms": 145.5,
                        "p50_ms": 132.0,
                        "p95_ms": 210.5,
                        "p99_ms": 285.0,
                    },
                    {
                        "group": "llm",
                        "count": 100,
                        "mean_ms": 850.0,
                        "p50_ms": 750.0,
                        "p95_ms": 1200.0,
                        "p99_ms": 1500.0,
                    },
                ]
            }
        }
    )


class FailureBreakdownItem(BaseModel):
    """Single item in failure breakdown."""

    group: str = Field(..., description="Group identifier (failure type, etc.)")
    count: int = Field(..., description="Number of failures")
    percentage: float | None = Field(None, description="Percentage of total failures")

    model_config = ConfigDict(
        json_schema_extra={"example": {"group": "high_latency", "count": 10, "percentage": 40.0}}
    )


class FailureBreakdownResponse(BaseModel):
    """Response model for failure breakdown by group."""

    breakdown: list[FailureBreakdownItem] = Field(..., description="Failure breakdown items")
    total: int = Field(..., description="Total number of failures")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "breakdown": [
                    {"group": "high_latency", "count": 10, "percentage": 40.0},
                    {"group": "interruption", "count": 15, "percentage": 60.0},
                ],
                "total": 25,
            }
        }
    )


class ConversationVolumeItem(BaseModel):
    """Single item in conversation volume time series."""

    time_bucket: str = Field(..., description="Time bucket identifier (ISO 8601 or formatted)")
    count: int = Field(..., description="Number of conversations in this bucket")

    model_config = ConfigDict(
        json_schema_extra={"example": {"time_bucket": "2024-01-15T10:00:00Z", "count": 5}}
    )


class ConversationVolumeResponse(BaseModel):
    """Response model for conversation volume over time."""

    volume: list[ConversationVolumeItem] = Field(..., description="Conversation volume time series")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "volume": [
                    {"time_bucket": "2024-01-15T10:00:00Z", "count": 5},
                    {"time_bucket": "2024-01-15T11:00:00Z", "count": 8},
                    {"time_bucket": "2024-01-15T12:00:00Z", "count": 12},
                ]
            }
        }
    )


class TrendDataPoint(BaseModel):
    """Single data point in a trend time series."""

    timestamp: str = Field(..., description="Timestamp (ISO 8601)")
    value: float | None = Field(None, description="Metric value")
    rolling_avg: float | None = Field(None, description="Rolling average value")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2024-01-15T10:00:00Z",
                "value": 150.0,
                "rolling_avg": 145.5,
            }
        }
    )


class TrendResponse(BaseModel):
    """Response model for time-series trends."""

    metric: str = Field(..., description="Metric name")
    window: str = Field(..., description="Time window (e.g., '1h', '1d')")
    data_points: list[TrendDataPoint] = Field(..., description="Time series data points")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metric": "latency",
                "window": "1h",
                "data_points": [
                    {"timestamp": "2024-01-15T10:00:00Z", "value": 150.0, "rolling_avg": 145.5},
                    {"timestamp": "2024-01-15T11:00:00Z", "value": 160.0, "rolling_avg": 155.0},
                ],
            }
        }
    )


# Test management response models


class TestSuiteResponse(BaseModel):
    """Response model for a test suite."""

    id: str = Field(..., description="Test suite UUID")
    name: str = Field(..., description="Test suite name")
    description: str | None = Field(None, description="Test suite description")
    status: str = Field(..., description="Test suite status (pending, running, completed)")
    created_at: datetime | None = Field(None, description="Creation timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Regression Suite",
                "description": "Daily regression tests",
                "status": "pending",
                "created_at": "2024-01-15T10:00:00Z",
            }
        }
    )


class TestSuiteCreateRequest(BaseModel):
    """Request model for creating a test suite."""

    name: str = Field(..., min_length=1, description="Test suite name")
    description: str | None = Field(None, description="Test suite description")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Regression Suite",
                "description": "Daily regression tests",
            }
        }
    )


class TestSuiteUpdateRequest(BaseModel):
    """Request model for updating a test suite."""

    name: str | None = Field(None, min_length=1, description="Test suite name")
    description: str | None = Field(None, description="Test suite description")
    status: str | None = Field(None, description="Test suite status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Suite Name",
                "description": "Updated description",
                "status": "running",
            }
        }
    )


class TestSuitesListResponse(BaseModel):
    """Response model for listing test suites."""

    count: int = Field(..., description="Number of test suites")
    suites: list[TestSuiteResponse] = Field(..., description="List of test suites")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "count": 2,
                "suites": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Regression Suite",
                        "description": "Daily regression tests",
                        "status": "pending",
                        "created_at": "2024-01-15T10:00:00Z",
                    },
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "Smoke Tests",
                        "description": "Quick smoke tests",
                        "status": "completed",
                        "created_at": "2024-01-15T09:00:00Z",
                    },
                ],
            }
        }
    )


class TestScenarioResponse(BaseModel):
    """Response model for a test scenario."""

    id: str = Field(..., description="Test scenario UUID")
    suite_id: str = Field(..., description="Parent test suite UUID")
    name: str = Field(..., description="Test scenario name")
    goal: str = Field(..., description="Test scenario goal")
    persona_id: str = Field(..., description="Persona UUID reference")
    max_turns: int | None = Field(None, description="Maximum number of turns")
    timeout: int | None = Field(None, description="Timeout in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "suite_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Order Status Check",
                "goal": "User checks order status",
                "persona_id": "550e8400-e29b-41d4-a716-446655440002",
                "max_turns": 10,
                "timeout": 300,
            }
        }
    )


class TestScenarioCreateRequest(BaseModel):
    """Request model for creating a test scenario."""

    suite_id: str = Field(..., description="Parent test suite UUID")
    name: str = Field(..., min_length=1, description="Test scenario name")
    goal: str = Field(..., min_length=1, description="Test scenario goal")
    persona_id: str = Field(..., description="Required reference to persona UUID")
    max_turns: int | None = Field(None, ge=1, description="Maximum number of turns")
    timeout: int | None = Field(None, ge=1, description="Timeout in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "suite_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Order Status Check",
                "goal": "User checks order status",
                "persona_id": "550e8400-e29b-41d4-a716-446655440002",
                "max_turns": 10,
                "timeout": 300,
            }
        }
    )


class TestScenarioUpdateRequest(BaseModel):
    """Request model for updating a test scenario."""

    name: str | None = Field(None, min_length=1, description="Test scenario name")
    goal: str | None = Field(None, min_length=1, description="Test scenario goal")
    persona_id: str | None = Field(None, description="Persona UUID reference")
    max_turns: int | None = Field(None, ge=1, description="Maximum number of turns")
    timeout: int | None = Field(None, ge=1, description="Timeout in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Scenario Name",
                "goal": "Updated goal",
                "persona_id": "550e8400-e29b-41d4-a716-446655440003",
                "max_turns": 15,
                "timeout": 600,
            }
        }
    )


class TestScenariosListResponse(BaseModel):
    """Response model for listing test scenarios."""

    count: int = Field(..., description="Number of test scenarios")
    scenarios: list[TestScenarioResponse] = Field(..., description="List of test scenarios")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "count": 2,
                "scenarios": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "suite_id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "Order Status Check",
                        "goal": "User checks order status",
                        "persona_id": "550e8400-e29b-41d4-a716-446655440002",
                        "max_turns": 10,
                        "timeout": 300,
                    },
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440003",
                        "suite_id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "Payment Processing",
                        "goal": "User processes payment",
                        "persona_id": "550e8400-e29b-41d4-a716-446655440004",
                        "max_turns": 15,
                        "timeout": 600,
                    },
                ],
            }
        }
    )


class TestRunRequest(BaseModel):
    """Request model for running tests."""

    suite_id: str | None = Field(None, description="Test suite ID to run")
    scenarios: list[str] | None = Field(None, description="Specific scenario IDs to run")
    max_workers: int = Field(10, ge=1, le=100, description="Maximum number of parallel workers")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "suite_id": "550e8400-e29b-41d4-a716-446655440001",
                "scenarios": ["550e8400-e29b-41d4-a716-446655440000"],
                "max_workers": 10,
            }
        }
    )


class TestRunResponse(BaseModel):
    """Response model for test run initiation."""

    execution_id: str = Field(..., description="Test execution UUID")
    status: str = Field(..., description="Execution status (queued, running, completed, failed)")
    scenarios_count: int = Field(..., description="Number of scenarios in execution")
    estimated_duration: int | None = Field(None, description="Estimated duration in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "execution_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "queued",
                "scenarios_count": 2,
                "estimated_duration": 300,
            }
        }
    )


class TestExecutionResponse(BaseModel):
    """Response model for a test execution."""

    id: str = Field(..., description="Test execution UUID")
    scenario_id: str = Field(..., description="Test scenario UUID")
    conversation_id: str | None = Field(None, description="Associated conversation UUID")
    status: str = Field(..., description="Execution status")
    started_at: datetime | None = Field(None, description="Start timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    result_json: dict[str, Any] = Field(default_factory=dict, description="Execution results")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_id": "550e8400-e29b-41d4-a716-446655440001",
                "conversation_id": "550e8400-e29b-41d4-a716-446655440002",
                "status": "completed",
                "started_at": "2024-01-15T10:00:00Z",
                "completed_at": "2024-01-15T10:05:00Z",
                "result_json": {"passed": True, "score": 0.95},
            }
        }
    )


class TestSummaryResponse(BaseModel):
    """Response model for test summary statistics."""

    total: int = Field(..., description="Total number of test executions")
    passed: int = Field(..., description="Number of passed tests")
    failed: int = Field(..., description="Number of failed tests")
    pass_rate: float | None = Field(None, description="Pass rate (0.0 to 1.0)")
    avg_duration_ms: float | None = Field(None, description="Average duration in milliseconds")
    avg_latency_ms: float | None = Field(None, description="Average latency in milliseconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 50,
                "passed": 40,
                "failed": 10,
                "pass_rate": 0.8,
                "avg_duration_ms": 45000,
                "avg_latency_ms": 850,
            }
        }
    )


# Persona management models


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
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    created_by: str | None = Field(None, description="User who created the persona")
    is_active: bool = Field(True, description="Whether the persona is active")

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
            }
        }
    )


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
    is_active: bool = Field(True, description="Whether the persona is active")

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
                "is_active": True,
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
