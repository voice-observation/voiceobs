"""Tests for generation status endpoint."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from voiceobs.server.models import GenerationStatusResponse


class TestGenerationStatusResponseModel:
    """Tests for the GenerationStatusResponse model."""

    def test_generation_status_response_model(self):
        """Test GenerationStatusResponse model creation."""
        response = GenerationStatusResponse(
            suite_id="550e8400-e29b-41d4-a716-446655440000",
            status="generating",
            scenario_count=0,
            error=None,
        )

        assert response.suite_id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.status == "generating"
        assert response.scenario_count == 0
        assert response.error is None

    def test_generation_status_response_with_error(self):
        """Test GenerationStatusResponse with error."""
        response = GenerationStatusResponse(
            suite_id="550e8400-e29b-41d4-a716-446655440000",
            status="generation_failed",
            scenario_count=0,
            error="LLM service unavailable",
        )

        assert response.status == "generation_failed"
        assert response.error == "LLM service unavailable"

    def test_generation_status_response_ready_with_scenarios(self):
        """Test GenerationStatusResponse in ready status with scenarios."""
        response = GenerationStatusResponse(
            suite_id="550e8400-e29b-41d4-a716-446655440000",
            status="ready",
            scenario_count=5,
            error=None,
        )

        assert response.status == "ready"
        assert response.scenario_count == 5

    def test_generation_status_response_pending(self):
        """Test GenerationStatusResponse in pending status."""
        response = GenerationStatusResponse(
            suite_id="550e8400-e29b-41d4-a716-446655440000",
            status="pending",
            scenario_count=0,
            error=None,
        )

        assert response.status == "pending"
        assert response.scenario_count == 0


class TestGenerationStatusEndpoint:
    """Tests for the generation status endpoint."""

    @pytest.fixture
    def mock_test_suite_row(self):
        """Create a mock test suite row."""
        return MagicMock(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            name="Test Suite",
            status="generating",
            generation_error=None,
        )

    @pytest.fixture
    def mock_scenario_rows(self):
        """Create mock scenario rows."""
        return [
            MagicMock(id=UUID("550e8400-e29b-41d4-a716-446655440001")),
            MagicMock(id=UUID("550e8400-e29b-41d4-a716-446655440002")),
        ]

    @pytest.mark.asyncio
    async def test_get_generation_status_generating(self, mock_test_suite_row, mock_scenario_rows):
        """Test getting generation status for a suite in generating status."""
        from voiceobs.server.routes.test_suites import get_generation_status

        mock_suite_repo = MagicMock()
        mock_suite_repo.get = AsyncMock(return_value=mock_test_suite_row)

        mock_scenario_repo = MagicMock()
        mock_scenario_repo.list_all = AsyncMock(return_value=mock_scenario_rows)

        result = await get_generation_status(
            suite_id="550e8400-e29b-41d4-a716-446655440000",
            suite_repo=mock_suite_repo,
            scenario_repo=mock_scenario_repo,
        )

        assert result.suite_id == "550e8400-e29b-41d4-a716-446655440000"
        assert result.status == "generating"
        assert result.scenario_count == 2
        assert result.error is None

    @pytest.mark.asyncio
    async def test_get_generation_status_ready(self, mock_test_suite_row, mock_scenario_rows):
        """Test getting generation status for a suite in ready status."""
        from voiceobs.server.routes.test_suites import get_generation_status

        mock_test_suite_row.status = "ready"

        mock_suite_repo = MagicMock()
        mock_suite_repo.get = AsyncMock(return_value=mock_test_suite_row)

        mock_scenario_repo = MagicMock()
        mock_scenario_repo.list_all = AsyncMock(return_value=mock_scenario_rows)

        result = await get_generation_status(
            suite_id="550e8400-e29b-41d4-a716-446655440000",
            suite_repo=mock_suite_repo,
            scenario_repo=mock_scenario_repo,
        )

        assert result.status == "ready"
        assert result.scenario_count == 2

    @pytest.mark.asyncio
    async def test_get_generation_status_failed(self, mock_test_suite_row):
        """Test getting generation status for a suite with failed generation."""
        from voiceobs.server.routes.test_suites import get_generation_status

        mock_test_suite_row.status = "generation_failed"
        mock_test_suite_row.generation_error = "LLM service unavailable"

        mock_suite_repo = MagicMock()
        mock_suite_repo.get = AsyncMock(return_value=mock_test_suite_row)

        mock_scenario_repo = MagicMock()
        mock_scenario_repo.list_all = AsyncMock(return_value=[])

        result = await get_generation_status(
            suite_id="550e8400-e29b-41d4-a716-446655440000",
            suite_repo=mock_suite_repo,
            scenario_repo=mock_scenario_repo,
        )

        assert result.status == "generation_failed"
        assert result.error == "LLM service unavailable"
        assert result.scenario_count == 0

    @pytest.mark.asyncio
    async def test_get_generation_status_not_found(self):
        """Test getting generation status for non-existent suite."""
        from fastapi import HTTPException

        from voiceobs.server.routes.test_suites import get_generation_status

        mock_suite_repo = MagicMock()
        mock_suite_repo.get = AsyncMock(return_value=None)

        mock_scenario_repo = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_generation_status(
                suite_id="550e8400-e29b-41d4-a716-446655440000",
                suite_repo=mock_suite_repo,
                scenario_repo=mock_scenario_repo,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_generation_status_invalid_uuid(self):
        """Test getting generation status with invalid UUID."""
        from fastapi import HTTPException

        from voiceobs.server.routes.test_suites import get_generation_status

        mock_suite_repo = MagicMock()
        mock_scenario_repo = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_generation_status(
                suite_id="invalid-uuid",
                suite_repo=mock_suite_repo,
                scenario_repo=mock_scenario_repo,
            )

        assert exc_info.value.status_code == 400
