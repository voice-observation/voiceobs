"""Common dependencies for test management routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status

from voiceobs.server.db.repositories.persona import PersonaRepository
from voiceobs.server.db.repositories.test_execution import TestExecutionRepository
from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository
from voiceobs.server.db.repositories.test_suite import TestSuiteRepository
from voiceobs.server.dependencies import (
    get_persona_repository,
    get_test_execution_repository,
    get_test_scenario_repository,
    get_test_suite_repository,
    is_using_postgres,
)
from voiceobs.server.utils import parse_uuid


def require_postgres() -> None:
    """Dependency to ensure PostgreSQL is being used.

    Raises:
        HTTPException: If PostgreSQL is not configured.
    """
    if not is_using_postgres():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Test API requires PostgreSQL database",
        )


def get_test_suite_repo() -> TestSuiteRepository:
    """Dependency to get test suite repository.

    Returns:
        Test suite repository.
    """
    require_postgres()
    return get_test_suite_repository()


# Make these functions easily mockable by exposing them at module level
__all__ = [
    "require_postgres",
    "get_test_suite_repo",
    "get_test_scenario_repo",
    "get_test_execution_repo",
    "get_persona_repo",
    "get_test_repos",
    "parse_suite_id",
    "parse_scenario_id",
    "parse_execution_id",
    "parse_persona_id",
    "validate_suite_exists",
    "validate_scenario_exists",
    "validate_persona_exists",
    "parse_scenario_ids",
]


def get_test_scenario_repo() -> TestScenarioRepository:
    """Dependency to get test scenario repository.

    Returns:
        Test scenario repository.
    """
    require_postgres()
    return get_test_scenario_repository()


def get_test_execution_repo() -> TestExecutionRepository:
    """Dependency to get test execution repository.

    Returns:
        Test execution repository.
    """
    require_postgres()
    return get_test_execution_repository()


def get_persona_repo() -> PersonaRepository:
    """Dependency to get persona repository.

    Returns:
        Persona repository.
    """
    require_postgres()
    return get_persona_repository()


def get_test_repos() -> tuple[TestSuiteRepository, TestScenarioRepository, TestExecutionRepository]:
    """Dependency to get all test repositories.

    Returns:
        Tuple of (suite repository, scenario repository, execution repository).

    Raises:
        HTTPException: If any repository is not available.
    """
    require_postgres()
    suite_repo = get_test_suite_repository()
    scenario_repo = get_test_scenario_repository()
    execution_repo = get_test_execution_repository()

    return suite_repo, scenario_repo, execution_repo


def parse_suite_id(suite_id: str) -> UUID:
    """Parse and validate suite ID.

    Args:
        suite_id: Suite ID string to parse.

    Returns:
        Parsed UUID.

    Raises:
        HTTPException: If UUID format is invalid.
    """
    return parse_uuid(suite_id, "suite")


def parse_scenario_id(scenario_id: str) -> UUID:
    """Parse and validate scenario ID.

    Args:
        scenario_id: Scenario ID string to parse.

    Returns:
        Parsed UUID.

    Raises:
        HTTPException: If UUID format is invalid.
    """
    return parse_uuid(scenario_id, "scenario")


def parse_execution_id(execution_id: str) -> UUID:
    """Parse and validate execution ID.

    Args:
        execution_id: Execution ID string to parse.

    Returns:
        Parsed UUID.

    Raises:
        HTTPException: If UUID format is invalid.
    """
    return parse_uuid(execution_id, "execution")


def parse_persona_id(persona_id: str) -> UUID:
    """Parse and validate persona ID.

    Args:
        persona_id: Persona ID string to parse.

    Returns:
        Parsed UUID.

    Raises:
        HTTPException: If UUID format is invalid.
    """
    return parse_uuid(persona_id, "persona")


async def validate_suite_exists(
    suite_id: str, suite_repo: TestSuiteRepository | None = None
) -> UUID:
    """Validate that a suite exists and return its UUID.

    Args:
        suite_id: Suite ID string to validate.
        suite_repo: Optional suite repository (if None, will be fetched).

    Returns:
        Parsed UUID of the suite.

    Raises:
        HTTPException: If UUID format is invalid or suite not found.
    """
    if suite_repo is None:
        suite_repo = get_test_suite_repo()

    suite_uuid = parse_suite_id(suite_id)
    suite = await suite_repo.get(suite_uuid)
    if suite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test suite '{suite_id}' not found",
        )
    return suite_uuid


async def validate_scenario_exists(
    scenario_id: str, scenario_repo: TestScenarioRepository | None = None
) -> UUID:
    """Validate that a scenario exists and return its UUID.

    Args:
        scenario_id: Scenario ID string to validate.
        scenario_repo: Optional scenario repository (if None, will be fetched).

    Returns:
        Parsed UUID of the scenario.

    Raises:
        HTTPException: If UUID format is invalid or scenario not found.
    """
    if scenario_repo is None:
        scenario_repo = get_test_scenario_repo()

    scenario_uuid = parse_scenario_id(scenario_id)
    scenario = await scenario_repo.get(scenario_uuid)
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test scenario '{scenario_id}' not found",
        )
    return scenario_uuid


async def validate_persona_exists(
    persona_id: str, persona_repo: PersonaRepository | None = None
) -> UUID:
    """Validate that a persona exists, is active, and return its UUID.

    Args:
        persona_id: Persona ID string to validate.
        persona_repo: Optional persona repository (if None, will be fetched).

    Returns:
        Parsed UUID of the persona.

    Raises:
        HTTPException: If UUID format is invalid, persona not found, or persona is inactive.
    """
    if persona_repo is None:
        persona_repo = get_persona_repo()

    persona_uuid = parse_persona_id(persona_id)
    persona = await persona_repo.get(persona_uuid)
    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )
    if not persona.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Persona '{persona_id}' is inactive",
        )
    return persona_uuid


def parse_scenario_ids(scenario_ids: list[str]) -> list[UUID]:
    """Parse and validate a list of scenario IDs.

    Args:
        scenario_ids: List of scenario ID strings to parse.

    Returns:
        List of parsed UUIDs.

    Raises:
        HTTPException: If any UUID format is invalid.
    """
    try:
        return [UUID(sid) for sid in scenario_ids]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario ID format: {e}",
        )
