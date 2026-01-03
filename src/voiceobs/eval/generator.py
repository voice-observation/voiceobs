"""Scenario generator for creating diverse test scenarios from agent descriptions.

This module provides LLM-based scenario generation for testing voice AI agents.
It uses langchain for LLM abstraction and structured output for reliable JSON responses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from voiceobs.eval.prompts import build_discovery_prompt
from voiceobs.eval.providers import get_provider
from voiceobs.eval.types import EvalConfig

if TYPE_CHECKING:
    pass


class Persona(BaseModel):
    """User persona traits for a scenario.

    Attributes:
        name: User's name (e.g., "John", "Sarah").
        gender: User's gender (e.g., "male", "female", "non-binary", "prefer not to say").
        age: User's age (integer, typically 18-100).
        aggression: How aggressive/frustrated the user is (0.0 = calm, 1.0 = very aggressive).
        patience: How patient the user is (0.0 = impatient, 1.0 = very patient).
        verbosity: How verbose/detailed the user speaks (0.0 = brief, 1.0 = very detailed).
    """

    name: str = Field(description="User's name")
    gender: str = Field(description="User's gender")
    age: int = Field(ge=0, description="User's age")
    aggression: float = Field(ge=0.0, le=1.0, description="Aggression level from 0.0 to 1.0")
    patience: float = Field(ge=0.0, le=1.0, description="Patience level from 0.0 to 1.0")
    verbosity: float = Field(ge=0.0, le=1.0, description="Verbosity level from 0.0 to 1.0")


class Scenario(BaseModel):
    """A single test scenario.

    Attributes:
        name: Descriptive name for the scenario.
        goal: The user's primary objective in this scenario.
        persona: User personality traits.
        edge_cases: List of edge cases this scenario tests (e.g., "barge_in", "silence").
    """

    name: str = Field(description="Descriptive name for the scenario")
    goal: str = Field(description="The user's primary objective in this scenario")
    persona: Persona = Field(description="User personality traits")
    edge_cases: list[str] = Field(
        default_factory=list,
        description="List of edge cases this scenario tests",
    )


class ScenarioOutput(BaseModel):
    """Structured output schema for LLM scenario generation response.

    Attributes:
        scenarios: List of generated scenarios.
    """

    scenarios: list[Scenario] = Field(description="List of generated scenarios")


def _build_prompt(agent_description: str, count: int) -> str:
    """Build the scenario generation prompt.

    Args:
        agent_description: One-sentence description of the agent.
        count: Number of scenarios to generate.

    Returns:
        The formatted prompt string.
    """
    return build_discovery_prompt(agent_description, count)


class ScenarioGenerator:
    """LLM-based scenario generator for voice AI agents.

    Uses langchain's structured output for reliable JSON responses
    and the provider factory pattern for LLM abstraction.

    Example:
        generator = ScenarioGenerator()
        scenarios = generator.generate_scenarios(
            "A customer service bot for scheduling doctor appointments",
            count=5
        )
        for scenario in scenarios:
            print(f"Scenario: {scenario['name']}")
            print(f"Goal: {scenario['goal']}")
            print(f"Edge cases: {scenario['edge_cases']}")

    Example with custom provider:
        config = EvalConfig(provider="openai", model="gpt-4o", temperature=0.7)
        generator = ScenarioGenerator(config)
    """

    def __init__(self, config: EvalConfig | None = None) -> None:
        """Initialize the scenario generator.

        Args:
            config: Evaluation configuration. Uses defaults if not provided.
        """
        self.config = config or EvalConfig()
        self._structured_llm = None

    def _get_structured_llm(self):
        """Get or create the structured LLM instance."""
        if self._structured_llm is None:
            provider = get_provider(self.config.provider)
            base_llm = provider.create_llm(self.config)
            # Use langchain's with_structured_output for reliable JSON
            self._structured_llm = base_llm.with_structured_output(ScenarioOutput)
        return self._structured_llm

    def generate_scenarios(self, agent_description: str, count: int = 5) -> list[dict[str, any]]:
        """Generate diverse test scenarios from an agent description.

        Args:
            agent_description: One-sentence description of the agent to test.
            count: Number of scenarios to generate (default: 5).

        Returns:
            List of scenario dictionaries, each containing:
            - name: Scenario name
            - goal: User's objective
            - persona: Dict with "name", "gender", "age", "aggression", "patience", and "verbosity"
            - edge_cases: List of edge case strings

        Raises:
            ImportError: If langchain dependencies are not installed.
            ValueError: If the LLM response cannot be parsed.
        """
        # Build prompt and call LLM with structured output
        prompt = _build_prompt(agent_description, count)
        structured_llm = self._get_structured_llm()

        output: ScenarioOutput = structured_llm.invoke(prompt)

        # Convert Pydantic models to dictionaries
        scenarios = []
        for scenario in output.scenarios:
            scenarios.append(
                {
                    "name": scenario.name,
                    "goal": scenario.goal,
                    "persona": {
                        "name": scenario.persona.name,
                        "gender": scenario.persona.gender,
                        "age": scenario.persona.age,
                        "aggression": scenario.persona.aggression,
                        "patience": scenario.persona.patience,
                        "verbosity": scenario.persona.verbosity,
                    },
                    "edge_cases": scenario.edge_cases,
                }
            )

        return scenarios
