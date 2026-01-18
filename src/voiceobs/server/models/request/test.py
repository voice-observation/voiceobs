"""Test request models."""

from pydantic import BaseModel, ConfigDict, Field


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

