"""Tests for voiceobs persona system."""

from __future__ import annotations

import pytest

from voiceobs.sim.persona import PersonaDNA
from voiceobs.sim.prompt import ConversationState, Scenario, generate_system_prompt


class TestPersonaDNA:
    """Tests for PersonaDNA class."""

    def test_create_persona_with_valid_traits(self) -> None:
        """Test creating a persona with valid trait values."""
        persona = PersonaDNA(
            aggression=0.7,
            patience=0.3,
            verbosity=0.8,
            traits=["impatient", "direct"],
        )
        assert persona.aggression == 0.7
        assert persona.patience == 0.3
        assert persona.verbosity == 0.8
        assert persona.traits == ["impatient", "direct"]

    def test_create_persona_with_default_traits(self) -> None:
        """Test creating a persona with default empty traits."""
        persona = PersonaDNA(aggression=0.5, patience=0.5, verbosity=0.5)
        assert persona.traits == []

    def test_aggression_below_zero_raises_error(self) -> None:
        """Test that aggression below 0 raises ValueError."""
        with pytest.raises(ValueError, match="aggression must be between 0 and 1"):
            PersonaDNA(aggression=-0.1, patience=0.5, verbosity=0.5)

    def test_aggression_above_one_raises_error(self) -> None:
        """Test that aggression above 1 raises ValueError."""
        with pytest.raises(ValueError, match="aggression must be between 0 and 1"):
            PersonaDNA(aggression=1.1, patience=0.5, verbosity=0.5)

    def test_patience_below_zero_raises_error(self) -> None:
        """Test that patience below 0 raises ValueError."""
        with pytest.raises(ValueError, match="patience must be between 0 and 1"):
            PersonaDNA(aggression=0.5, patience=-0.1, verbosity=0.5)

    def test_patience_above_one_raises_error(self) -> None:
        """Test that patience above 1 raises ValueError."""
        with pytest.raises(ValueError, match="patience must be between 0 and 1"):
            PersonaDNA(aggression=0.5, patience=1.1, verbosity=0.5)

    def test_verbosity_below_zero_raises_error(self) -> None:
        """Test that verbosity below 0 raises ValueError."""
        with pytest.raises(ValueError, match="verbosity must be between 0 and 1"):
            PersonaDNA(aggression=0.5, patience=0.5, verbosity=-0.1)

    def test_verbosity_above_one_raises_error(self) -> None:
        """Test that verbosity above 1 raises ValueError."""
        with pytest.raises(ValueError, match="verbosity must be between 0 and 1"):
            PersonaDNA(aggression=0.5, patience=0.5, verbosity=1.1)

    def test_get_personality_directives_high_aggression(self) -> None:
        """Test personality directives for high aggression."""
        persona = PersonaDNA(aggression=0.8, patience=0.5, verbosity=0.5)
        directives = persona.get_personality_directives()
        assert "High aggression" in directives or "aggression" in directives.lower()
        assert "0.8" in directives

    def test_get_personality_directives_low_patience(self) -> None:
        """Test personality directives for low patience."""
        persona = PersonaDNA(aggression=0.5, patience=0.2, verbosity=0.5)
        directives = persona.get_personality_directives()
        assert "Low patience" in directives or "patience" in directives.lower()
        assert "0.2" in directives

    def test_get_personality_directives_high_verbosity(self) -> None:
        """Test personality directives for high verbosity."""
        persona = PersonaDNA(aggression=0.5, patience=0.5, verbosity=0.9)
        directives = persona.get_personality_directives()
        assert "High verbosity" in directives or "verbosity" in directives.lower()
        assert "0.9" in directives

    def test_get_personality_directives_includes_traits(self) -> None:
        """Test that personality directives include custom traits."""
        persona = PersonaDNA(
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["impatient", "direct"],
        )
        directives = persona.get_personality_directives()
        assert "impatient" in directives or "direct" in directives

    def test_get_personality_directives_low_aggression(self) -> None:
        """Test personality directives for low aggression."""
        persona = PersonaDNA(aggression=0.2, patience=0.5, verbosity=0.5)
        directives = persona.get_personality_directives()
        assert "Low aggression" in directives
        assert "0.2" in directives

    def test_get_personality_directives_high_patience(self) -> None:
        """Test personality directives for high patience."""
        persona = PersonaDNA(aggression=0.5, patience=0.8, verbosity=0.5)
        directives = persona.get_personality_directives()
        assert "High patience" in directives
        assert "0.8" in directives

    def test_get_personality_directives_low_verbosity(self) -> None:
        """Test personality directives for low verbosity."""
        persona = PersonaDNA(aggression=0.5, patience=0.5, verbosity=0.2)
        directives = persona.get_personality_directives()
        assert "Low verbosity" in directives
        assert "0.2" in directives


