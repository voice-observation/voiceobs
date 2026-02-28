"""Evaluation service for LLM-based test result evaluation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from voiceobs.server.models import EvaluationResult
from voiceobs.server.prompts.evaluation import (
    EVALUATION_PROMPT_TEMPLATE,
    STRICTNESS_GUIDANCE,
)

if TYPE_CHECKING:
    from voiceobs.server.db.repositories.test_execution import TestExecutionRepository
    from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository
    from voiceobs.server.db.repositories.test_suite import TestSuiteRepository
    from voiceobs.server.services.llm import LLMService

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for LLM-based evaluation of test execution results.

    Fetches execution transcript, scenario context, and suite strictness,
    then calls the LLM to produce a structured EvaluationResult.
    """

    def __init__(
        self,
        execution_repo: TestExecutionRepository,
        scenario_repo: TestScenarioRepository,
        suite_repo: TestSuiteRepository,
        llm_service: LLMService,
    ) -> None:
        """Initialize the evaluation service.

        Args:
            execution_repo: Repository for test executions.
            scenario_repo: Repository for test scenarios.
            suite_repo: Repository for test suites.
            llm_service: LLM service for structured evaluation output.
        """
        self._execution_repo = execution_repo
        self._scenario_repo = scenario_repo
        self._suite_repo = suite_repo
        self._llm_service = llm_service

    def _format_transcript(self, transcript: list[dict]) -> str:
        """Format transcript for the evaluation prompt."""
        lines: list[str] = []
        for entry in transcript:
            if not isinstance(entry, dict):
                continue
            role = entry.get("role", "unknown")
            text = entry.get("text", "")
            ts = entry.get("timestamp_ms", 0)
            lines.append(f"[{ts}ms] {role}: {text}")
        return "\n".join(lines)

    def _build_evaluation_prompt(
        self,
        transcript: str,
        scenario_goal: str,
        scenario_intent: str | None,
        caller_behaviors: list[str],
        evaluation_strictness: str,
    ) -> str:
        """Build the evaluation prompt with transcript and success criteria."""
        guidance = STRICTNESS_GUIDANCE.get(
            evaluation_strictness.lower(), STRICTNESS_GUIDANCE["balanced"]
        )

        intent_section = ""
        if scenario_intent:
            intent_section = f"\n- Expected intent: {scenario_intent}"

        behaviors_section = ""
        if caller_behaviors:
            behaviors_section = f"\n- Caller behaviors to consider: {', '.join(caller_behaviors)}"

        return EVALUATION_PROMPT_TEMPLATE.format(
            transcript=transcript,
            scenario_goal=scenario_goal,
            intent_section=intent_section,
            behaviors_section=behaviors_section,
            guidance=guidance,
        )

    async def evaluate(self, execution_id: UUID) -> EvaluationResult:
        """Evaluate a test execution using the transcript and scenario context.

        Args:
            execution_id: The test execution UUID.

        Returns:
            The LLM-generated EvaluationResult.

        Raises:
            ValueError: If execution, scenario, or suite not found, or if
                execution has no transcript.
        """
        execution = await self._execution_repo.get_by_id(execution_id)
        if execution is None:
            raise ValueError(f"Execution {execution_id} not found")

        if not execution.transcript or len(execution.transcript) == 0:
            raise ValueError(f"No transcript for execution {execution_id}")

        scenario = await self._scenario_repo.get(execution.scenario_id, execution.org_id)
        if scenario is None:
            raise ValueError(f"Scenario {execution.scenario_id} not found")

        suite = await self._suite_repo.get(scenario.suite_id, execution.org_id)
        if suite is None:
            raise ValueError(f"Test suite {scenario.suite_id} not found")

        transcript_str = self._format_transcript(execution.transcript)
        prompt = self._build_evaluation_prompt(
            transcript=transcript_str,
            scenario_goal=scenario.goal,
            scenario_intent=scenario.intent,
            caller_behaviors=scenario.caller_behaviors or [],
            evaluation_strictness=suite.evaluation_strictness or "balanced",
        )

        logger.debug("Evaluating execution %s", execution_id)
        result = await self._llm_service.generate_structured(
            prompt=prompt,
            output_schema=EvaluationResult,
            temperature=0.3,  # Lower temperature for consistent evaluation
        )
        return result
