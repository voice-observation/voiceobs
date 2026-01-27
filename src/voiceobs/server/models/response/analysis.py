"""Analysis response models."""

from pydantic import BaseModel, ConfigDict, Field


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
