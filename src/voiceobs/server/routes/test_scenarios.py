"""Test scenario management routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from voiceobs.server.db.repositories.persona import PersonaRepository
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
    get_persona_repo,
    get_test_scenario_repo,
    get_test_suite_repo,
    parse_scenario_id,
    parse_suite_id,
    validate_persona_exists,
    validate_suite_exists,
)
from voiceobs.server.services.scenario_generation import PersonaMatcher

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
    persona_repo: PersonaRepository = Depends(get_persona_repo),
) -> TestScenarioResponse:
    """Create a new test scenario."""
    suite_uuid = await validate_suite_exists(request.suite_id, suite_repo)
    persona_uuid = await validate_persona_exists(request.persona_id, persona_repo)

    scenario = await scenario_repo.create(
        suite_id=suite_uuid,
        name=request.name,
        goal=request.goal,
        persona_id=persona_uuid,
        max_turns=request.max_turns,
        timeout=request.timeout,
        caller_behaviors=request.caller_behaviors,
        tags=request.tags,
    )

    return TestScenarioResponse(
        id=str(scenario.id),
        suite_id=str(scenario.suite_id),
        name=scenario.name,
        goal=scenario.goal,
        persona_id=str(scenario.persona_id),
        persona_name=scenario.persona_name,
        max_turns=scenario.max_turns,
        timeout=scenario.timeout,
        intent=scenario.intent,
        persona_traits=scenario.persona_traits if scenario.persona_traits else None,
        persona_match_score=scenario.persona_match_score,
        caller_behaviors=scenario.caller_behaviors if scenario.caller_behaviors else None,
        tags=scenario.tags if scenario.tags else None,
        status=scenario.status,
        is_manual=scenario.is_manual,
    )


@router.get(
    "",
    response_model=TestScenariosListResponse,
    summary="List test scenarios",
    description="Get a list of test scenarios with optional filtering and pagination.",
    responses={
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def list_test_scenarios(
    suite_id: str | None = Query(None, description="Filter by test suite ID"),
    status: str | None = Query(None, description="Filter by status (ready or draft)"),
    tags: list[str] | None = Query(
        None, description="Filter by tags (returns scenarios with ANY specified tag)"
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> TestScenariosListResponse:
    """List test scenarios with optional filtering and pagination."""
    suite_uuid = None
    if suite_id is not None:
        suite_uuid = parse_suite_id(suite_id)

    # Get total count for pagination
    total_count = await repo.count(
        suite_id=suite_uuid,
        status=status,
        tags=tags,
    )

    scenarios = await repo.list_all(
        suite_id=suite_uuid,
        status=status,
        tags=tags,
        limit=limit,
        offset=offset,
    )

    return TestScenariosListResponse(
        count=total_count,
        scenarios=[
            TestScenarioResponse(
                id=str(scenario.id),
                suite_id=str(scenario.suite_id),
                name=scenario.name,
                goal=scenario.goal,
                persona_id=str(scenario.persona_id),
                persona_name=scenario.persona_name,
                max_turns=scenario.max_turns,
                timeout=scenario.timeout,
                intent=scenario.intent,
                persona_traits=scenario.persona_traits if scenario.persona_traits else None,
                persona_match_score=scenario.persona_match_score,
                caller_behaviors=scenario.caller_behaviors if scenario.caller_behaviors else None,
                tags=scenario.tags if scenario.tags else None,
                status=scenario.status,
                is_manual=scenario.is_manual,
            )
            for scenario in scenarios
        ],
        limit=limit,
        offset=offset,
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
        persona_id=str(scenario.persona_id),
        persona_name=scenario.persona_name,
        max_turns=scenario.max_turns,
        timeout=scenario.timeout,
        intent=scenario.intent,
        persona_traits=scenario.persona_traits if scenario.persona_traits else None,
        persona_match_score=scenario.persona_match_score,
        caller_behaviors=scenario.caller_behaviors if scenario.caller_behaviors else None,
        tags=scenario.tags if scenario.tags else None,
        status=scenario.status,
        is_manual=scenario.is_manual,
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
    persona_repo: PersonaRepository = Depends(get_persona_repo),
    suite_repo: TestSuiteRepository = Depends(get_test_suite_repo),
) -> TestScenarioResponse:
    """Update a test scenario."""
    scenario_uuid = parse_scenario_id(scenario_id)

    # Validate suite if provided (for moving scenario to different suite)
    suite_uuid = None
    if request.suite_id is not None:
        suite_uuid = await validate_suite_exists(request.suite_id, suite_repo)

    # Validate persona if provided
    persona_uuid = None
    new_persona = None
    if request.persona_id is not None:
        persona_uuid = await validate_persona_exists(request.persona_id, persona_repo)
        # TODO: Once test scenarios are org-scoped, pass org_id here
        new_persona = await persona_repo._get_by_id_unchecked(persona_uuid)

    # Calculate new persona_match_score if persona is changing and scenario has traits
    new_match_score = None
    if persona_uuid is not None and new_persona is not None:
        # Get the existing scenario to check for persona_traits
        existing_scenario = await repo.get(scenario_uuid)
        if (
            existing_scenario is not None
            and existing_scenario.persona_traits
            and len(existing_scenario.persona_traits) > 0
        ):
            # Calculate the match score between scenario's persona_traits and new persona
            matcher = PersonaMatcher([new_persona])
            match_result = matcher.find_best_match(existing_scenario.persona_traits)
            new_match_score = match_result.score

    scenario = await repo.update(
        scenario_id=scenario_uuid,
        suite_id=suite_uuid,
        name=request.name,
        goal=request.goal,
        persona_id=persona_uuid,
        max_turns=request.max_turns,
        timeout=request.timeout,
        persona_match_score=new_match_score,
        caller_behaviors=request.caller_behaviors,
        tags=request.tags,
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
        persona_id=str(scenario.persona_id),
        persona_name=scenario.persona_name,
        max_turns=scenario.max_turns,
        timeout=scenario.timeout,
        intent=scenario.intent,
        persona_traits=scenario.persona_traits if scenario.persona_traits else None,
        persona_match_score=scenario.persona_match_score,
        caller_behaviors=scenario.caller_behaviors if scenario.caller_behaviors else None,
        tags=scenario.tags if scenario.tags else None,
        status=scenario.status,
        is_manual=scenario.is_manual,
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
