"""Test scenario management routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository
from voiceobs.server.db.repositories.test_suite import TestSuiteRepository
from voiceobs.server.models import (
    ErrorResponse,
    TestScenarioCreateRequest,
    TestScenarioResponse,
    TestScenariosListResponse,
    TestScenarioUpdateRequest,
)
from voiceobs.server.routes.test_dependencies import (
    get_test_scenario_repo,
    get_test_suite_repo,
    parse_scenario_id,
    parse_suite_id,
    validate_suite_exists,
)

router = APIRouter(prefix="/api/v1/tests/scenarios", tags=["Test Scenarios"])


@router.post(
    "",
    response_model=TestScenarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create test scenario",
    description="Create a new test scenario.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Test suite not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def create_test_scenario(
    request: TestScenarioCreateRequest,
    scenario_repo: TestScenarioRepository = Depends(get_test_scenario_repo),
    suite_repo: TestSuiteRepository = Depends(get_test_suite_repo),
) -> TestScenarioResponse:
    """Create a new test scenario."""
    suite_uuid = await validate_suite_exists(request.suite_id, suite_repo)

    scenario = await scenario_repo.create(
        suite_id=suite_uuid,
        name=request.name,
        goal=request.goal,
        persona_json=request.persona_json,
        max_turns=request.max_turns,
        timeout=request.timeout,
    )

    return TestScenarioResponse(
        id=str(scenario.id),
        suite_id=str(scenario.suite_id),
        name=scenario.name,
        goal=scenario.goal,
        persona_json=scenario.persona_json,
        max_turns=scenario.max_turns,
        timeout=scenario.timeout,
    )


@router.get(
    "",
    response_model=TestScenariosListResponse,
    summary="List test scenarios",
    description="Get a list of test scenarios with optional filtering.",
    responses={
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def list_test_scenarios(
    suite_id: str | None = Query(None, description="Filter by test suite ID"),
    repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> TestScenariosListResponse:
    """List test scenarios with optional filtering."""
    suite_uuid = None
    if suite_id is not None:
        suite_uuid = parse_suite_id(suite_id)

    scenarios = await repo.list_all(suite_id=suite_uuid)

    return TestScenariosListResponse(
        count=len(scenarios),
        scenarios=[
            TestScenarioResponse(
                id=str(scenario.id),
                suite_id=str(scenario.suite_id),
                name=scenario.name,
                goal=scenario.goal,
                persona_json=scenario.persona_json,
                max_turns=scenario.max_turns,
                timeout=scenario.timeout,
            )
            for scenario in scenarios
        ],
    )


@router.get(
    "/{scenario_id}",
    response_model=TestScenarioResponse,
    summary="Get test scenario details",
    description="Get detailed information about a specific test scenario.",
    responses={
        404: {"model": ErrorResponse, "description": "Test scenario not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def get_test_scenario(
    scenario_id: str,
    repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> TestScenarioResponse:
    """Get test scenario details."""
    scenario_uuid = parse_scenario_id(scenario_id)
    scenario = await repo.get(scenario_uuid)
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test scenario '{scenario_id}' not found",
        )

    return TestScenarioResponse(
        id=str(scenario.id),
        suite_id=str(scenario.suite_id),
        name=scenario.name,
        goal=scenario.goal,
        persona_json=scenario.persona_json,
        max_turns=scenario.max_turns,
        timeout=scenario.timeout,
    )


@router.put(
    "/{scenario_id}",
    response_model=TestScenarioResponse,
    summary="Update test scenario",
    description="Update an existing test scenario.",
    responses={
        404: {"model": ErrorResponse, "description": "Test scenario not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def update_test_scenario(
    scenario_id: str,
    request: TestScenarioUpdateRequest,
    repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> TestScenarioResponse:
    """Update a test scenario."""
    scenario_uuid = parse_scenario_id(scenario_id)
    scenario = await repo.update(
        scenario_id=scenario_uuid,
        name=request.name,
        goal=request.goal,
        persona_json=request.persona_json,
        max_turns=request.max_turns,
        timeout=request.timeout,
    )

    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test scenario '{scenario_id}' not found",
        )

    return TestScenarioResponse(
        id=str(scenario.id),
        suite_id=str(scenario.suite_id),
        name=scenario.name,
        goal=scenario.goal,
        persona_json=scenario.persona_json,
        max_turns=scenario.max_turns,
        timeout=scenario.timeout,
    )


@router.delete(
    "/{scenario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete test scenario",
    description="Delete a test scenario.",
    responses={
        404: {"model": ErrorResponse, "description": "Test scenario not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def delete_test_scenario(
    scenario_id: str,
    repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> None:
    """Delete a test scenario."""
    scenario_uuid = parse_scenario_id(scenario_id)
    deleted = await repo.delete(scenario_uuid)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test scenario '{scenario_id}' not found",
        )
