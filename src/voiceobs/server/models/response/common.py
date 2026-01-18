"""Common response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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

