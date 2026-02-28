"""Test execution management routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from voiceobs.server.db.repositories.test_execution import TestExecutionRepository
from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository
from voiceobs.server.db.repositories.test_suite import TestSuiteRepository
from voiceobs.server.db.repositories.test_suite_run import TestSuiteRunRepository
from voiceobs.server.models import (
    ErrorResponse,
    TestExecutionResponse,
    TestRunRequest,
    TestRunResponse,
    TestSummaryResponse,
)
from voiceobs.server.routes.test_dependencies import (
    get_test_execution_repo,
    get_test_repos,
    parse_execution_id,
    parse_scenario_ids,
    parse_suite_id,
    validate_suite_exists,
)

router = APIRouter(prefix="/api/v1/tests", tags=["Test Executions"])


@router.post(
    "/run",
    response_model=TestRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger test execution",
    description="Trigger execution of test scenarios.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Test suite or scenario not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def run_tests(
    request: TestRunRequest,
    repos: tuple[
        TestSuiteRepository,
        TestScenarioRepository,
        TestExecutionRepository,
        TestSuiteRunRepository,
    ] = Depends(get_test_repos),
) -> TestRunResponse:
    """Trigger test execution."""
    suite_repo, scenario_repo, execution_repo, suite_run_repo = repos

    # Determine which scenarios to run
    scenario_ids: list[UUID] = []

    if request.suite_id:
        # Get all scenarios for the suite
        suite_uuid = await validate_suite_exists(request.suite_id, suite_repo)
        suite = await suite_repo.get_by_id(suite_uuid)
        if suite is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test suite '{request.suite_id}' not found",
            )
        scenarios = await scenario_repo.list_all(org_id=suite.org_id, suite_id=suite_uuid)
        scenario_ids = [s.id for s in scenarios]

        if not scenario_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Test suite '{request.suite_id}' has no scenarios",
            )

    if request.scenarios:
        # Use specific scenarios
        scenario_ids = parse_scenario_ids(request.scenarios)

        # Verify all scenarios exist (use get_by_id for legacy unscoped route)
        for sid in scenario_ids:
            scenario = await scenario_repo.get_by_id(sid)
            if scenario is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Test scenario '{sid}' not found",
                )

    if not scenario_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either suite_id or scenarios must be provided",
        )

    # Get org_id from suite (for suite_id path) or first scenario (for scenarios path)
    if request.suite_id:
        suite_uuid = await validate_suite_exists(request.suite_id, suite_repo)
        suite = await suite_repo.get_by_id(suite_uuid)
        org_id = suite.org_id if suite else None
        suite_id_for_run = suite_uuid
    else:
        first_scenario = await scenario_repo.get_by_id(scenario_ids[0])
        org_id = first_scenario.org_id if first_scenario else None
        suite_id_for_run = first_scenario.suite_id if first_scenario else None

    if org_id is None or suite_id_for_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not determine organization or suite for test run",
        )

    # Create suite run and execution(s)
    suite_run = await suite_run_repo.create(
        org_id=org_id,
        suite_id=suite_id_for_run,
        total_scenarios=len(scenario_ids),
        triggered_by=None,
    )

    # Create one execution per scenario (use first as representative for legacy response)
    execution = await execution_repo.create(
        org_id=org_id,
        suite_run_id=suite_run.id,
        scenario_id=scenario_ids[0],
        status="queued",
    )

    # Estimate duration (simple heuristic: 5 minutes per scenario)
    estimated_duration = len(scenario_ids) * 300

    return TestRunResponse(
        execution_id=str(execution.id),
        status=execution.status,
        scenarios_count=len(scenario_ids),
        estimated_duration=estimated_duration,
    )


@router.get(
    "/summary",
    response_model=TestSummaryResponse,
    summary="Get test summary statistics",
    description="Get test summary statistics with optional filtering by suite.",
    responses={
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def get_test_summary(
    suite_id: str | None = Query(None, description="Filter by test suite ID"),
    repo: TestExecutionRepository = Depends(get_test_execution_repo),
) -> TestSummaryResponse:
    """Get test summary statistics."""
    suite_uuid = None
    if suite_id is not None:
        suite_uuid = parse_suite_id(suite_id)

    summary = await repo.get_summary(suite_id=suite_uuid)

    return TestSummaryResponse(**summary)


@router.get(
    "/executions/{execution_id}",
    response_model=TestExecutionResponse,
    summary="Get execution status",
    description="Get the status and details of a test execution.",
    responses={
        404: {"model": ErrorResponse, "description": "Test execution not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def get_test_execution(
    execution_id: str,
    repo: TestExecutionRepository = Depends(get_test_execution_repo),
) -> TestExecutionResponse:
    """Get test execution status."""
    execution_uuid = parse_execution_id(execution_id)
    execution = await repo.get_by_id(execution_uuid)
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test execution '{execution_id}' not found",
        )

    return TestExecutionResponse(
        id=str(execution.id),
        scenario_id=str(execution.scenario_id),
        conversation_id=str(execution.conversation_id) if execution.conversation_id else None,
        status=execution.status,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        result_json=execution.result_json,
    )
