"""Tests for triggering scenario generation on test suite creation."""

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from voiceobs.server.dependencies import (
    get_scenario_generation_service,
)


class TestGetScenarioGenerationService:
    """Tests for the get_scenario_generation_service dependency."""

    def test_get_scenario_generation_service_returns_none_when_not_postgres(self):
        """Test that get_scenario_generation_service returns None when not using PostgreSQL."""
        with patch("voiceobs.server.dependencies._use_postgres", False):
            with patch("voiceobs.server.dependencies._test_suite_repo", None):
                result = get_scenario_generation_service()
                assert result is None

    def test_get_scenario_generation_service_returns_service_when_postgres(self):
        """Test that get_scenario_generation_service returns service when using PostgreSQL."""
        # Create mock repositories
        mock_test_suite_repo = MagicMock()
        mock_test_scenario_repo = MagicMock()
        mock_persona_repo = MagicMock()
        mock_agent_repo = MagicMock()

        with (
            patch("voiceobs.server.dependencies._use_postgres", True),
            patch("voiceobs.server.dependencies._test_suite_repo", mock_test_suite_repo),
            patch("voiceobs.server.dependencies._test_scenario_repo", mock_test_scenario_repo),
            patch("voiceobs.server.dependencies._persona_repo", mock_persona_repo),
            patch("voiceobs.server.dependencies._agent_repo", mock_agent_repo),
            patch("voiceobs.server.dependencies._scenario_generation_service", None),
            patch("voiceobs.server.services.llm_factory.LLMServiceFactory") as mock_llm_factory,
        ):
            mock_llm_service = MagicMock()
            mock_llm_factory.create.return_value = mock_llm_service

            result = get_scenario_generation_service()

            assert result is not None
            mock_llm_factory.create.assert_called_once()


