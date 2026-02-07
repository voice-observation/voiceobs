"""Generation status response model."""

from pydantic import BaseModel, ConfigDict, Field


class GenerationStatusResponse(BaseModel):
    """Response model for generation status.

    This model provides information about the scenario generation status
    for a test suite, including the current status, number of generated
    scenarios, and any error message if generation failed.
    """

    suite_id: str = Field(..., description="Test suite UUID")
    status: str = Field(
        ...,
        description="Generation status (pending, generating, ready, generation_failed)",
    )
    scenario_count: int = Field(..., description="Number of scenarios generated")
    error: str | None = Field(None, description="Error message if generation failed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "suite_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "ready",
                "scenario_count": 5,
                "error": None,
            }
        }
    )
