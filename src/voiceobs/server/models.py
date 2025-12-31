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
    attributes: dict[str, Any] = Field(default_factory=dict, description="Span attributes")
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
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current server time")


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Additional error details")


# Analysis response models


class StageMetricsResponse(BaseModel):
    """Response model for stage metrics (ASR/LLM/TTS)."""

    stage_type: str = Field(..., description="Stage type (asr, llm, tts)")
    count: int = Field(..., description="Number of spans for this stage")
    mean_ms: float | None = Field(None, description="Mean duration in milliseconds")
    p50_ms: float | None = Field(None, description="Median (p50) duration")
    p95_ms: float | None = Field(None, description="95th percentile duration")
    p99_ms: float | None = Field(None, description="99th percentile duration")


class TurnMetricsResponse(BaseModel):
    """Response model for turn metrics."""

    silence_samples: int = Field(..., description="Number of silence measurements")
    silence_mean_ms: float | None = Field(None, description="Mean silence after user turn")
    silence_p95_ms: float | None = Field(None, description="95th percentile silence")
    total_agent_turns: int = Field(..., description="Total number of agent turns")
    interruptions: int = Field(..., description="Number of detected interruptions")
    interruption_rate: float | None = Field(None, description="Interruption rate percentage")


class EvalMetricsResponse(BaseModel):
    """Response model for semantic evaluation metrics."""

    total_evals: int = Field(..., description="Number of evaluated turns")
    intent_correct_count: int = Field(..., description="Turns with correct intent")
    intent_incorrect_count: int = Field(..., description="Turns with incorrect intent")
    intent_correct_rate: float | None = Field(None, description="Intent correctness percentage")
    intent_failure_rate: float | None = Field(None, description="Intent failure percentage")
    avg_relevance_score: float | None = Field(None, description="Average relevance score")
    min_relevance_score: float | None = Field(None, description="Minimum relevance score")
    max_relevance_score: float | None = Field(None, description="Maximum relevance score")


class AnalysisSummary(BaseModel):
    """Summary section of analysis response."""

    total_spans: int = Field(..., description="Total number of spans")
    total_conversations: int = Field(..., description="Number of unique conversations")
    total_turns: int = Field(..., description="Number of voice turns")


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
    """Response model for a conversation turn."""

    id: str = Field(..., description="Turn ID")
    actor: str = Field(..., description="Actor (user, agent, system)")
    turn_index: int | None = Field(None, description="Turn index in conversation")
    duration_ms: float | None = Field(None, description="Turn duration")
    transcript: str | None = Field(None, description="Turn transcript if available")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Turn attributes")


class ConversationSummary(BaseModel):
    """Summary model for a conversation."""

    id: str = Field(..., description="Conversation ID")
    turn_count: int = Field(..., description="Number of turns")
    span_count: int = Field(..., description="Number of spans")
    has_failures: bool = Field(False, description="Whether failures were detected")


class ConversationDetail(BaseModel):
    """Detailed model for a conversation."""

    id: str = Field(..., description="Conversation ID")
    turns: list[TurnResponse] = Field(..., description="List of turns")
    span_count: int = Field(..., description="Total spans in conversation")
    analysis: AnalysisResponse | None = Field(None, description="Analysis for this conversation")


class ConversationsListResponse(BaseModel):
    """Response model for listing conversations."""

    count: int = Field(..., description="Number of conversations")
    conversations: list[ConversationSummary] = Field(..., description="List of conversations")


# Failure response models


class FailureResponse(BaseModel):
    """Response model for a detected failure."""

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


class FailuresListResponse(BaseModel):
    """Response model for listing failures."""

    count: int = Field(..., description="Number of failures")
    failures: list[FailureResponse] = Field(..., description="List of failures")
    by_severity: dict[str, int] = Field(
        default_factory=dict, description="Count of failures by severity"
    )
    by_type: dict[str, int] = Field(default_factory=dict, description="Count of failures by type")
