"""Tests for the ScenarioGenerationService."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from voiceobs.server.db.models import AgentRow, PersonaRow, TestScenarioRow, TestSuiteRow
from voiceobs.server.services.scenario_generation import (
    GeneratedScenario,
    GeneratedScenariosResponse,
    ScenarioGenerationService,
)


def make_agent(
    name: str = "Test Agent",
    goal: str = "Help customers",
    context: str | None = "E-commerce support",
    supported_intents: list[str] | None = None,
) -> AgentRow:
    """Create an AgentRow for testing."""
    return AgentRow(
        id=uuid4(),
        name=name,
        goal=goal,
        agent_type="phone",
        contact_info={"phone_number": "+1234567890"},
        supported_intents=supported_intents or ["check_order", "cancel_order"],
        context=context,
    )


def make_test_suite(
    agent_id=None,
    name: str = "Test Suite",
    thoroughness: int = 1,
    test_scopes: list[str] | None = None,
    edge_cases: list[str] | None = None,
    status: str = "pending",
) -> TestSuiteRow:
    """Create a TestSuiteRow for testing."""
    return TestSuiteRow(
        id=uuid4(),
        name=name,
        agent_id=agent_id,
        thoroughness=thoroughness,
        test_scopes=test_scopes or ["core_flows"],
        edge_cases=edge_cases or [],
        status=status,
    )


def make_persona(
    name: str = "Default Persona",
    traits: list[str] | None = None,
    is_default: bool = False,
) -> PersonaRow:
    """Create a PersonaRow for testing."""
    return PersonaRow(
        id=uuid4(),
        name=name,
        aggression=0.5,
        patience=0.5,
        verbosity=0.5,
        tts_provider="deepgram",
        traits=traits or [],
        is_default=is_default,
    )


def make_scenario(
    suite_id,
    name: str = "Existing Scenario",
    goal: str = "Test existing flow",
) -> TestScenarioRow:
    """Create a TestScenarioRow for testing."""
    return TestScenarioRow(
        id=uuid4(),
        suite_id=suite_id,
        name=name,
        goal=goal,
        persona_id=uuid4(),
    )


class TestScenarioCountGuidance:
    """Tests for _get_scenario_count_guidance method."""

    def test_thoroughness_0_returns_3_to_5(self):
        """Light thoroughness (0) should suggest 3-5 scenarios."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        result = service._get_scenario_count_guidance(0)
        assert result == "3-5"

    def test_thoroughness_1_returns_5_to_10(self):
        """Standard thoroughness (1) should suggest 5-10 scenarios."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        result = service._get_scenario_count_guidance(1)
        assert result == "5-10"

    def test_thoroughness_2_returns_10_to_20(self):
        """Exhaustive thoroughness (2) should suggest 10-20 scenarios."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        result = service._get_scenario_count_guidance(2)
        assert result == "10-20"

    def test_invalid_thoroughness_defaults_to_5_to_10(self):
        """Invalid thoroughness values should default to standard (5-10)."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        result = service._get_scenario_count_guidance(99)
        assert result == "5-10"


class TestBuildGenerationPrompt:
    """Tests for _build_generation_prompt method."""

    def test_prompt_includes_agent_name_and_goal(self):
        """Prompt should include the agent's name and goal."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        agent = make_agent(name="Order Support Bot", goal="Help with order inquiries")
        suite = make_test_suite()

        prompt = service._build_generation_prompt(agent, suite, [], None)

        assert "Order Support Bot" in prompt
        assert "Help with order inquiries" in prompt

    def test_prompt_includes_agent_context(self):
        """Prompt should include the agent's context when available."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        agent = make_agent(context="E-commerce platform for electronics")
        suite = make_test_suite()

        prompt = service._build_generation_prompt(agent, suite, [], None)

        assert "E-commerce platform for electronics" in prompt

    def test_prompt_includes_supported_intents(self):
        """Prompt should include the agent's supported intents."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        agent = make_agent(supported_intents=["check_order", "cancel_order", "return_item"])
        suite = make_test_suite()

        prompt = service._build_generation_prompt(agent, suite, [], None)

        assert "check_order" in prompt
        assert "cancel_order" in prompt
        assert "return_item" in prompt

    def test_prompt_includes_test_scopes(self):
        """Prompt should include the test suite's test scopes."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        agent = make_agent()
        suite = make_test_suite(test_scopes=["core_flows", "edge_cases", "error_handling"])

        prompt = service._build_generation_prompt(agent, suite, [], None)

        assert "core_flows" in prompt
        assert "edge_cases" in prompt
        assert "error_handling" in prompt

    def test_prompt_includes_edge_cases(self):
        """Prompt should include the test suite's edge cases."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        agent = make_agent()
        suite = make_test_suite(edge_cases=["invalid_input", "timeout", "network_error"])

        prompt = service._build_generation_prompt(agent, suite, [], None)

        assert "invalid_input" in prompt
        assert "timeout" in prompt
        assert "network_error" in prompt

    def test_prompt_includes_existing_scenarios_to_avoid_duplicates(self):
        """Prompt should list existing scenarios to avoid duplicates."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        agent = make_agent()
        suite = make_test_suite()
        existing = [
            make_scenario(suite.id, name="Check order status", goal="Verify order lookup"),
            make_scenario(suite.id, name="Cancel pending order", goal="Test cancellation"),
        ]

        prompt = service._build_generation_prompt(agent, suite, existing, None)

        assert "Check order status" in prompt
        assert "Cancel pending order" in prompt

    def test_prompt_includes_additional_prompt(self):
        """Prompt should include additional user-provided prompt."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        agent = make_agent()
        suite = make_test_suite()

        prompt = service._build_generation_prompt(agent, suite, [], "Focus on angry customers")

        assert "Focus on angry customers" in prompt

    def test_prompt_includes_scenario_count_guidance(self):
        """Prompt should include scenario count guidance based on thoroughness."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        agent = make_agent()
        suite = make_test_suite(thoroughness=2)  # Exhaustive

        prompt = service._build_generation_prompt(agent, suite, [], None)

        assert "10-20" in prompt

    def test_prompt_includes_trait_vocabulary(self):
        """Prompt should include the available trait vocabulary."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        agent = make_agent()
        suite = make_test_suite()

        prompt = service._build_generation_prompt(agent, suite, [], None)

        # Check that vocabulary section exists
        assert "Available Persona Traits" in prompt
        # Check some traits are included
        assert "angry" in prompt
        assert "impatient" in prompt
        assert "cooperative" in prompt
        # Check instruction to use only these traits
        assert "ONLY" in prompt or "only" in prompt

    def test_prompt_includes_all_trait_categories(self):
        """Prompt should include traits from all categories."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )
        agent = make_agent()
        suite = make_test_suite()

        prompt = service._build_generation_prompt(agent, suite, [], None)

        # Check categories are mentioned
        assert "emotional_state" in prompt
        assert "communication_style" in prompt
        assert "patience_level" in prompt
        assert "cooperation" in prompt
        assert "expertise" in prompt


class TestGenerateScenarios:
    """Tests for generate_scenarios method."""

    @pytest.mark.asyncio
    async def test_generates_scenarios_and_matches_personas(self):
        """Test that scenarios are generated and matched to personas."""
        agent = make_agent()
        suite = make_test_suite(agent_id=agent.id)
        persona = make_persona(traits=["impatient"], is_default=True)

        # Mock dependencies
        llm_service = AsyncMock()
        llm_service.generate_structured.return_value = GeneratedScenariosResponse(
            scenarios=[
                GeneratedScenario(
                    name="Test Scenario",
                    goal="Test goal",
                    intent="check_order",
                    persona_traits=["impatient"],
                    max_turns=10,
                )
            ]
        )

        test_suite_repo = AsyncMock()
        test_suite_repo.get.return_value = suite

        test_scenario_repo = AsyncMock()
        test_scenario_repo.list_all.return_value = []
        test_scenario_repo.create.return_value = make_scenario(suite.id)

        persona_repo = AsyncMock()
        persona_repo.list_all.return_value = [persona]

        agent_repo = AsyncMock()
        agent_repo.get.return_value = agent

        service = ScenarioGenerationService(
            llm_service=llm_service,
            test_suite_repo=test_suite_repo,
            test_scenario_repo=test_scenario_repo,
            persona_repo=persona_repo,
            agent_repo=agent_repo,
        )

        scenarios = await service.generate_scenarios(suite.id)

        # Verify LLM was called
        llm_service.generate_structured.assert_called_once()
        # Verify scenario was created
        test_scenario_repo.create.assert_called_once()
        # Verify returned scenarios
        assert len(scenarios) == 1

    @pytest.mark.asyncio
    async def test_raises_value_error_if_suite_not_found(self):
        """Test that ValueError is raised if test suite not found."""
        test_suite_repo = AsyncMock()
        test_suite_repo.get.return_value = None

        service = ScenarioGenerationService(
            llm_service=AsyncMock(),
            test_suite_repo=test_suite_repo,
            test_scenario_repo=AsyncMock(),
            persona_repo=AsyncMock(),
            agent_repo=AsyncMock(),
        )

        with pytest.raises(ValueError, match="Test suite .* not found"):
            await service.generate_scenarios(uuid4())

    @pytest.mark.asyncio
    async def test_raises_value_error_if_suite_has_no_agent(self):
        """Test that ValueError is raised if test suite has no agent assigned."""
        suite = make_test_suite(agent_id=None)

        test_suite_repo = AsyncMock()
        test_suite_repo.get.return_value = suite

        service = ScenarioGenerationService(
            llm_service=AsyncMock(),
            test_suite_repo=test_suite_repo,
            test_scenario_repo=AsyncMock(),
            persona_repo=AsyncMock(),
            agent_repo=AsyncMock(),
        )

        with pytest.raises(ValueError, match="has no agent assigned"):
            await service.generate_scenarios(suite.id)

    @pytest.mark.asyncio
    async def test_raises_value_error_if_agent_not_found(self):
        """Test that ValueError is raised if agent not found."""
        suite = make_test_suite(agent_id=uuid4())

        test_suite_repo = AsyncMock()
        test_suite_repo.get.return_value = suite

        agent_repo = AsyncMock()
        agent_repo.get.return_value = None

        service = ScenarioGenerationService(
            llm_service=AsyncMock(),
            test_suite_repo=test_suite_repo,
            test_scenario_repo=AsyncMock(),
            persona_repo=AsyncMock(),
            agent_repo=agent_repo,
        )

        with pytest.raises(ValueError, match="Agent .* not found"):
            await service.generate_scenarios(suite.id)

    @pytest.mark.asyncio
    async def test_raises_value_error_if_no_personas_available(self):
        """Test that ValueError is raised if no personas are available."""
        agent = make_agent()
        suite = make_test_suite(agent_id=agent.id)

        test_suite_repo = AsyncMock()
        test_suite_repo.get.return_value = suite

        agent_repo = AsyncMock()
        agent_repo.get.return_value = agent

        persona_repo = AsyncMock()
        persona_repo.list_all.return_value = []

        service = ScenarioGenerationService(
            llm_service=AsyncMock(),
            test_suite_repo=test_suite_repo,
            test_scenario_repo=AsyncMock(),
            persona_repo=persona_repo,
            agent_repo=agent_repo,
        )

        with pytest.raises(ValueError, match="No active personas available"):
            await service.generate_scenarios(suite.id)

    @pytest.mark.asyncio
    async def test_calculates_timeout_from_max_turns(self):
        """Test that timeout is calculated as max_turns * 60 seconds."""
        agent = make_agent()
        suite = make_test_suite(agent_id=agent.id)
        persona = make_persona(is_default=True)

        llm_service = AsyncMock()
        llm_service.generate_structured.return_value = GeneratedScenariosResponse(
            scenarios=[
                GeneratedScenario(
                    name="Test",
                    goal="Test goal",
                    intent="test",
                    persona_traits=[],
                    max_turns=15,
                )
            ]
        )

        test_suite_repo = AsyncMock()
        test_suite_repo.get.return_value = suite

        test_scenario_repo = AsyncMock()
        test_scenario_repo.list_all.return_value = []
        test_scenario_repo.create.return_value = make_scenario(suite.id)

        persona_repo = AsyncMock()
        persona_repo.list_all.return_value = [persona]

        agent_repo = AsyncMock()
        agent_repo.get.return_value = agent

        service = ScenarioGenerationService(
            llm_service=llm_service,
            test_suite_repo=test_suite_repo,
            test_scenario_repo=test_scenario_repo,
            persona_repo=persona_repo,
            agent_repo=agent_repo,
        )

        await service.generate_scenarios(suite.id)

        # Verify scenario was created with correct timeout
        call_kwargs = test_scenario_repo.create.call_args.kwargs
        assert call_kwargs["timeout"] == 15 * 60  # max_turns * 60


class TestGenerateScenariosBackground:
    """Tests for generate_scenarios_background method."""

    @pytest.mark.asyncio
    async def test_updates_status_to_ready_on_success(self):
        """Test that status is updated to ready after successful generation."""
        agent = make_agent()
        suite = make_test_suite(agent_id=agent.id, status="generating")
        persona = make_persona(is_default=True)

        llm_service = AsyncMock()
        llm_service.generate_structured.return_value = GeneratedScenariosResponse(
            scenarios=[
                GeneratedScenario(
                    name="Test",
                    goal="Test goal",
                    intent="test",
                    persona_traits=[],
                    max_turns=10,
                )
            ]
        )

        test_suite_repo = AsyncMock()
        test_suite_repo.get.return_value = suite
        test_suite_repo.update.return_value = suite

        test_scenario_repo = AsyncMock()
        test_scenario_repo.list_all.return_value = []
        test_scenario_repo.create.return_value = make_scenario(suite.id)

        persona_repo = AsyncMock()
        persona_repo.list_all.return_value = [persona]

        agent_repo = AsyncMock()
        agent_repo.get.return_value = agent

        service = ScenarioGenerationService(
            llm_service=llm_service,
            test_suite_repo=test_suite_repo,
            test_scenario_repo=test_scenario_repo,
            persona_repo=persona_repo,
            agent_repo=agent_repo,
        )

        await service.generate_scenarios_background(suite.id)

        # Verify status was updated to ready
        test_suite_repo.update.assert_called()
        final_update = test_suite_repo.update.call_args
        assert final_update.kwargs["updates"]["status"] == "ready"

    @pytest.mark.asyncio
    async def test_updates_status_to_generation_failed_on_error(self):
        """Test that status is updated to generation_failed on error."""
        agent = make_agent()
        suite = make_test_suite(agent_id=agent.id, status="generating")

        test_suite_repo = AsyncMock()
        test_suite_repo.get.return_value = suite
        test_suite_repo.update.return_value = suite

        agent_repo = AsyncMock()
        agent_repo.get.return_value = agent

        persona_repo = AsyncMock()
        persona_repo.list_all.return_value = []  # This will cause an error

        service = ScenarioGenerationService(
            llm_service=AsyncMock(),
            test_suite_repo=test_suite_repo,
            test_scenario_repo=AsyncMock(),
            persona_repo=persona_repo,
            agent_repo=agent_repo,
        )

        await service.generate_scenarios_background(suite.id)

        # Verify status was updated to generation_failed
        test_suite_repo.update.assert_called()
        final_update = test_suite_repo.update.call_args
        assert final_update.kwargs["updates"]["status"] == "generation_failed"
        assert "generation_error" in final_update.kwargs["updates"]


class TestStartBackgroundGeneration:
    """Tests for start_background_generation method."""

    @pytest.mark.asyncio
    async def test_creates_asyncio_task(self):
        """Test that start_background_generation creates an asyncio task."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )

        suite_id = uuid4()
        with patch("asyncio.create_task") as mock_create_task:
            service.start_background_generation(suite_id)
            mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_additional_prompt_to_background_task(self):
        """Test that additional_prompt is passed to background generation."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )

        suite_id = uuid4()
        additional_prompt = "Focus on edge cases"

        with patch("asyncio.create_task") as mock_create_task:
            service.start_background_generation(suite_id, additional_prompt)
            mock_create_task.assert_called_once()


class TestSanitizeTraits:
    """Tests for _sanitize_traits method."""

    def test_filters_out_invalid_traits(self):
        """Test that invalid traits are removed."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )

        result = service._sanitize_traits(["angry", "invalid_trait", "calm"])

        assert result == ["angry", "calm"]

    def test_preserves_valid_traits(self):
        """Test that all valid traits are preserved."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )

        result = service._sanitize_traits(["angry", "impatient", "demanding"])

        assert result == ["angry", "impatient", "demanding"]

    def test_handles_empty_list(self):
        """Test that empty list returns empty list."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )

        result = service._sanitize_traits([])

        assert result == []

    def test_case_insensitive_matching(self):
        """Test that trait matching is case insensitive."""
        service = ScenarioGenerationService(
            llm_service=MagicMock(),
            test_suite_repo=MagicMock(),
            test_scenario_repo=MagicMock(),
            persona_repo=MagicMock(),
            agent_repo=MagicMock(),
        )

        result = service._sanitize_traits(["ANGRY", "Calm", "IMPATIENT"])

        assert result == ["ANGRY", "Calm", "IMPATIENT"]


