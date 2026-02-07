"""Tests for scenario generation schemas."""

import pytest

from voiceobs.server.services.scenario_generation.schemas import (
    GeneratedScenario,
    GeneratedScenariosResponse,
)


class TestScenarioGenerationSchemas:
    """Tests for the scenario generation Pydantic schemas."""

    def test_generated_scenario_creation(self):
        """Test creating GeneratedScenario."""
        scenario = GeneratedScenario(
            name="Order Status Check",
            goal="User wants to check the status of their recent order",
            intent="check_order_status",
            persona_traits=["impatient", "direct"],
            max_turns=10,
        )

        assert scenario.name == "Order Status Check"
        assert scenario.goal == "User wants to check the status of their recent order"
        assert scenario.intent == "check_order_status"
        assert scenario.persona_traits == ["impatient", "direct"]
        assert scenario.max_turns == 10

    def test_generated_scenarios_response_creation(self):
        """Test creating GeneratedScenariosResponse."""
        response = GeneratedScenariosResponse(
            scenarios=[
                GeneratedScenario(
                    name="Order Status Check",
                    goal="User wants to check order status",
                    intent="check_order_status",
                    persona_traits=["impatient"],
                    max_turns=10,
                ),
                GeneratedScenario(
                    name="Place New Order",
                    goal="User wants to place a new order",
                    intent="place_order",
                    persona_traits=["friendly", "detailed"],
                    max_turns=15,
                ),
            ]
        )

        assert len(response.scenarios) == 2
        assert response.scenarios[0].intent == "check_order_status"
        assert response.scenarios[1].intent == "place_order"

    def test_generated_scenario_default_max_turns(self):
        """Test that max_turns defaults to 10."""
        scenario = GeneratedScenario(
            name="Test Scenario",
            goal="Test goal",
            intent="test_intent",
        )
        assert scenario.max_turns == 10

    def test_generated_scenario_default_persona_traits(self):
        """Test that persona_traits defaults to empty list."""
        scenario = GeneratedScenario(
            name="Test Scenario",
            goal="Test goal",
            intent="test_intent",
        )
        assert scenario.persona_traits == []

    def test_generated_scenario_max_turns_validation_min(self):
        """Test that max_turns must be at least 1."""
        with pytest.raises(ValueError):
            GeneratedScenario(
                name="Test Scenario",
                goal="Test goal",
                intent="test_intent",
                max_turns=0,
            )

    def test_generated_scenario_max_turns_validation_max(self):
        """Test that max_turns cannot exceed 50."""
        with pytest.raises(ValueError):
            GeneratedScenario(
                name="Test Scenario",
                goal="Test goal",
                intent="test_intent",
                max_turns=51,
            )

    def test_generated_scenario_max_turns_boundary_values(self):
        """Test boundary values for max_turns (1 and 50)."""
        scenario_min = GeneratedScenario(
            name="Test Scenario",
            goal="Test goal",
            intent="test_intent",
            max_turns=1,
        )
        assert scenario_min.max_turns == 1

        scenario_max = GeneratedScenario(
            name="Test Scenario",
            goal="Test goal",
            intent="test_intent",
            max_turns=50,
        )
        assert scenario_max.max_turns == 50

    def test_generated_scenarios_response_empty_list(self):
        """Test creating response with empty scenarios list."""
        response = GeneratedScenariosResponse(scenarios=[])
        assert response.scenarios == []
        assert len(response.scenarios) == 0
