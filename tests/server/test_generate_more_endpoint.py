"""Tests for generate more scenarios endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from voiceobs.server.models import GenerateScenariosRequest


class TestGenerateScenariosRequestModel:
    """Tests for the GenerateScenariosRequest model."""

    def test_generate_scenarios_request_model(self):
        """Test GenerateScenariosRequest model with prompt."""
        request = GenerateScenariosRequest(
            prompt="Generate scenarios for edge cases with angry customers"
        )
        assert request.prompt == "Generate scenarios for edge cases with angry customers"

    def test_generate_scenarios_request_prompt_optional(self):
        """Test that prompt is optional."""
        request = GenerateScenariosRequest()
        assert request.prompt is None

    def test_generate_scenarios_request_empty_string_prompt(self):
        """Test that empty string prompt is valid."""
        request = GenerateScenariosRequest(prompt="")
        assert request.prompt == ""


class TestGenerateMoreEndpoint:
    """Tests for the POST /test-suites/{id}/generate-scenarios endpoint."""

    @pytest.fixture
    def mock_suite_repo(self):
        """Create a mock test suite repository."""
        return MagicMock()

    @pytest.fixture
    def mock_scenario_repo(self):
        """Create a mock test scenario repository."""
        return MagicMock()

    @pytest.fixture
    def mock_generation_service(self):
        """Create a mock scenario generation service."""
        service = MagicMock()
        service.start_background_generation = MagicMock()
        return service

    @pytest.fixture
    def test_client(self, mock_suite_repo, mock_scenario_repo, mock_generation_service):
        """Create a test client with mocked dependencies."""
        from voiceobs.server.app import create_app

        app = create_app()

        # Override dependencies
        from voiceobs.server.routes.test_dependencies import (
            get_test_scenario_repo,
            get_test_suite_repo,
        )

        app.dependency_overrides[get_test_suite_repo] = lambda: mock_suite_repo
        app.dependency_overrides[get_test_scenario_repo] = lambda: mock_scenario_repo

        with patch(
            "voiceobs.server.routes.test_suites.get_scenario_generation_service",
            return_value=mock_generation_service,
        ):
            yield TestClient(app)

    @pytest.mark.asyncio
    async def test_generate_more_scenarios_success(
        self, mock_suite_repo, mock_scenario_repo, mock_generation_service
    ):
        """Test successful generation trigger."""
        suite_id = uuid4()

        # Mock suite with "ready" status (not generating)
        mock_suite = MagicMock()
        mock_suite.id = suite_id
        mock_suite.status = "ready"
        mock_suite.generation_error = None
        mock_suite_repo.get = AsyncMock(return_value=mock_suite)
        mock_suite_repo.update = AsyncMock(return_value=mock_suite)

        # Mock scenarios list
        mock_scenario_repo.list_all = AsyncMock(return_value=[])

        from voiceobs.server.models.request import GenerateScenariosRequest
        from voiceobs.server.routes.test_suites import generate_more_scenarios

        request = GenerateScenariosRequest(prompt="Test edge cases")

        with patch(
            "voiceobs.server.routes.test_suites.get_scenario_generation_service",
            return_value=mock_generation_service,
        ):
            response = await generate_more_scenarios(
                suite_id=str(suite_id),
                request=request,
                suite_repo=mock_suite_repo,
                scenario_repo=mock_scenario_repo,
            )

        assert response.suite_id == str(suite_id)
        assert response.status == "generating"
        mock_generation_service.start_background_generation.assert_called_once_with(
            suite_id, "Test edge cases"
        )

    @pytest.mark.asyncio
    async def test_generate_more_scenarios_suite_not_found(
        self, mock_suite_repo, mock_scenario_repo
    ):
        """Test 404 when suite doesn't exist."""
        suite_id = uuid4()

        mock_suite_repo.get = AsyncMock(return_value=None)

        from fastapi import HTTPException

        from voiceobs.server.models.request import GenerateScenariosRequest
        from voiceobs.server.routes.test_suites import generate_more_scenarios

        request = GenerateScenariosRequest()

        with pytest.raises(HTTPException) as exc_info:
            await generate_more_scenarios(
                suite_id=str(suite_id),
                request=request,
                suite_repo=mock_suite_repo,
                scenario_repo=mock_scenario_repo,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_generate_more_scenarios_already_generating(
        self, mock_suite_repo, mock_scenario_repo
    ):
        """Test 400 when suite is already generating."""
        suite_id = uuid4()

        # Mock suite with "generating" status
        mock_suite = MagicMock()
        mock_suite.id = suite_id
        mock_suite.status = "generating"
        mock_suite_repo.get = AsyncMock(return_value=mock_suite)

        from fastapi import HTTPException

        from voiceobs.server.models.request import GenerateScenariosRequest
        from voiceobs.server.routes.test_suites import generate_more_scenarios

        request = GenerateScenariosRequest()

        with pytest.raises(HTTPException) as exc_info:
            await generate_more_scenarios(
                suite_id=str(suite_id),
                request=request,
                suite_repo=mock_suite_repo,
                scenario_repo=mock_scenario_repo,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "already generating" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_generate_more_scenarios_no_prompt(
        self, mock_suite_repo, mock_scenario_repo, mock_generation_service
    ):
        """Test generation without additional prompt."""
        suite_id = uuid4()

        mock_suite = MagicMock()
        mock_suite.id = suite_id
        mock_suite.status = "ready"
        mock_suite.generation_error = None
        mock_suite_repo.get = AsyncMock(return_value=mock_suite)
        mock_suite_repo.update = AsyncMock(return_value=mock_suite)

        mock_scenario_repo.list_all = AsyncMock(return_value=[])

        from voiceobs.server.models.request import GenerateScenariosRequest
        from voiceobs.server.routes.test_suites import generate_more_scenarios

        request = GenerateScenariosRequest()  # No prompt

        with patch(
            "voiceobs.server.routes.test_suites.get_scenario_generation_service",
            return_value=mock_generation_service,
        ):
            response = await generate_more_scenarios(
                suite_id=str(suite_id),
                request=request,
                suite_repo=mock_suite_repo,
                scenario_repo=mock_scenario_repo,
            )

        assert response.status == "generating"
        mock_generation_service.start_background_generation.assert_called_once_with(suite_id, None)

    @pytest.mark.asyncio
    async def test_generate_more_scenarios_updates_status_to_generating(
        self, mock_suite_repo, mock_scenario_repo, mock_generation_service
    ):
        """Test that suite status is updated to 'generating' before triggering."""
        suite_id = uuid4()

        mock_suite = MagicMock()
        mock_suite.id = suite_id
        mock_suite.status = "ready"
        mock_suite.generation_error = None
        mock_suite_repo.get = AsyncMock(return_value=mock_suite)
        mock_suite_repo.update = AsyncMock(return_value=mock_suite)

        mock_scenario_repo.list_all = AsyncMock(return_value=[MagicMock()])

        from voiceobs.server.models.request import GenerateScenariosRequest
        from voiceobs.server.routes.test_suites import generate_more_scenarios

        request = GenerateScenariosRequest(prompt="Test")

        with patch(
            "voiceobs.server.routes.test_suites.get_scenario_generation_service",
            return_value=mock_generation_service,
        ):
            response = await generate_more_scenarios(
                suite_id=str(suite_id),
                request=request,
                suite_repo=mock_suite_repo,
                scenario_repo=mock_scenario_repo,
            )

        # Verify status was updated to "generating"
        mock_suite_repo.update.assert_called_once()
        call_args = mock_suite_repo.update.call_args
        # Using keyword arguments: update(suite_id=..., updates=...)
        assert call_args.kwargs["suite_id"] == suite_id
        assert call_args.kwargs["updates"]["status"] == "generating"

        # Response should include scenario count
        assert response.scenario_count == 1

    @pytest.mark.asyncio
    async def test_generate_more_scenarios_invalid_uuid(self, mock_suite_repo, mock_scenario_repo):
        """Test 400 when suite ID is not a valid UUID."""
        from fastapi import HTTPException

        from voiceobs.server.models.request import GenerateScenariosRequest
        from voiceobs.server.routes.test_suites import generate_more_scenarios

        request = GenerateScenariosRequest()

        with pytest.raises(HTTPException) as exc_info:
            await generate_more_scenarios(
                suite_id="not-a-valid-uuid",
                request=request,
                suite_repo=mock_suite_repo,
                scenario_repo=mock_scenario_repo,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_generate_more_scenarios_service_exception(
        self, mock_suite_repo, mock_scenario_repo
    ):
        """Test that exception during generation reverts status."""
        suite_id = uuid4()

        mock_suite = MagicMock()
        mock_suite.id = suite_id
        mock_suite.status = "ready"
        mock_suite.generation_error = None
        mock_suite_repo.get = AsyncMock(return_value=mock_suite)
        mock_suite_repo.update = AsyncMock(return_value=mock_suite)

        mock_scenario_repo.list_all = AsyncMock(return_value=[])

        # Create a service that raises an exception
        mock_service = MagicMock()
        mock_service.start_background_generation = MagicMock(
            side_effect=RuntimeError("Service initialization failed")
        )

        from voiceobs.server.models.request import GenerateScenariosRequest
        from voiceobs.server.routes.test_suites import generate_more_scenarios

        request = GenerateScenariosRequest(prompt="Test")

        with patch(
            "voiceobs.server.routes.test_suites.get_scenario_generation_service",
            return_value=mock_service,
        ):
            response = await generate_more_scenarios(
                suite_id=str(suite_id),
                request=request,
                suite_repo=mock_suite_repo,
                scenario_repo=mock_scenario_repo,
            )

        # Verify status was reverted to "generation_failed"
        update_calls = mock_suite_repo.update.call_args_list
        assert len(update_calls) == 2  # First to "generating", then to "generation_failed"
        second_call = update_calls[1]
        assert second_call.kwargs["updates"]["status"] == "generation_failed"
        assert "Service initialization failed" in second_call.kwargs["updates"]["generation_error"]

        # Response should still be returned
        assert response.status == "generating"