class TestGenerateScenariosTraitSanitization:
    """Tests for trait sanitization during scenario generation."""

    @pytest.mark.asyncio
    async def test_sanitizes_llm_generated_traits(self):
        """Test that invalid traits from LLM are filtered out before matching."""
        agent = make_agent()
        suite = make_test_suite(agent_id=agent.id)
        persona = make_persona(traits=["angry", "impatient"], is_default=True)

        # LLM returns some invalid traits
        llm_service = AsyncMock()
        llm_service.generate_structured.return_value = GeneratedScenariosResponse(
            scenarios=[
                GeneratedScenario(
                    name="Test Scenario",
                    goal="Test goal",
                    intent="check_order",
                    persona_traits=["angry", "made_up_trait", "impatient"],
                    max_turns=10,
                )
            ]
        )

        test_suite_repo = AsyncMock()
        test_suite_repo.get.return_value = suite

        test_scenario_repo = AsyncMock()
        test_scenario_repo.list_all.return_value = []
        test_scenario_repo.create.return_value = make_scenario(suite.id)

        persona_repo = AsyncMock()
        persona_repo.list_all.return_value = [persona]

        agent_repo = AsyncMock()
        agent_repo.get.return_value = agent

        service = ScenarioGenerationService(
            llm_service=llm_service,
            test_suite_repo=test_suite_repo,
            test_scenario_repo=test_scenario_repo,
            persona_repo=persona_repo,
            agent_repo=agent_repo,
        )

        await service.generate_scenarios(suite.id)

        # Verify scenario was created with sanitized traits (without made_up_trait)
        call_kwargs = test_scenario_repo.create.call_args.kwargs
        assert "made_up_trait" not in call_kwargs["persona_traits"]
        assert "angry" in call_kwargs["persona_traits"]
        assert "impatient" in call_kwargs["persona_traits"]
