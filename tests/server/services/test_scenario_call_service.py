"""Unit tests for ScenarioCallService."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from voiceobs.server.db.models import (
    AgentRow,
    PersonaRow,
    TestExecutionRow,
    TestScenarioRow,
    TestSuiteRow,
)
from voiceobs.server.services.execution.scenario_call_service import ScenarioCallService


def _make_execution(org_id=None, scenario_id=None):
    return TestExecutionRow(
        id=uuid4(),
        org_id=org_id or uuid4(),
        suite_run_id=uuid4(),
        scenario_id=scenario_id or uuid4(),
        status="pending",
    )


def _make_scenario(org_id=None, suite_id=None, persona_id=None, timeout=2):
    return TestScenarioRow(
        id=uuid4(),
        suite_id=suite_id or uuid4(),
        org_id=org_id or uuid4(),
        name="Test Scenario",
        goal="Book a flight",
        persona_id=persona_id or uuid4(),
        persona_traits=["assertive", "patient"],
        caller_behaviors=["ask for price", "confirm booking"],
        timeout=timeout,
    )


def _make_suite(org_id=None, agent_id=None):
    return TestSuiteRow(
        id=uuid4(),
        org_id=org_id or uuid4(),
        name="Test Suite",
        agent_id=agent_id or uuid4(),
    )


def _make_agent(org_id=None, agent_type="phone", phone_number="+15551234567"):
    return AgentRow(
        id=uuid4(),
        org_id=org_id or uuid4(),
        name="Test Agent",
        goal="Help users",
        agent_type=agent_type,
        contact_info={"phone_number": phone_number} if agent_type == "phone" else {},
    )


def _make_persona(org_id=None, description="Friendly customer"):
    return PersonaRow(
        id=uuid4(),
        name="Test Persona",
        aggression=0.3,
        patience=0.8,
        verbosity=0.5,
        tts_provider="openai",
        description=description,
        traits=["friendly", "patient"],
    )


@pytest.fixture
def mock_repos():
    """Create mock repositories."""
    suite_run_repo = AsyncMock()
    suite_run_repo.get.return_value = MagicMock(
        completed_scenarios=0, failed_scenarios=0, total_scenarios=1
    )
    return {
        "execution_repo": AsyncMock(),
        "scenario_repo": AsyncMock(),
        "suite_repo": AsyncMock(),
        "suite_run_repo": suite_run_repo,
        "agent_repo": AsyncMock(),
        "persona_repo": AsyncMock(),
    }


@pytest.fixture
def mock_settings():
    """Create mock verification and execution settings."""
    verification = MagicMock()
    verification.livekit_url = "wss://test.livekit.cloud"
    verification.livekit_api_key = "key"
    verification.livekit_api_secret = "secret"
    verification.sip_outbound_trunk_id = "trunk"
    verification.verification_call_timeout = 30

    execution = MagicMock()
    execution.audio_storage_provider = "s3"
    execution.audio_storage_path = "test-bucket"
    execution.audio_s3_region = "us-east-1"
    execution.audio_s3_access_key = "test-access-key"
    execution.audio_s3_secret = "test-secret-key"

    return {"verification": verification, "execution": execution}


@pytest.fixture
def service(mock_repos, mock_settings):
    """Create ScenarioCallService with mocked dependencies."""
    return ScenarioCallService(
        execution_repo=mock_repos["execution_repo"],
        scenario_repo=mock_repos["scenario_repo"],
        suite_repo=mock_repos["suite_repo"],
        suite_run_repo=mock_repos["suite_run_repo"],
        agent_repo=mock_repos["agent_repo"],
        persona_repo=mock_repos["persona_repo"],
        verification_settings=mock_settings["verification"],
        execution_settings=mock_settings["execution"],
    )


class TestScenarioCallServiceRunScenario:
    """Tests for ScenarioCallService.run_scenario."""

    @pytest.mark.asyncio
    async def test_returns_false_when_execution_not_found(self, service, mock_repos):
        """Test that run_scenario returns False when execution is not found."""
        mock_repos["execution_repo"].get_by_id.return_value = None

        result = await service.run_scenario(uuid4())

        assert result is False
        mock_repos["execution_repo"].get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_marks_failed_when_scenario_not_found(self, service, mock_repos):
        """Test that run_scenario marks failed when scenario is not found."""
        execution = _make_execution()
        mock_repos["execution_repo"].get_by_id.return_value = execution
        mock_repos["scenario_repo"].get.return_value = None

        result = await service.run_scenario(execution.id)

        assert result is False
        mock_repos["execution_repo"].update.assert_called_once()
        call_args = mock_repos["execution_repo"].update.call_args[0]
        assert call_args[2]["status"] == "failed"
        assert "Scenario not found" in call_args[2]["error_message"]

    @pytest.mark.asyncio
    async def test_marks_failed_when_agent_not_phone(self, service, mock_repos):
        """Test that run_scenario marks failed when agent type is not phone."""
        org_id = uuid4()
        execution = _make_execution(org_id=org_id)
        scenario = _make_scenario(org_id=org_id, suite_id=uuid4())
        suite = _make_suite(org_id=org_id, agent_id=uuid4())
        agent = _make_agent(org_id=org_id, agent_type="web", phone_number="")

        mock_repos["execution_repo"].get_by_id.return_value = execution
        mock_repos["scenario_repo"].get.return_value = scenario
        mock_repos["suite_repo"].get.return_value = suite
        mock_repos["agent_repo"].get.return_value = agent

        result = await service.run_scenario(execution.id)

        assert result is False
        update_call = mock_repos["execution_repo"].update.call_args_list[-1]
        assert update_call[0][2]["status"] == "failed"
        assert "not supported" in update_call[0][2]["error_message"]

    @pytest.mark.asyncio
    async def test_marks_failed_when_agent_has_no_phone_number(self, service, mock_repos):
        """Test that run_scenario marks failed when agent has no phone number."""
        org_id = uuid4()
        execution = _make_execution(org_id=org_id)
        scenario = _make_scenario(org_id=org_id, suite_id=uuid4())
        suite = _make_suite(org_id=org_id, agent_id=uuid4())
        agent = _make_agent(org_id=org_id, agent_type="phone", phone_number="")

        mock_repos["execution_repo"].get_by_id.return_value = execution
        mock_repos["scenario_repo"].get.return_value = scenario
        mock_repos["suite_repo"].get.return_value = suite
        mock_repos["agent_repo"].get.return_value = agent

        result = await service.run_scenario(execution.id)

        assert result is False
        update_call = mock_repos["execution_repo"].update.call_args_list[-1]
        assert update_call[0][2]["status"] == "failed"
        assert "phone number" in update_call[0][2]["error_message"]

    @pytest.mark.asyncio
    async def test_success_updates_execution_with_transcript_and_audio(
        self, service, mock_repos, mock_settings
    ):
        """Test that successful run updates execution with transcript, audio_url, status."""
        org_id = uuid4()
        execution = _make_execution(org_id=org_id)
        scenario = _make_scenario(org_id=org_id, suite_id=uuid4())
        suite = _make_suite(org_id=org_id, agent_id=uuid4())
        agent = _make_agent(org_id=org_id)
        persona = _make_persona(org_id=org_id)

        mock_repos["execution_repo"].get_by_id.return_value = execution
        mock_repos["scenario_repo"].get.return_value = scenario
        mock_repos["suite_repo"].get.return_value = suite
        mock_repos["agent_repo"].get.return_value = agent
        mock_repos["persona_repo"].get.return_value = persona

        @asynccontextmanager
        async def mock_run(*args, **kwargs):
            mock_room = MagicMock()
            mock_session = MagicMock()
            mock_session.start = AsyncMock()

            async def capture_conv(room, session, room_name):
                # Simulate conversation_item_added
                event = MagicMock()
                event.item.text_content = "Hello"
                event.item.role = "user"
                for handler in getattr(session.on, "_handlers", []):
                    pass  # Would need to invoke handler
                await session.start()

            yield (mock_room, mock_session, "exec-123")
            # Simulate that transcript was collected
            pass

        with (
            patch(
                "voiceobs.server.services.execution.scenario_call_service.run_livekit_sip_call",
                return_value=mock_run(),
            ),
            patch(
                "voiceobs.server.services.execution.scenario_call_service.api.LiveKitAPI"
            ) as mock_api_class,
            patch(
                "voiceobs.server.services.execution.scenario_call_service.asyncio.sleep",
                new_callable=AsyncMock,
            ),
        ):
            mock_api = MagicMock()
            mock_api.egress.start_room_composite_egress = AsyncMock()
            mock_api.egress.stop_egress = AsyncMock()
            mock_api.egress.list_egress = AsyncMock()
            list_resp = MagicMock()
            list_resp.items = []
            mock_api.egress.list_egress.return_value = list_resp
            mock_api.aclose = AsyncMock()
            mock_api_class.return_value = mock_api

            result = await service.run_scenario(execution.id)

        assert result is True
        # Should have updated to evaluating
        update_calls = [c for c in mock_repos["execution_repo"].update.call_args_list]
        evaluating_call = next(
            (c for c in update_calls if c[0][2].get("status") == "evaluating"), None
        )
        assert evaluating_call is not None
        assert evaluating_call[0][2]["transcript"] is not None
        assert "audio_url" in evaluating_call[0][2]
        assert evaluating_call[0][2]["duration_seconds"] is not None

    @pytest.mark.asyncio
    async def test_marks_failed_on_sip_exception(self, service, mock_repos):
        """Test that run_scenario marks failed when run_livekit_sip_call raises."""
        org_id = uuid4()
        execution = _make_execution(org_id=org_id)
        scenario = _make_scenario(org_id=org_id, suite_id=uuid4())
        suite = _make_suite(org_id=org_id, agent_id=uuid4())
        agent = _make_agent(org_id=org_id)
        persona = _make_persona(org_id=org_id)

        mock_repos["execution_repo"].get_by_id.return_value = execution
        mock_repos["scenario_repo"].get.return_value = scenario
        mock_repos["suite_repo"].get.return_value = suite
        mock_repos["agent_repo"].get.return_value = agent
        mock_repos["persona_repo"].get.return_value = persona

        with patch(
            "voiceobs.server.services.execution.scenario_call_service.run_livekit_sip_call"
        ) as mock_run:
            mock_run.side_effect = Exception("SIP connection failed")

            result = await service.run_scenario(execution.id)

        assert result is False
        update_call = mock_repos["execution_repo"].update.call_args_list[-1]
        assert update_call[0][2]["status"] == "failed"
        assert "SIP connection failed" in update_call[0][2]["error_message"]


class TestBuildScenarioSystemPrompt:
    """Tests for _build_scenario_system_prompt (via ScenarioCallService)."""

    @pytest.mark.asyncio
    async def test_prompt_includes_goal_traits_behaviors(self, service, mock_repos):
        """Test that the system prompt includes goal, traits, and behaviors."""
        prompt = service._build_scenario_system_prompt(
            goal="Book a flight to NYC",
            persona_traits=["assertive", "patient"],
            caller_behaviors=["ask for price", "confirm dates"],
            persona_description="Business traveler",
        )

        assert "Book a flight to NYC" in prompt
        assert "assertive" in prompt
        assert "patient" in prompt
        assert "ask for price" in prompt
        assert "confirm dates" in prompt
        assert "Business traveler" in prompt
        assert "3–6 turns" in prompt
