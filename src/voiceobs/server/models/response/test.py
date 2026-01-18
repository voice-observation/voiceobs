"""Test response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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

