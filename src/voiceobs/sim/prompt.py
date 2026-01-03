"""Meta-prompt generator for combining Persona and Scenario."""

from __future__ import annotations

from typing import Literal

from voiceobs.sim.persona import PersonaDNA

GoalStatus = Literal["not_started", "in_progress", "achieved", "failed"]


class Scenario:
    """Represents a conversation scenario with goal and context."""

    def __init__(self, goal: str, context: str | None = None) -> None:
        """Initialize Scenario with goal and optional context.

        Args:
            goal: The goal to achieve in the conversation
            context: Optional context about the situation
        """
        self.goal = goal
        self.context = context


class ConversationState:
    """Tracks stateful conversation information."""

    def __init__(
        self,
        turn_count: int = 0,
        goal_status: GoalStatus = "not_started",
    ) -> None:
        """Initialize ConversationState.

        Args:
            turn_count: Current number of turns in conversation
            goal_status: Current status of the goal
        """
        self.turn_count = turn_count
        self.goal_status = goal_status

    def increment_turn(self) -> None:
        """Increment the turn count."""
        self.turn_count += 1

    def update_goal_status(self, status: GoalStatus) -> None:
        """Update the goal status.

        Args:
            status: New goal status

        Raises:
            ValueError: If status is not a valid GoalStatus
        """
        valid_statuses: list[GoalStatus] = ["not_started", "in_progress", "achieved", "failed"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid goal_status: {status}. Must be one of {valid_statuses}")
        self.goal_status = status


def generate_system_prompt(
    persona: PersonaDNA,
    scenario: Scenario,
    state: ConversationState | None = None,
) -> str:
    """Generate system prompt from Persona + Scenario.

    Args:
        persona: PersonaDNA instance with personality traits
        scenario: Scenario instance with goal and context
        state: Optional ConversationState for current conversation state

    Returns:
        Complete system prompt string
    """
    parts = []

    # Persona section
    parts.append("You are a caller with these traits:")
    parts.append(persona.get_personality_directives())
    parts.append("")

    # Scenario section
    parts.append(f"Goal: {scenario.goal}")
    if scenario.context:
        parts.append(f"Context: {scenario.context}")
    parts.append("")

    # Goal tracking instructions
    parts.append("Track your progress toward the goal. Update your goal status as you progress:")
    parts.append("- not_started: Goal hasn't been addressed yet")
    parts.append("- in_progress: Working toward the goal")
    parts.append("- achieved: Goal has been successfully completed")
    parts.append("- failed: Goal cannot be achieved")
    parts.append("")

    # Turn-taking behavior rules
    if persona.aggression >= 0.7:
        parts.append("If the agent is slow or unhelpful, interrupt them.")
    elif persona.patience <= 0.3:
        parts.append("If responses are slow, express your impatience.")
    else:
        parts.append("Wait for the agent to finish speaking before responding.")

    # State information if provided
    if state:
        parts.append("")
        parts.append("Current conversation state:")
        parts.append(f"- Turn count: {state.turn_count}")
        parts.append(f"- Goal status: {state.goal_status}")

    return "\n".join(parts)