class TestCreateTestSuiteTriggersGeneration:
    """Tests for triggering generation on test suite creation."""

    @pytest.mark.asyncio
    async def test_create_endpoint_triggers_background_generation(self):
        """Test that creating a test suite triggers background generation."""
        from voiceobs.server.models import TestSuiteCreateRequest
        from voiceobs.server.routes.test_suites import create_test_suite

        # Create mock repositories
        mock_suite_repo = MagicMock()
        mock_agent_repo = MagicMock()

        # Create mock suite that will be returned
        mock_suite = MagicMock()
        mock_suite.id = UUID("550e8400-e29b-41d4-a716-446655440000")
        mock_suite.name = "Test Suite"
        mock_suite.description = "A test suite"
        mock_suite.status = "pending"
        mock_suite.agent_id = UUID("550e8400-e29b-41d4-a716-446655440001")
        mock_suite.test_scopes = ["core_flows"]
        mock_suite.thoroughness = 1
        mock_suite.edge_cases = []
        mock_suite.evaluation_strictness = "balanced"
        mock_suite.created_at = None

        # Create mock agent
        mock_agent = MagicMock()
        mock_agent.id = UUID("550e8400-e29b-41d4-a716-446655440001")

        # Configure mocks
        mock_suite_repo.create = MagicMock(return_value=mock_suite)
        mock_agent_repo.get = MagicMock(return_value=mock_agent)

        # Create mock generation service
        mock_generation_service = MagicMock()

        # Create request
        request = TestSuiteCreateRequest(
            name="Test Suite",
            description="A test suite",
            agent_id="550e8400-e29b-41d4-a716-446655440001",
        )

        with patch(
            "voiceobs.server.routes.test_suites.get_scenario_generation_service",
            return_value=mock_generation_service,
        ):
            # Need to await the coroutines
            mock_suite_repo.create.return_value = mock_suite
            mock_agent_repo.get.return_value = mock_agent

            # Make the mock methods async
            async def mock_create(*args, **kwargs):
                return mock_suite

            async def mock_get_agent(agent_id):
                return mock_agent

            mock_suite_repo.create = mock_create
            mock_agent_repo.get = mock_get_agent

            response = await create_test_suite(
                request=request,
                repo=mock_suite_repo,
                agent_repo=mock_agent_repo,
            )

            # Verify generation was triggered
            mock_generation_service.start_background_generation.assert_called_once_with(
                mock_suite.id
            )

            # Verify response is correct
            assert response.id == str(mock_suite.id)
            assert response.name == "Test Suite"

    @pytest.mark.asyncio
    async def test_create_endpoint_does_not_fail_when_generation_service_unavailable(
        self,
    ):
        """Test that suite creation succeeds even if generation service is unavailable."""
        from voiceobs.server.models import TestSuiteCreateRequest
        from voiceobs.server.routes.test_suites import create_test_suite

        # Create mock repositories
        mock_suite_repo = MagicMock()
        mock_agent_repo = MagicMock()

        # Create mock suite that will be returned
        mock_suite = MagicMock()
        mock_suite.id = UUID("550e8400-e29b-41d4-a716-446655440000")
        mock_suite.name = "Test Suite"
        mock_suite.description = "A test suite"
        mock_suite.status = "pending"
        mock_suite.agent_id = UUID("550e8400-e29b-41d4-a716-446655440001")
        mock_suite.test_scopes = ["core_flows"]
        mock_suite.thoroughness = 1
        mock_suite.edge_cases = []
        mock_suite.evaluation_strictness = "balanced"
        mock_suite.created_at = None

        # Create mock agent
        mock_agent = MagicMock()
        mock_agent.id = UUID("550e8400-e29b-41d4-a716-446655440001")

        # Create request
        request = TestSuiteCreateRequest(
            name="Test Suite",
            description="A test suite",
            agent_id="550e8400-e29b-41d4-a716-446655440001",
        )

        with patch(
            "voiceobs.server.routes.test_suites.get_scenario_generation_service",
            return_value=None,
        ):
            # Make the mock methods async
            async def mock_create(*args, **kwargs):
                return mock_suite

            async def mock_get_agent(agent_id):
                return mock_agent

            mock_suite_repo.create = mock_create
            mock_agent_repo.get = mock_get_agent

            # Should not raise an exception
            response = await create_test_suite(
                request=request,
                repo=mock_suite_repo,
                agent_repo=mock_agent_repo,
            )

            # Verify response is correct (suite still created)
            assert response.id == str(mock_suite.id)
            assert response.name == "Test Suite"

    @pytest.mark.asyncio
    async def test_create_endpoint_does_not_fail_when_generation_raises_exception(
        self,
    ):
        """Test that suite creation succeeds even if generation service raises."""
        from voiceobs.server.models import TestSuiteCreateRequest
        from voiceobs.server.routes.test_suites import create_test_suite

        # Create mock repositories
        mock_suite_repo = MagicMock()
        mock_agent_repo = MagicMock()

        # Create mock suite that will be returned
        mock_suite = MagicMock()
        mock_suite.id = UUID("550e8400-e29b-41d4-a716-446655440000")
        mock_suite.name = "Test Suite"
        mock_suite.description = "A test suite"
        mock_suite.status = "pending"
        mock_suite.agent_id = UUID("550e8400-e29b-41d4-a716-446655440001")
        mock_suite.test_scopes = ["core_flows"]
        mock_suite.thoroughness = 1
        mock_suite.edge_cases = []
        mock_suite.evaluation_strictness = "balanced"
        mock_suite.created_at = None

        # Create mock agent
        mock_agent = MagicMock()
        mock_agent.id = UUID("550e8400-e29b-41d4-a716-446655440001")

        # Create mock generation service that raises
        mock_generation_service = MagicMock()
        mock_generation_service.start_background_generation.side_effect = Exception(
            "LLM service unavailable"
        )

        # Create request
        request = TestSuiteCreateRequest(
            name="Test Suite",
            description="A test suite",
            agent_id="550e8400-e29b-41d4-a716-446655440001",
        )

        with patch(
            "voiceobs.server.routes.test_suites.get_scenario_generation_service",
            return_value=mock_generation_service,
        ):
            # Make the mock methods async
            async def mock_create(*args, **kwargs):
                return mock_suite

            async def mock_get_agent(agent_id):
                return mock_agent

            mock_suite_repo.create = mock_create
            mock_agent_repo.get = mock_get_agent

            # Should not raise an exception
            response = await create_test_suite(
                request=request,
                repo=mock_suite_repo,
                agent_repo=mock_agent_repo,
            )

            # Verify response is correct (suite still created)
            assert response.id == str(mock_suite.id)
            assert response.name == "Test Suite"
