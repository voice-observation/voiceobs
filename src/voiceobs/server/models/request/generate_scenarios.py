"""Generate scenarios request model."""

from pydantic import BaseModel, ConfigDict, Field


class GenerateScenariosRequest(BaseModel):
    """Request model for generating additional scenarios.

    This model is used when triggering the generation of additional
    test scenarios for an existing test suite.
    """

    prompt: str | None = Field(
        None,
        description="Optional free-form prompt for additional scenario requirements",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt": "Generate scenarios focusing on edge cases with impatient customers",
            }
        }
    )
