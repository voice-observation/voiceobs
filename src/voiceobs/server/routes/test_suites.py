"""Test suite management routes."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from voiceobs.server.db.repositories.agent import AgentRepository
from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository
from voiceobs.server.db.repositories.test_suite import TestSuiteRepository
from voiceobs.server.dependencies import get_agent_repository, get_scenario_generation_service
from voiceobs.server.models import (
    ErrorResponse,
    GenerateScenariosRequest,
    GenerationStatusResponse,
    TestSuiteCreateRequest,
    TestSuiteResponse,
    TestSuitesListResponse,
    TestSuiteUpdateRequest,
)
from voiceobs.server.routes.test_dependencies import (
    get_test_scenario_repo,
    get_test_suite_repo,
    parse_suite_id,
    require_postgres,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tests/suites", tags=["Test Suites"])


def get_agent_repo() -> AgentRepository:
    """Dependency to get agent repository.

    Returns:
        Agent repository.

    Raises:
        HTTPException: If repository is not available.
    """
    require_postgres()
    repo = get_agent_repository()
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent repository not available",
        )
    return repo


async def validate_agent_exists(agent_id: str, agent_repo: AgentRepository) -> UUID:
    """Validate that an agent exists and return its UUID.

    Args:
        agent_id: Agent ID string to validate.
        agent_repo: Agent repository.

    Returns:
        Parsed UUID of the agent.

    Raises:
        HTTPException: If UUID format is invalid or agent not found.
    """
    try:
        agent_uuid = UUID(agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent ID format: {agent_id}",
        )

    agent = await agent_repo.get(agent_uuid)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    return agent_uuid


@router.post(
    "",
    response_model=TestSuiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create test suite",
    description="Create a new test suite.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Agent not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def create_test_suite(
    request: TestSuiteCreateRequest,
    repo: TestSuiteRepository = Depends(get_test_suite_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
) -> TestSuiteResponse:
    """Create a new test suite."""
    # Validate that the agent exists
    agent_uuid = await validate_agent_exists(request.agent_id, agent_repo)

    suite = await repo.create(
        name=request.name,
        description=request.description,
        agent_id=agent_uuid,
        test_scopes=request.test_scopes,
        thoroughness=request.thoroughness,
        edge_cases=request.edge_cases,
        evaluation_strictness=request.evaluation_strictness,
    )

    # Trigger background scenario generation
    try:
        service = get_scenario_generation_service()
        if service is not None:
            service.start_background_generation(suite.id)
            logger.info(f"Started background generation for test suite {suite.id}")
    except Exception as e:
        logger.warning(f"Failed to start scenario generation for suite {suite.id}: {e}")
        # Don't fail the request, just log the warning
        # The suite is still created with status "pending"

    return TestSuiteResponse(
        id=str(suite.id),
        name=suite.name,
        description=suite.description,
        status=suite.status,
        agent_id=str(suite.agent_id) if suite.agent_id else None,
        test_scopes=suite.test_scopes or ["core_flows", "common_mistakes"],
        thoroughness=suite.thoroughness,
        edge_cases=suite.edge_cases or [],
        evaluation_strictness=suite.evaluation_strictness,
        created_at=suite.created_at,
    )


@router.get(
    "",
    response_model=TestSuitesListResponse,
    summary="List test suites",
    description="Get a list of all test suites.",
    responses={
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def list_test_suites(
    repo: TestSuiteRepository = Depends(get_test_suite_repo),
    scenario_repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> TestSuitesListResponse:
    """List all test suites."""
    suites = await repo.list_all()

    # Get all scenarios to count per suite efficiently
    all_scenarios = await scenario_repo.list_all()
    scenario_counts: dict[UUID, int] = {}
    for scenario in all_scenarios:
        suite_id = scenario.suite_id
        scenario_counts[suite_id] = scenario_counts.get(suite_id, 0) + 1

    return TestSuitesListResponse(
        count=len(suites),
        suites=[
            TestSuiteResponse(
                id=str(suite.id),
                name=suite.name,
                description=suite.description,
                status=suite.status,
                agent_id=str(suite.agent_id) if suite.agent_id else None,
                test_scopes=suite.test_scopes or ["core_flows", "common_mistakes"],
                thoroughness=suite.thoroughness,
                edge_cases=suite.edge_cases or [],
                evaluation_strictness=suite.evaluation_strictness,
                created_at=suite.created_at,
                scenario_count=scenario_counts.get(suite.id, 0),
            )
            for suite in suites
        ],
    )


@router.get(
    "/{suite_id}",
    response_model=TestSuiteResponse,
    summary="Get test suite details",
    description="Get detailed information about a specific test suite.",
    responses={
        404: {"model": ErrorResponse, "description": "Test suite not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def get_test_suite(
    suite_id: str,
    repo: TestSuiteRepository = Depends(get_test_suite_repo),
    scenario_repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> TestSuiteResponse:
    """Get test suite details."""
    suite_uuid = parse_suite_id(suite_id)
    suite = await repo.get(suite_uuid)
    if suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test suite '{suite_id}' not found",
        )

    # Get scenario count for this suite
    scenarios = await scenario_repo.list_all(suite_id=suite_uuid)

    return TestSuiteResponse(
        id=str(suite.id),
        name=suite.name,
        description=suite.description,
        status=suite.status,
        agent_id=str(suite.agent_id) if suite.agent_id else None,
        test_scopes=suite.test_scopes or ["core_flows", "common_mistakes"],
        thoroughness=suite.thoroughness,
        edge_cases=suite.edge_cases or [],
        evaluation_strictness=suite.evaluation_strictness,
        created_at=suite.created_at,
        scenario_count=len(scenarios),
    )


@router.put(
    "/{suite_id}",
    response_model=TestSuiteResponse,
    summary="Update test suite",
    description="Update an existing test suite.",
    responses={
        404: {"model": ErrorResponse, "description": "Test suite not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def update_test_suite(
    suite_id: str,
    request: TestSuiteUpdateRequest,
    repo: TestSuiteRepository = Depends(get_test_suite_repo),
) -> TestSuiteResponse:
    """Update a test suite."""
    suite_uuid = parse_suite_id(suite_id)
    suite = await repo.update(suite_uuid, request.model_dump(exclude_unset=True))

    if suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test suite '{suite_id}' not found",
        )

    return TestSuiteResponse(
        id=str(suite.id),
        name=suite.name,
        description=suite.description,
        status=suite.status,
        agent_id=str(suite.agent_id) if suite.agent_id else None,
        test_scopes=suite.test_scopes or ["core_flows", "common_mistakes"],
        thoroughness=suite.thoroughness,
        edge_cases=suite.edge_cases or [],
        evaluation_strictness=suite.evaluation_strictness,
        created_at=suite.created_at,
    )


@router.delete(
    "/{suite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete test suite",
    description="Delete a test suite.",
    responses={
        404: {"model": ErrorResponse, "description": "Test suite not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def delete_test_suite(
    suite_id: str,
    repo: TestSuiteRepository = Depends(get_test_suite_repo),
) -> None:
    """Delete a test suite."""
    suite_uuid = parse_suite_id(suite_id)
    deleted = await repo.delete(suite_uuid)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test suite '{suite_id}' not found",
        )


@router.get(
    "/{suite_id}/generation-status",
    response_model=GenerationStatusResponse,
    summary="Get generation status",
    description="Get the scenario generation status for a test suite.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid suite ID format"},
        404: {"model": ErrorResponse, "description": "Test suite not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def get_generation_status(
    suite_id: str,
    suite_repo: TestSuiteRepository = Depends(get_test_suite_repo),
    scenario_repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> GenerationStatusResponse:
    """Get the scenario generation status for a test suite.

    This endpoint returns the current generation status, including:
    - The test suite status (pending, generating, ready, generation_failed)
    - The number of scenarios generated so far
    - Any error message if generation failed

    Args:
        suite_id: The test suite UUID.
        suite_repo: Test suite repository dependency.
        scenario_repo: Test scenario repository dependency.

    Returns:
        GenerationStatusResponse with status information.

    Raises:
        HTTPException: If suite not found or invalid UUID format.
    """
    suite_uuid = parse_suite_id(suite_id)
    suite = await suite_repo.get(suite_uuid)

    if suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test suite '{suite_id}' not found",
        )

    scenarios = await scenario_repo.list_all(suite_id=suite_uuid)

    return GenerationStatusResponse(
        suite_id=str(suite.id),
        status=suite.status,
        scenario_count=len(scenarios),
        error=suite.generation_error,
    )


@router.post(
    "/{suite_id}/generate-scenarios",
    response_model=GenerationStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate more scenarios",
    description="Trigger generation of additional scenarios for a test suite.",
    responses={
        400: {"model": ErrorResponse, "description": "Suite is already generating or invalid ID"},
        404: {"model": ErrorResponse, "description": "Test suite not found"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def generate_more_scenarios(
    suite_id: str,
    request: GenerateScenariosRequest,
    suite_repo: TestSuiteRepository = Depends(get_test_suite_repo),
    scenario_repo: TestScenarioRepository = Depends(get_test_scenario_repo),
) -> GenerationStatusResponse:
    """Generate additional scenarios for a test suite.

    This endpoint triggers background generation of new test scenarios
    for an existing test suite. The generation uses LLMs to create
    realistic test scenarios based on the agent and suite configuration.

    Args:
        suite_id: The test suite UUID.
        request: Request containing optional generation prompt.
        suite_repo: Test suite repository dependency.
        scenario_repo: Test scenario repository dependency.

    Returns:
        GenerationStatusResponse with status "generating".

    Raises:
        HTTPException: If suite not found, already generating, or invalid UUID.
    """
    suite_uuid = parse_suite_id(suite_id)
    suite = await suite_repo.get(suite_uuid)

    if suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test suite '{suite_id}' not found",
        )

    if suite.status == "generating":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test suite is already generating scenarios",
        )

    # Update status to "generating"
    await suite_repo.update(
        suite_id=suite_uuid,
        updates={"status": "generating", "generation_error": None},
    )

    # Get current scenario count
    scenarios = await scenario_repo.list_all(suite_id=suite_uuid)

    # Trigger background generation
    try:
        service = get_scenario_generation_service()
        if service is not None:
            service.start_background_generation(suite_uuid, request.prompt)
            logger.info(
                f"Started background generation for test suite {suite_id} "
                f"with prompt: {request.prompt}"
            )
    except Exception as e:
        logger.warning(f"Failed to start scenario generation for suite {suite_id}: {e}")
        # Revert status on failure
        await suite_repo.update(
            suite_id=suite_uuid,
            updates={"status": "generation_failed", "generation_error": str(e)},
        )

    return GenerationStatusResponse(
        suite_id=str(suite_uuid),
        status="generating",
        scenario_count=len(scenarios),
        error=None,
    )
