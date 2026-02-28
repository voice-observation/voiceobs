"""Suite run routes for triggering, polling, and cancelling test runs."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from voiceobs.server.auth.context import AuthContext, require_org_membership
from voiceobs.server.db.repositories.test_execution import TestExecutionRepository
from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository
from voiceobs.server.db.repositories.test_suite import TestSuiteRepository
from voiceobs.server.db.repositories.test_suite_run import TestSuiteRunRepository
from voiceobs.server.models import (
    ErrorResponse,
    ExecutionSummaryResponse,
    SuiteRunResponse,
    SuiteRunTriggerResponse,
    TestExecutionResponse,
)
from voiceobs.server.routes.test_dependencies import (
    get_execution_orchestration_service_or_raise,
    get_test_execution_repo,
    get_test_scenario_repo,
    get_test_suite_repo,
    get_test_suite_run_repo,
    parse_execution_id,
    parse_suite_run_id,
    validate_scenario_exists,
    validate_suite_exists,
)
from voiceobs.server.utils.storage import get_audio_bytes_from_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/orgs/{org_id}", tags=["Suite Runs"])


@router.post(
    "/test-suites/{suite_id}/run",
    response_model=SuiteRunTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run entire test suite",
    description="Trigger execution of all ready scenarios in a test suite.",
    responses={
        400: {"model": ErrorResponse, "description": "Suite has no ready scenarios"},
        404: {"model": ErrorResponse, "description": "Test suite not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL"},
        503: {"model": ErrorResponse, "description": "SQS not configured"},
    },
)
async def run_suite(
    org_id: UUID,
    suite_id: str,
    auth: AuthContext = Depends(require_org_membership),
    orchestration_service=Depends(get_execution_orchestration_service_or_raise),
    suite_repo: TestSuiteRepository = Depends(get_test_suite_repo),
    scenario_repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> SuiteRunTriggerResponse:
    """Trigger execution of all ready scenarios in a test suite."""

    suite_uuid = await validate_suite_exists(suite_id, suite_repo, org_id=org_id)
    scenarios = await scenario_repo.list_all(org_id=org_id, suite_id=suite_uuid, status="ready")
    if not scenarios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test suite has no ready scenarios",
        )

    result = await orchestration_service.trigger_suite_run(
        org_id=org_id,
        suite_id=suite_uuid,
        triggered_by=str(auth.user.id),
    )

    return SuiteRunTriggerResponse(
        suite_run_id=str(result.suite_run_id),
        status="running",
        total_scenarios=result.total_scenarios,
    )


@router.post(
    "/test-scenarios/{scenario_id}/run",
    response_model=SuiteRunTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run single scenario",
    description="Trigger execution of a single test scenario.",
    responses={
        404: {"model": ErrorResponse, "description": "Test scenario not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL"},
        503: {"model": ErrorResponse, "description": "SQS not configured"},
    },
)
async def run_scenario(
    org_id: UUID,
    scenario_id: str,
    auth: AuthContext = Depends(require_org_membership),
    orchestration_service=Depends(get_execution_orchestration_service_or_raise),
    scenario_repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> SuiteRunTriggerResponse:
    """Trigger execution of a single test scenario."""

    scenario_uuid = await validate_scenario_exists(scenario_id, scenario_repo, org_id=org_id)

    result = await orchestration_service.trigger_scenario_run(
        org_id=org_id,
        scenario_id=scenario_uuid,
        triggered_by=str(auth.user.id),
    )

    return SuiteRunTriggerResponse(
        suite_run_id=str(result.suite_run_id),
        status="running",
        total_scenarios=result.total_scenarios,
    )


@router.get(
    "/suite-runs/{suite_run_id}",
    response_model=SuiteRunResponse,
    summary="Get suite run status",
    description="Get suite run with embedded execution summaries.",
    responses={
        404: {"model": ErrorResponse, "description": "Suite run not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL"},
    },
)
async def get_suite_run(
    org_id: UUID,
    suite_run_id: str,
    auth: AuthContext = Depends(require_org_membership),
    suite_run_repo: TestSuiteRunRepository = Depends(get_test_suite_run_repo),
    execution_repo: TestExecutionRepository = Depends(get_test_execution_repo),
    scenario_repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> SuiteRunResponse:
    """Get suite run with execution summaries."""
    run_uuid = parse_suite_run_id(suite_run_id)
    run = await suite_run_repo.get(run_uuid, org_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suite run '{suite_run_id}' not found",
        )

    executions = await execution_repo.list_by_suite_run(org_id, run.id)
    scenario_ids = [e.scenario_id for e in executions]
    scenario_map: dict[UUID, str] = {}
    for sid in scenario_ids:
        scenario = await scenario_repo.get_by_id(sid)
        scenario_map[sid] = scenario.name if scenario else "Unknown"

    exec_summaries = [
        ExecutionSummaryResponse.from_execution_row(e, scenario_map.get(e.scenario_id, "Unknown"))
        for e in executions
    ]

    return SuiteRunResponse.from_row(run, exec_summaries)


@router.post(
    "/suite-runs/{suite_run_id}/cancel",
    response_model=SuiteRunResponse,
    summary="Cancel suite run",
    description="Cancel a running suite run and all pending/queued executions.",
    responses={
        404: {"model": ErrorResponse, "description": "Suite run not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL"},
    },
)
async def cancel_suite_run(
    org_id: UUID,
    suite_run_id: str,
    auth: AuthContext = Depends(require_org_membership),
    suite_run_repo: TestSuiteRunRepository = Depends(get_test_suite_run_repo),
    execution_repo: TestExecutionRepository = Depends(get_test_execution_repo),
    scenario_repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> SuiteRunResponse:
    """Cancel suite run and pending executions."""
    run_uuid = parse_suite_run_id(suite_run_id)
    run = await suite_run_repo.get(run_uuid, org_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suite run '{suite_run_id}' not found",
        )

    await suite_run_repo.update(
        run.id, org_id, {"status": "cancelled", "completed_at": datetime.utcnow()}
    )

    executions = await execution_repo.list_by_suite_run(org_id, run.id)
    for e in executions:
        if e.status in ("pending", "queued"):
            await execution_repo.update(e.id, org_id, {"status": "cancelled"})

    updated_run = await suite_run_repo.get(run.id, org_id)
    if updated_run is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch updated suite run",
        )

    updated_executions = await execution_repo.list_by_suite_run(org_id, run.id)
    exec_summaries = []
    for e in updated_executions:
        scenario = await scenario_repo.get_by_id(e.scenario_id)
        name = scenario.name if scenario else "Unknown"
        exec_summaries.append(ExecutionSummaryResponse.from_execution_row(e, name))

    return SuiteRunResponse.from_row(updated_run, exec_summaries)


@router.get(
    "/executions/{execution_id}",
    response_model=TestExecutionResponse,
    summary="Get execution detail",
    description="Get full execution with audio_url, transcript, evaluation_result.",
    responses={
        404: {"model": ErrorResponse, "description": "Execution not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL"},
    },
)
async def get_execution(
    org_id: UUID,
    execution_id: str,
    auth: AuthContext = Depends(require_org_membership),
    execution_repo: TestExecutionRepository = Depends(get_test_execution_repo),
) -> TestExecutionResponse:
    """Get execution detail."""
    exec_uuid = parse_execution_id(execution_id)
    execution = await execution_repo.get(exec_uuid, org_id)
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution '{execution_id}' not found",
        )

    return TestExecutionResponse.from_row(execution)


@router.get(
    "/executions/{execution_id}/audio/stream",
    summary="Stream execution audio",
    description="Stream execution audio file (avoids CORS when loading from S3).",
    responses={
        404: {"description": "Execution not found or no audio"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL"},
    },
)
async def stream_execution_audio(
    org_id: UUID,
    execution_id: str,
    auth: AuthContext = Depends(require_org_membership),
    execution_repo: TestExecutionRepository = Depends(get_test_execution_repo),
) -> Response:
    """Stream execution audio from S3 (same-origin, no CORS)."""
    exec_uuid = parse_execution_id(execution_id)
    execution = await execution_repo.get(exec_uuid, org_id)
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution '{execution_id}' not found",
        )

    if not execution.audio_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution has no audio recorded",
        )

    audio_bytes = await get_audio_bytes_from_url(execution.audio_url)
    if audio_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found in storage",
        )

    content_type = "audio/ogg"
    if execution.audio_url.endswith(".wav"):
        content_type = "audio/wav"
    elif execution.audio_url.endswith(".m4a"):
        content_type = "audio/mp4"

    return Response(
        content=audio_bytes,
        media_type=content_type,
        headers={"Content-Length": str(len(audio_bytes))},
    )


@router.get(
    "/executions/{execution_id}/audio",
    summary="Get execution audio URL",
    description="Get URL for execution audio (stream endpoint, same-origin).",
    responses={
        404: {"model": ErrorResponse, "description": "Execution not found or no audio"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL"},
    },
)
async def get_execution_audio(
    org_id: UUID,
    execution_id: str,
    auth: AuthContext = Depends(require_org_membership),
    execution_repo: TestExecutionRepository = Depends(get_test_execution_repo),
) -> dict:
    """Get stream URL for execution audio (avoids CORS)."""
    exec_uuid = parse_execution_id(execution_id)
    execution = await execution_repo.get(exec_uuid, org_id)
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution '{execution_id}' not found",
        )

    if not execution.audio_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution has no audio recorded",
        )

    stream_path = f"/api/v1/orgs/{org_id}/executions/{execution_id}/audio/stream"
    return {"url": stream_path}
