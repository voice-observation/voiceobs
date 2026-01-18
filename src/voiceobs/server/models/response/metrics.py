"""Metrics response models."""

from pydantic import BaseModel, ConfigDict, Field


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

