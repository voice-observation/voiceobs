"""Test suite management routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from voiceobs.server.db.repositories.test_suite import TestSuiteRepository
from voiceobs.server.models import (
    ErrorResponse,
    TestSuiteCreateRequest,
    TestSuiteResponse,
    TestSuitesListResponse,
    TestSuiteUpdateRequest,
)
from voiceobs.server.routes.test_dependencies import (
    get_test_suite_repo,
    parse_suite_id,
)

router = APIRouter(prefix="/api/v1/tests/suites", tags=["Test Suites"])


@router.post(
    "",
    response_model=TestSuiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create test suite",
    description="Create a new test suite.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        501: {"model": ErrorResponse, "description": "Test API requires PostgreSQL database"},
    },
)
async def create_test_suite(
    request: TestSuiteCreateRequest,
    repo: TestSuiteRepository = Depends(get_test_suite_repo),
) -> TestSuiteResponse:
    """Create a new test suite."""
    suite = await repo.create(
        name=request.name,
        description=request.description,
    )

    return TestSuiteResponse(
        id=str(suite.id),
        name=suite.name,
        description=suite.description,
        status=suite.status,
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
) -> TestSuitesListResponse:
    """List all test suites."""
    suites = await repo.list_all()

    return TestSuitesListResponse(
        count=len(suites),
        suites=[
            TestSuiteResponse(
                id=str(suite.id),
                name=suite.name,
                description=suite.description,
                status=suite.status,
                created_at=suite.created_at,
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
) -> TestSuiteResponse:
    """Get test suite details."""
    suite_uuid = parse_suite_id(suite_id)
    suite = await repo.get(suite_uuid)
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
        created_at=suite.created_at,
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
    suite = await repo.update(
        suite_id=suite_uuid,
        name=request.name,
        description=request.description,
        status=request.status,
    )

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
