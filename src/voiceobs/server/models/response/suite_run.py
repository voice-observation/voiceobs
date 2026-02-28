"""Response models for suite run endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from voiceobs.server.db.models import TestExecutionRow, TestSuiteRunRow
from voiceobs.server.utils.json_utils import parse_jsonb_dict, parse_jsonb_list


class ScenarioRunSummaryResponse(BaseModel):
    """Summary of a single scenario run (execution) for run history."""

    id: str = Field(..., description="Execution UUID")
    created_at: datetime | None = Field(None, description="When the run was created")
    passed: bool = Field(..., description="Whether the scenario passed evaluation")
    duration_seconds: float | None = Field(None, description="Call duration in seconds")
    turns_count: int | None = Field(None, description="Number of conversation turns")

    @classmethod
    def from_execution_row(cls, execution: TestExecutionRow) -> ScenarioRunSummaryResponse:
        """Create from TestExecutionRow."""
        eval_result = execution.evaluation_result or {}
        passed = execution.status == "completed" and bool(eval_result.get("passed", False))
        turns = None
        if execution.transcript:
            turns = len(execution.transcript)
        return cls(
            id=str(execution.id),
            created_at=execution.created_at,
            passed=passed,
            duration_seconds=float(execution.duration_seconds)
            if execution.duration_seconds is not None
            else None,
            turns_count=turns,
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2024-01-15T10:00:00Z",
                "passed": True,
                "duration_seconds": 30.5,
                "turns_count": 6,
            }
        }
    )


class ScenarioRunsListResponse(BaseModel):
    """List of scenario runs for run history."""

    runs: list[ScenarioRunSummaryResponse] = Field(
        default_factory=list, description="List of scenario runs"
    )


class SuiteRunTriggerResponse(BaseModel):
    """Response returned from POST /run (trigger)."""

    suite_run_id: str = Field(..., description="Test suite run UUID")
    status: str = Field(..., description="Status (pending, running)")
    total_scenarios: int = Field(..., description="Total number of scenarios in run")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "suite_run_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "running",
                "total_scenarios": 5,
            }
        }
    )


class ExecutionSummaryResponse(BaseModel):
    """Summary of a single execution within a suite run."""

    id: str = Field(..., description="Execution UUID")
    scenario_id: str = Field(..., description="Scenario UUID")
    scenario_name: str = Field(..., description="Scenario display name")
    status: str = Field(..., description="Execution status")
    audio_url: str | None = Field(None, description="S3 URL of recorded audio")
    transcript: list[dict[str, Any]] | None = Field(None, description="Conversation transcript")
    evaluation_result: dict[str, Any] | None = Field(None, description="LLM evaluation result")
    duration_seconds: float | None = Field(None, description="Call duration in seconds")
    attempt: int = Field(1, description="Attempt number (1-based)")
    error_message: str | None = Field(None, description="Error message if failed")

    @classmethod
    def from_execution_row(
        cls, execution: TestExecutionRow, scenario_name: str
    ) -> ExecutionSummaryResponse:
        """Create from TestExecutionRow with resolved scenario name."""
        transcript = parse_jsonb_list(execution.transcript)
        evaluation_result = parse_jsonb_dict(execution.evaluation_result)
        return cls(
            id=str(execution.id),
            scenario_id=str(execution.scenario_id),
            scenario_name=scenario_name,
            status=execution.status,
            audio_url=execution.audio_url,
            transcript=transcript,
            evaluation_result=evaluation_result,
            duration_seconds=execution.duration_seconds,
            attempt=execution.attempt,
            error_message=execution.error_message,
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_id": "550e8400-e29b-41d4-a716-446655440001",
                "scenario_name": "Order Status Check",
                "status": "completed",
                "audio_url": "s3://bucket/audio.wav",
                "duration_seconds": 30.5,
                "attempt": 1,
            }
        }
    )


class SuiteRunResponse(BaseModel):
    """Full suite run with embedded executions."""

    id: str = Field(..., description="Suite run UUID")
    suite_id: str = Field(..., description="Test suite UUID")
    status: str = Field(
        ...,
        description="Status (pending, running, completed, failed, cancelled)",
    )
    total_scenarios: int = Field(..., description="Total scenarios in run")
    completed_scenarios: int = Field(0, description="Number completed")
    failed_scenarios: int = Field(0, description="Number failed")
    triggered_by: str | None = Field(None, description="User ID who triggered")
    started_at: datetime | None = Field(None, description="When run started")
    completed_at: datetime | None = Field(None, description="When run completed")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    executions: list[ExecutionSummaryResponse] = Field(
        default_factory=list, description="Executions in this run"
    )

    @classmethod
    def from_row(
        cls,
        run: TestSuiteRunRow,
        executions: list[ExecutionSummaryResponse],
    ) -> SuiteRunResponse:
        """Create from TestSuiteRunRow with embedded executions."""
        return cls(
            id=str(run.id),
            suite_id=str(run.suite_id),
            status=run.status,
            total_scenarios=run.total_scenarios,
            completed_scenarios=run.completed_scenarios,
            failed_scenarios=run.failed_scenarios,
            triggered_by=run.triggered_by,
            started_at=run.started_at,
            completed_at=run.completed_at,
            created_at=run.created_at,
            executions=executions,
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "suite_id": "550e8400-e29b-41d4-a716-446655440001",
                "status": "running",
                "total_scenarios": 5,
                "completed_scenarios": 2,
                "failed_scenarios": 0,
                "triggered_by": "user-123",
                "executions": [],
            }
        }
    )
