"""Test response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TestSuiteResponse(BaseModel):
    """Response model for a test suite."""

    id: str = Field(..., description="Test suite UUID")
    name: str = Field(..., description="Test suite name")
    description: str | None = Field(None, description="Test suite description")
    status: str = Field(
        ...,
        description=(
            "Test suite status (pending, generating, ready, generation_failed, running, completed)"
        ),
    )
    agent_id: str | None = Field(None, description="Agent UUID")
    test_scopes: list[str] = Field(
        default_factory=lambda: ["core_flows", "common_mistakes"],
        description="Test scopes",
    )
    thoroughness: int = Field(
        1, description="Test thoroughness (0: Light, 1: Standard, 2: Exhaustive)"
    )
    edge_cases: list[str] = Field(default_factory=list, description="Edge cases to include")
    evaluation_strictness: str = Field("balanced", description="Evaluation strictness")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    generation_error: str | None = Field(None, description="Error message if generation failed")
    scenario_count: int | None = Field(None, description="Number of scenarios in this suite")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Regression Suite",
                "description": "Daily regression tests",
                "status": "pending",
                "agent_id": "550e8400-e29b-41d4-a716-446655440001",
                "test_scopes": ["core_flows", "common_mistakes"],
                "thoroughness": 1,
                "edge_cases": ["hesitations", "interrupts"],
                "evaluation_strictness": "balanced",
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
    intent: str | None = Field(None, description="LLM-identified intent for this scenario")
    persona_traits: list[str] | None = Field(
        None, description="Desired persona traits for this scenario"
    )
    persona_match_score: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="How well the assigned persona matches desired traits (0-1)",
    )
    caller_behaviors: list[str] | None = Field(None, description="Test steps for caller behavior")
    tags: list[str] | None = Field(None, description="Tags for categorization")
    status: str = Field("draft", description="Status: ready or draft")
    is_manual: bool = Field(
        False, description="True for manually created scenarios, False for AI-generated"
    )

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
                "intent": "check_order_status",
                "persona_traits": ["impatient", "direct"],
                "persona_match_score": 0.85,
                "caller_behaviors": ["Ask for order status", "Provide order number"],
                "success_criteria": "Agent provides order status",
                "must_mention": ["order number", "delivery date"],
                "tags": ["happy-path", "order"],
                "status": "ready",
            }
        }
    )


class TestScenariosListResponse(BaseModel):
    """Response model for listing test scenarios."""

    count: int = Field(..., description="Total number of test scenarios matching filters")
    scenarios: list[TestScenarioResponse] = Field(..., description="List of test scenarios")
    limit: int = Field(..., description="Maximum number of results per page")
    offset: int = Field(..., description="Number of results skipped")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "count": 50,
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
                "limit": 20,
                "offset": 0,
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
