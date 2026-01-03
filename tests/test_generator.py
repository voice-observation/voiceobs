"""Tests for the scenario generator module."""

from unittest.mock import MagicMock, patch

import pytest

from voiceobs.eval.types import EvalConfig


class TestScenarioGenerator:
    """Tests for ScenarioGenerator class."""

    @pytest.fixture
    def mock_scenario_output(self):
        """Create a mock scenario output response."""
        from voiceobs.eval.generator import ScenarioOutput

        return ScenarioOutput(
            scenarios=[
                {
                    "name": "Urgent Appointment Request",
                    "goal": "Schedule appointment within 24 hours",
                    "persona": {
                        "name": "John",
                        "gender": "male",
                        "age": 45,
                        "aggression": 0.7,
                        "patience": 0.3,
                        "verbosity": 0.5,
                    },
                    "edge_cases": ["barge_in", "silence"],
                },
                {
                    "name": "Cancellation Request",
                    "goal": "Cancel existing appointment",
                    "persona": {
                        "name": "Sarah",
                        "gender": "female",
                        "age": 32,
                        "aggression": 0.5,
                        "patience": 0.6,
                        "verbosity": 0.4,
                    },
                    "edge_cases": ["interruption"],
                },
                {
                    "name": "Routine Checkup",
                    "goal": "Schedule annual checkup",
                    "persona": {
                        "name": "Mike",
                        "gender": "male",
                        "age": 28,
                        "aggression": 0.2,
                        "patience": 0.9,
                        "verbosity": 0.6,
                    },
                    "edge_cases": [],
                },
                {
                    "name": "Emergency Consultation",
                    "goal": "Get immediate medical advice",
                    "persona": {
                        "name": "Emma",
                        "gender": "female",
                        "age": 55,
                        "aggression": 0.9,
                        "patience": 0.1,
                        "verbosity": 0.8,
                    },
                    "edge_cases": ["barge_in", "stress"],
                },
                {
                    "name": "Reschedule Appointment",
                    "goal": "Change appointment time",
                    "persona": {
                        "name": "David",
                        "gender": "male",
                        "age": 38,
                        "aggression": 0.4,
                        "patience": 0.7,
                        "verbosity": 0.3,
                    },
                    "edge_cases": ["silence"],
                },
            ]
        )

    @pytest.fixture
    def mock_llm(self, mock_scenario_output):
        """Create a mock structured LLM."""
        mock = MagicMock()
        mock.invoke.return_value = mock_scenario_output
        return mock

    def test_generate_scenarios_returns_list(self, mock_llm, mock_scenario_output) -> None:
        """generate_scenarios should return list of scenarios from LLM response."""
        from voiceobs.eval.generator import ScenarioGenerator

        with patch("voiceobs.eval.generator.get_provider") as mock_get_provider:
            # Setup mock provider
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=False)
            generator = ScenarioGenerator(config)

            agent_description = "A customer service bot for scheduling doctor appointments"
            scenarios = generator.generate_scenarios(agent_description, count=5)

            assert len(scenarios) == 5
            assert scenarios[0]["name"] == "Urgent Appointment Request"
            assert scenarios[0]["goal"] == "Schedule appointment within 24 hours"
            assert "barge_in" in scenarios[0]["edge_cases"]
            assert scenarios[0]["persona"]["aggression"] == 0.7
            assert scenarios[0]["persona"]["name"] == "John"
            assert scenarios[0]["persona"]["gender"] == "male"
            assert scenarios[0]["persona"]["age"] == 45

    def test_generate_scenarios_includes_edge_cases(self, mock_llm) -> None:
        """generate_scenarios should ensure scenarios include edge cases."""
        from voiceobs.eval.generator import ScenarioGenerator, ScenarioOutput

        # Create output with edge cases
        mock_output = ScenarioOutput(
            scenarios=[
                {
                    "name": "Test Scenario",
                    "goal": "Test goal",
                    "persona": {
                        "name": "Test User",
                        "gender": "non-binary",
                        "age": 30,
                        "aggression": 0.5,
                        "patience": 0.5,
                        "verbosity": 0.5,
                    },
                    "edge_cases": ["barge_in", "silence", "stress"],
                }
            ]
        )
        mock_llm.invoke.return_value = mock_output

        with patch("voiceobs.eval.generator.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=False)
            generator = ScenarioGenerator(config)

            scenarios = generator.generate_scenarios("Test agent", count=1)

            assert len(scenarios) == 1
            edge_cases = scenarios[0]["edge_cases"]
            assert "barge_in" in edge_cases or "silence" in edge_cases or "stress" in edge_cases

    def test_generate_scenarios_with_custom_count(self, mock_llm) -> None:
        """generate_scenarios should generate requested number of scenarios."""
        from voiceobs.eval.generator import ScenarioGenerator, ScenarioOutput

        # Create output with 3 scenarios
        mock_output = ScenarioOutput(
            scenarios=[
                {
                    "name": f"Scenario {i}",
                    "goal": f"Goal {i}",
                    "persona": {
                        "name": f"User{i}",
                        "gender": "male",
                        "age": 30 + i,
                        "aggression": 0.5,
                        "patience": 0.5,
                        "verbosity": 0.5,
                    },
                    "edge_cases": [],
                }
                for i in range(3)
            ]
        )
        mock_llm.invoke.return_value = mock_output

        with patch("voiceobs.eval.generator.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=False)
            generator = ScenarioGenerator(config)

            scenarios = generator.generate_scenarios("Test agent", count=3)

            assert len(scenarios) == 3

    def test_generate_scenarios_validates_persona_values(self, mock_llm) -> None:
        """generate_scenarios should validate persona values are in range 0-1."""
        from voiceobs.eval.generator import ScenarioGenerator, ScenarioOutput

        mock_output = ScenarioOutput(
            scenarios=[
                {
                    "name": "Test",
                    "goal": "Test goal",
                    "persona": {
                        "name": "Test User",
                        "gender": "female",
                        "age": 35,
                        "aggression": 0.5,
                        "patience": 0.5,
                        "verbosity": 0.5,
                    },
                    "edge_cases": [],
                }
            ]
        )
        mock_llm.invoke.return_value = mock_output

        with patch("voiceobs.eval.generator.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=False)
            generator = ScenarioGenerator(config)

            scenarios = generator.generate_scenarios("Test agent", count=1)

            persona = scenarios[0]["persona"]
            assert 0.0 <= persona["aggression"] <= 1.0
            assert 0.0 <= persona["patience"] <= 1.0
            assert 0.0 <= persona["verbosity"] <= 1.0

    def test_generate_scenarios_uses_prompt_template(self, mock_llm) -> None:
        """generate_scenarios should use correct prompt template."""
        from voiceobs.eval.generator import ScenarioGenerator, ScenarioOutput

        mock_output = ScenarioOutput(scenarios=[])
        mock_llm.invoke.return_value = mock_output

        with patch("voiceobs.eval.generator.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=False)
            generator = ScenarioGenerator(config)

            agent_description = "A customer service bot for scheduling doctor appointments"
            generator.generate_scenarios(agent_description, count=5)

            # Verify prompt was called with agent description
            call_args = mock_llm.invoke.call_args[0][0]
            assert agent_description in call_args
            assert "5" in call_args or "five" in call_args.lower()

    def test_generate_scenarios_with_different_providers(self, mock_llm) -> None:
        """generate_scenarios should work with different LLM providers."""
        from voiceobs.eval.generator import ScenarioGenerator, ScenarioOutput

        mock_output = ScenarioOutput(
            scenarios=[
                {
                    "name": "Test",
                    "goal": "Test goal",
                    "persona": {
                        "name": "Test User",
                        "gender": "male",
                        "age": 40,
                        "aggression": 0.5,
                        "patience": 0.5,
                        "verbosity": 0.5,
                    },
                    "edge_cases": [],
                }
            ]
        )
        mock_llm.invoke.return_value = mock_output

        providers = ["gemini", "openai", "anthropic"]
        for provider_name in providers:
            with patch("voiceobs.eval.generator.get_provider") as mock_get_provider:
                mock_provider = MagicMock()
                mock_base_llm = MagicMock()
                mock_base_llm.with_structured_output.return_value = mock_llm
                mock_provider.create_llm.return_value = mock_base_llm
                mock_get_provider.return_value = mock_provider

                config = EvalConfig(provider=provider_name, cache_enabled=False)
                generator = ScenarioGenerator(config)

                scenarios = generator.generate_scenarios("Test agent", count=1)
                assert len(scenarios) == 1


class TestScenarioOutput:
    """Tests for ScenarioOutput Pydantic model."""

    def test_scenario_output_validates_structure(self) -> None:
        """ScenarioOutput should validate scenario structure."""
        from voiceobs.eval.generator import ScenarioOutput

        output = ScenarioOutput(
            scenarios=[
                {
                    "name": "Test Scenario",
                    "goal": "Test goal",
                    "persona": {
                        "name": "Alice",
                        "gender": "female",
                        "age": 28,
                        "aggression": 0.5,
                        "patience": 0.5,
                        "verbosity": 0.5,
                    },
                    "edge_cases": ["barge_in"],
                }
            ]
        )

        assert len(output.scenarios) == 1
        assert output.scenarios[0].name == "Test Scenario"

    def test_scenario_output_validates_persona_range(self) -> None:
        """ScenarioOutput should validate persona values are 0-1."""
        from pydantic import ValidationError

        from voiceobs.eval.generator import ScenarioOutput

        # Valid values
        output = ScenarioOutput(
            scenarios=[
                {
                    "name": "Test",
                    "goal": "Test goal",
                    "persona": {
                        "name": "Bob",
                        "gender": "male",
                        "age": 50,
                        "aggression": 0.0,
                        "patience": 1.0,
                        "verbosity": 0.5,
                    },
                    "edge_cases": [],
                }
            ]
        )
        assert output.scenarios[0].persona.aggression == 0.0
        assert output.scenarios[0].persona.patience == 1.0

        # Invalid values should raise ValidationError
        with pytest.raises(ValidationError):
            ScenarioOutput(
                scenarios=[
                    {
                        "name": "Test",
                        "goal": "Test goal",
                        "persona": {
                            "name": "Test",
                            "gender": "male",
                            "age": 30,
                            "aggression": 1.5,
                            "patience": 0.5,
                            "verbosity": 0.5,
                        },  # > 1.0
                        "edge_cases": [],
                    }
                ]
            )

        with pytest.raises(ValidationError):
            ScenarioOutput(
                scenarios=[
                    {
                        "name": "Test",
                        "goal": "Test goal",
                        "persona": {
                            "name": "Test",
                            "gender": "female",
                            "age": 25,
                            "aggression": -0.1,
                            "patience": 0.5,
                            "verbosity": 0.5,
                        },  # < 0.0
                        "edge_cases": [],
                    }
                ]
            )

    def test_scenario_output_allows_empty_edge_cases(self) -> None:
        """ScenarioOutput should allow empty edge_cases list."""
        from voiceobs.eval.generator import ScenarioOutput

        output = ScenarioOutput(
            scenarios=[
                {
                    "name": "Test",
                    "goal": "Test goal",
                    "persona": {
                        "name": "Charlie",
                        "gender": "non-binary",
                        "age": 22,
                        "aggression": 0.5,
                        "patience": 0.5,
                        "verbosity": 0.5,
                    },
                    "edge_cases": [],
                }
            ]
        )

        assert output.scenarios[0].edge_cases == []


class TestPromptBuilding:
    """Tests for prompt building."""

    def test_build_prompt_includes_agent_description(self) -> None:
        """Prompt should include agent description."""
        from voiceobs.eval.generator import _build_prompt

        agent_description = "A customer service bot for scheduling doctor appointments"
        prompt = _build_prompt(agent_description, count=5)

        assert agent_description in prompt

    def test_build_prompt_includes_count(self) -> None:
        """Prompt should include scenario count."""
        from voiceobs.eval.generator import _build_prompt

        prompt = _build_prompt("Test agent", count=5)
        assert "5" in prompt or "five" in prompt.lower()

        prompt = _build_prompt("Test agent", count=10)
        assert "10" in prompt or "ten" in prompt.lower()

    def test_build_prompt_includes_edge_case_requirements(self) -> None:
        """Prompt should include requirements for edge cases."""
        from voiceobs.eval.generator import _build_prompt

        prompt = _build_prompt("Test agent", count=5)

        # Should mention edge cases like barge-in, silence, stress
        assert "edge" in prompt.lower() or "barge" in prompt.lower() or "silence" in prompt.lower()

    def test_build_prompt_conditional_edge_case_requirements(self) -> None:
        """Prompt should adjust edge case requirements based on count."""
        from voiceobs.eval.generator import _build_prompt

        # For count >= 4, should require multiple edge cases
        prompt_5 = _build_prompt("Test agent", count=5)
        assert "at least 2 scenarios that test barge-in" in prompt_5
        assert "at least 1 scenario that tests silence" in prompt_5
        assert "at least 1 stress scenario" in prompt_5

        # For count == 3, should require fewer edge cases
        prompt_3 = _build_prompt("Test agent", count=3)
        assert "at least 1 scenario that tests barge-in" in prompt_3
        assert "at least 1 scenario that tests silence" in prompt_3
        assert "at least 2 scenarios that test barge-in" not in prompt_3

        # For count == 2, should require minimal edge cases
        prompt_2 = _build_prompt("Test agent", count=2)
        assert "at least 1 scenario that tests an edge case" in prompt_2

        # For count == 1, should have flexible requirements
        prompt_1 = _build_prompt("Test agent", count=1)
        assert "edge cases when appropriate" in prompt_1
