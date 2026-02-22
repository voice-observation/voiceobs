"""Service for generating test scenarios using LLMs."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING
from uuid import UUID

from voiceobs.server.db.models import AgentRow, TestScenarioRow, TestSuiteRow
from voiceobs.server.services.scenario_generation.persona_matcher import PersonaMatcher
from voiceobs.server.services.scenario_generation.schemas import GeneratedScenariosResponse
from voiceobs.server.services.scenario_generation.trait_vocabulary import (
    ALL_TRAITS,
    TRAIT_VOCABULARY,
)

if TYPE_CHECKING:
    from voiceobs.server.db.repositories.agent import AgentRepository
    from voiceobs.server.db.repositories.persona import PersonaRepository
    from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository
    from voiceobs.server.db.repositories.test_suite import TestSuiteRepository
    from voiceobs.server.services.llm import LLMService

logger = logging.getLogger(__name__)


class ScenarioGenerationService:
    """Service for generating test scenarios using LLMs and matching to personas.

    This service orchestrates the generation of test scenarios by:
    1. Building a context-aware prompt from agent and suite configuration
    2. Calling the LLM to generate scenarios
    3. Matching generated scenarios to the best available personas
    4. Creating the scenarios in the database
    """

    def __init__(
        self,
        llm_service: LLMService,
        test_suite_repo: TestSuiteRepository,
        test_scenario_repo: TestScenarioRepository,
        persona_repo: PersonaRepository,
        agent_repo: AgentRepository,
    ) -> None:
        """Initialize the scenario generation service.

        Args:
            llm_service: LLM service for generating scenarios.
            test_suite_repo: Repository for test suite operations.
            test_scenario_repo: Repository for test scenario operations.
            persona_repo: Repository for persona operations.
            agent_repo: Repository for agent operations.
        """
        self._llm_service = llm_service
        self._test_suite_repo = test_suite_repo
        self._test_scenario_repo = test_scenario_repo
        self._persona_repo = persona_repo
        self._agent_repo = agent_repo

    def _sanitize_traits(self, traits: list[str]) -> list[str]:
        """Filter traits to only include valid vocabulary traits.

        Args:
            traits: List of trait strings from LLM output.

        Returns:
            List containing only traits that exist in ALL_TRAITS.
        """
        valid_set = {t.lower() for t in ALL_TRAITS}
        return [t for t in traits if t.lower() in valid_set]

    def _get_scenario_count_guidance(self, thoroughness: int) -> str:
        """Get scenario count guidance based on thoroughness level.

        Args:
            thoroughness: Thoroughness level (0=Light, 1=Standard, 2=Exhaustive).

        Returns:
            String describing the recommended number of scenarios.
        """
        guidance_map = {
            0: "3-5",  # Light
            1: "5-10",  # Standard
            2: "10-20",  # Exhaustive
        }
        return guidance_map.get(thoroughness, "5-10")

    def _build_generation_prompt(
        self,
        agent: AgentRow,
        suite: TestSuiteRow,
        existing_scenarios: list[TestScenarioRow],
        additional_prompt: str | None,
    ) -> str:
        """Build the prompt for LLM scenario generation.

        Args:
            agent: The agent to generate scenarios for.
            suite: The test suite configuration.
            existing_scenarios: List of existing scenarios to avoid duplicating.
            additional_prompt: Additional user-provided prompt guidance.

        Returns:
            The formatted prompt string for the LLM.
        """
        scenario_count = self._get_scenario_count_guidance(suite.thoroughness)

        # Build the base prompt
        prompt_parts = [
            "You are a test scenario generator for voice AI agents.",
            "",
            "## Agent Information",
            f"- **Name**: {agent.name}",
            f"- **Goal**: {agent.goal}",
        ]

        # Add context if available
        if agent.context:
            prompt_parts.append(f"- **Context**: {agent.context}")

        # Add supported intents
        if agent.supported_intents:
            intents_str = ", ".join(agent.supported_intents)
            prompt_parts.append(f"- **Supported Intents**: {intents_str}")

        # Add trait vocabulary
        traits_by_category = "\n".join(
            f"  - {category}: {', '.join(traits)}" for category, traits in TRAIT_VOCABULARY.items()
        )
        prompt_parts.extend(
            [
                "",
                "## Available Persona Traits",
                "Select 2-4 traits from this list ONLY:",
                traits_by_category,
                "",
                "Do NOT invent new traits. Use exact trait names from the list above.",
            ]
        )

        # Add test suite configuration
        prompt_parts.extend(
            [
                "",
                "## Test Suite Configuration",
            ]
        )

        if suite.test_scopes:
            scopes_str = ", ".join(suite.test_scopes)
            prompt_parts.append(f"- **Test Scopes**: {scopes_str}")

        if suite.edge_cases:
            edge_cases_str = ", ".join(suite.edge_cases)
            prompt_parts.append(f"- **Edge Cases to Cover**: {edge_cases_str}")

        prompt_parts.append(f"- **Scenario Count Guidance**: Generate {scenario_count} scenarios")

        # Add existing scenarios to avoid
        if existing_scenarios:
            prompt_parts.extend(
                [
                    "",
                    "## Existing Scenarios (do not duplicate)",
                ]
            )
            for scenario in existing_scenarios:
                prompt_parts.append(f"- {scenario.name}: {scenario.goal}")

        # Add additional prompt if provided
        if additional_prompt:
            prompt_parts.extend(
                [
                    "",
                    "## Additional Instructions",
                    additional_prompt,
                ]
            )

        # Add generation instructions
        prompt_parts.extend(
            [
                "",
                "## Instructions",
                "Generate realistic test scenarios that a caller might have when "
                "interacting with this agent.",
                "Each scenario should include:",
                "- A short, descriptive name",
                "- A clear goal describing what the caller is trying to accomplish",
                "- An intent that matches the agent's supported intents",
                "- Persona traits that would be ideal for testing this scenario",
                "- A suggested maximum number of conversation turns",
                "",
                "Create diverse scenarios that cover different user intents, "
                "personality types, and edge cases.",
            ]
        )

        return "\n".join(prompt_parts)

    async def generate_scenarios(
        self,
        suite_id: UUID,
        org_id: UUID,
        additional_prompt: str | None = None,
    ) -> list[TestScenarioRow]:
        """Generate test scenarios for a test suite.

        Args:
            suite_id: The test suite UUID.
            org_id: The organization UUID (suite and agent must belong to this org).
            additional_prompt: Additional prompt guidance for generation.

        Returns:
            List of created test scenario rows.

        Raises:
            ValueError: If test suite, agent, or personas not found.
        """
        suite = await self._test_suite_repo.get(suite_id, org_id)
        if suite is None:
            raise ValueError(f"Test suite {suite_id} not found")

        # Fetch the agent
        if suite.agent_id is None:
            raise ValueError(f"Test suite {suite_id} has no agent assigned")

        agent = await self._agent_repo.get(suite.agent_id, org_id)
        if agent is None:
            raise ValueError(f"Agent {suite.agent_id} not found")

        # Fetch active personas for the org
        personas = await self._persona_repo.list_all(org_id=org_id, is_active=True)
        if not personas:
            raise ValueError("No active personas available for scenario generation")

        # Fetch existing scenarios
        existing_scenarios = await self._test_scenario_repo.list_all(suite_id=suite_id)

        # Build the prompt
        prompt = self._build_generation_prompt(agent, suite, existing_scenarios, additional_prompt)
        logger.debug(f"generation prompt: {prompt}")

        # Generate scenarios using LLM
        response = await self._llm_service.generate_structured(
            prompt=prompt,
            output_schema=GeneratedScenariosResponse,
            temperature=0.8,  # Higher temperature for creative diversity
        )

        # Create persona matcher
        matcher = PersonaMatcher(personas)

        # Create scenarios in database
        created_scenarios: list[TestScenarioRow] = []
        for generated in response.scenarios:
            # Sanitize traits to only valid vocabulary
            sanitized_traits = self._sanitize_traits(generated.persona_traits)

            # Match to best persona
            match = matcher.find_best_match(sanitized_traits)

            # Calculate timeout from max_turns (1 minute per turn)
            timeout = generated.max_turns * 60

            # Create the scenario
            scenario = await self._test_scenario_repo.create(
                suite_id=suite_id,
                name=generated.name,
                goal=generated.goal,
                persona_id=match.persona.id,
                max_turns=generated.max_turns,
                timeout=timeout,
                intent=generated.intent,
                persona_traits=sanitized_traits,
                persona_match_score=match.score,
            )
            created_scenarios.append(scenario)

        return created_scenarios

    async def generate_scenarios_background(
        self,
        suite_id: UUID,
        org_id: UUID,
        additional_prompt: str | None = None,
    ) -> None:
        """Generate scenarios in the background, updating suite status.

        This method wraps generate_scenarios with status updates:
        - On success: status -> "ready"
        - On failure: status -> "generation_failed", generation_error set

        Args:
            suite_id: The test suite UUID.
            org_id: The organization UUID.
            additional_prompt: Additional prompt guidance for generation.
        """
        try:
            await self.generate_scenarios(suite_id, org_id, additional_prompt)

            # Update status to ready
            await self._test_suite_repo.update(
                suite_id,
                org_id,
                {"status": "ready", "generation_error": None},
            )
            logger.info(f"Successfully generated scenarios for suite {suite_id}")

        except Exception as e:
            # Update status to generation_failed
            error_message = str(e)
            await self._test_suite_repo.update(
                suite_id,
                org_id,
                {"status": "generation_failed", "generation_error": error_message},
            )
            logger.error(f"Failed to generate scenarios for suite {suite_id}: {error_message}")

    def start_background_generation(
        self,
        suite_id: UUID,
        org_id: UUID,
        additional_prompt: str | None = None,
    ) -> None:
        """Start scenario generation as a background asyncio task.

        Args:
            suite_id: The test suite UUID.
            org_id: The organization UUID.
            additional_prompt: Additional prompt guidance for generation.
        """
        asyncio.create_task(self.generate_scenarios_background(suite_id, org_id, additional_prompt))
