"""Failure response models."""

from pydantic import BaseModel, ConfigDict, Field


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