class TestScenario:
    """Tests for Scenario class."""

    def test_create_scenario_with_goal_and_context(self) -> None:
        """Test creating a scenario with goal and context."""
        scenario = Scenario(
            goal="Schedule a doctor's appointment",
            context="User needs urgent care",
        )
        assert scenario.goal == "Schedule a doctor's appointment"
        assert scenario.context == "User needs urgent care"

    def test_create_scenario_with_optional_context(self) -> None:
        """Test creating a scenario without context."""
        scenario = Scenario(goal="Schedule a doctor's appointment")
        assert scenario.goal == "Schedule a doctor's appointment"
        assert scenario.context is None


class TestConversationState:
    """Tests for ConversationState class."""

    def test_create_state_with_defaults(self) -> None:
        """Test creating conversation state with defaults."""
        state = ConversationState()
        assert state.turn_count == 0
        assert state.goal_status == "not_started"

    def test_create_state_with_values(self) -> None:
        """Test creating conversation state with specific values."""
        state = ConversationState(turn_count=5, goal_status="in_progress")
        assert state.turn_count == 5
        assert state.goal_status == "in_progress"

    def test_increment_turn_count(self) -> None:
        """Test incrementing turn count."""
        state = ConversationState()
        state.increment_turn()
        assert state.turn_count == 1
        state.increment_turn()
        assert state.turn_count == 2

    def test_update_goal_status(self) -> None:
        """Test updating goal status."""
        state = ConversationState()
        state.update_goal_status("in_progress")
        assert state.goal_status == "in_progress"
        state.update_goal_status("achieved")
        assert state.goal_status == "achieved"

    def test_invalid_goal_status_raises_error(self) -> None:
        """Test that invalid goal status raises ValueError."""
        state = ConversationState()
        with pytest.raises(ValueError, match="Invalid goal_status"):
            state.update_goal_status("invalid_status")


class TestGenerateSystemPrompt:
    """Tests for generate_system_prompt function."""

    def test_generate_prompt_with_persona_and_scenario(self) -> None:
        """Test generating system prompt from persona and scenario."""
        persona = PersonaDNA(
            aggression=0.7,
            patience=0.3,
            verbosity=0.8,
            traits=["impatient", "direct"],
        )
        scenario = Scenario(
            goal="Schedule a doctor's appointment",
            context="User needs urgent care",
        )
        prompt = generate_system_prompt(persona, scenario)
        assert "aggression" in prompt.lower() or "0.7" in prompt
        assert "patience" in prompt.lower() or "0.3" in prompt
        assert "verbosity" in prompt.lower() or "0.8" in prompt
        assert "Schedule a doctor's appointment" in prompt
        assert "User needs urgent care" in prompt

    def test_generate_prompt_includes_goal_tracking(self) -> None:
        """Test that generated prompt includes goal tracking instructions."""
        persona = PersonaDNA(aggression=0.5, patience=0.5, verbosity=0.5)
        scenario = Scenario(goal="Test goal")
        prompt = generate_system_prompt(persona, scenario)
        assert "goal" in prompt.lower() or "track" in prompt.lower()

    def test_generate_prompt_includes_turn_taking(self) -> None:
        """Test that generated prompt includes turn-taking behavior rules."""
        persona = PersonaDNA(aggression=0.5, patience=0.5, verbosity=0.5)
        scenario = Scenario(goal="Test goal")
        prompt = generate_system_prompt(persona, scenario)
        assert "turn" in prompt.lower() or "interrupt" in prompt.lower()

    def test_generate_prompt_with_state(self) -> None:
        """Test generating prompt with conversation state."""
        persona = PersonaDNA(aggression=0.5, patience=0.5, verbosity=0.5)
        scenario = Scenario(goal="Test goal")
        state = ConversationState(turn_count=3, goal_status="in_progress")
        prompt = generate_system_prompt(persona, scenario, state)
        assert "3" in prompt or "in_progress" in prompt.lower()

    def test_generate_prompt_with_high_patience(self) -> None:
        """Test generating prompt with high patience (else branch)."""
        persona = PersonaDNA(aggression=0.5, patience=0.5, verbosity=0.5)
        scenario = Scenario(goal="Test goal")
        prompt = generate_system_prompt(persona, scenario)
        assert "Wait for the agent" in prompt or "finish speaking" in prompt

    def test_generate_prompt_with_low_patience_but_low_aggression(self) -> None:
        """Test generating prompt with low patience but low aggression (elif branch)."""
        persona = PersonaDNA(aggression=0.5, patience=0.2, verbosity=0.5)
        scenario = Scenario(goal="Test goal")
        prompt = generate_system_prompt(persona, scenario)
        assert "express your impatience" in prompt.lower() or "slow" in prompt.lower()
