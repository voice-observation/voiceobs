"""Semantic evaluator using LLM-as-judge.

This module provides the core evaluation functionality using langchain
for LLM abstraction. Uses structured output for reliable JSON responses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from voiceobs.eval.providers import get_provider
from voiceobs.eval.types import EvalConfig, EvalInput, EvalResult

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


class EvalOutput(BaseModel):
    """Structured output schema for LLM evaluation response."""

    intent_correct: bool = Field(
        description="Whether the agent correctly understood the user's intent"
    )
    relevance_score: float = Field(
        description="How relevant the response was, from 0.0 to 1.0",
        ge=0.0,
        le=1.0,
    )
    explanation: str = Field(description="Brief explanation of the evaluation (1-2 sentences)")


# Evaluation prompt template
# fmt: off
EVAL_PROMPT = """You are an expert evaluator for voice AI conversations. \
Your task is to assess whether an AI agent's response correctly addresses \
the user's intent and is relevant to what they said.

## User's Input
{user_transcript}

{context_section}

## Agent's Response
{agent_response}

{expected_intent_section}

## Your Task
Evaluate the agent's response and provide:
1. **intent_correct**: Did the agent correctly understand what the user wanted? (true/false)
2. **relevance_score**: How relevant and helpful was the response? (0.0 to 1.0)
3. **explanation**: A brief explanation of your evaluation (1-2 sentences)"""
# fmt: on


def _build_prompt(eval_input: EvalInput) -> str:
    """Build the evaluation prompt from input.

    Args:
        eval_input: The evaluation input.

    Returns:
        The formatted prompt string.
    """
    # Build optional sections
    context_section = ""
    if eval_input.conversation_context:
        context_section = f"## Prior Context\n{eval_input.conversation_context}\n"

    expected_intent_section = ""
    if eval_input.expected_intent:
        expected_intent_section = (
            f"## Expected Intent\n"
            f"The user's expected intent was: {eval_input.expected_intent}\n"
            f"Evaluate whether the agent addressed this specific intent.\n"
        )

    return EVAL_PROMPT.format(
        user_transcript=eval_input.user_transcript,
        agent_response=eval_input.agent_response,
        context_section=context_section,
        expected_intent_section=expected_intent_section,
    )


class SemanticEvaluator:
    """LLM-based semantic evaluator for voice conversations.

    Uses langchain's structured output for reliable JSON responses
    and the provider factory pattern for LLM abstraction.

    Example:
        evaluator = SemanticEvaluator()
        result = evaluator.evaluate(EvalInput(
            user_transcript="What's the weather like?",
            agent_response="It's currently 72 degrees and sunny.",
        ))
        print(f"Intent correct: {result.intent_correct}")
        print(f"Relevance: {result.relevance_score}")

    Example with custom provider:
        config = EvalConfig(provider="openai", model="gpt-4o")
        evaluator = SemanticEvaluator(config)
    """

    def __init__(self, config: EvalConfig | None = None) -> None:
        """Initialize the evaluator.

        Args:
            config: Evaluation configuration. Uses defaults if not provided.
        """
        self.config = config or EvalConfig()
        self._llm: BaseChatModel | None = None
        self._structured_llm = None
        self._cache: dict[str, EvalResult] = {}

        # Initialize cache directory if caching is enabled
        if self.config.cache_enabled:
            self._cache_dir = Path(self.config.cache_dir)
            self._load_cache()

    def _load_cache(self) -> None:
        """Load cached results from disk."""
        if not self._cache_dir.exists():
            return

        cache_file = self._cache_dir / "eval_cache.json"
        if cache_file.exists():
            try:
                with cache_file.open() as f:
                    data = json.load(f)
                    for hash_key, result_data in data.items():
                        self._cache[hash_key] = EvalResult(
                            intent_correct=result_data["intent_correct"],
                            relevance_score=result_data["relevance_score"],
                            explanation=result_data["explanation"],
                            conversation_id=result_data.get("conversation_id"),
                            turn_id=result_data.get("turn_id"),
                            content_hash=hash_key,
                            cached=True,
                        )
            except (json.JSONDecodeError, KeyError):
                # Invalid cache file, start fresh
                self._cache = {}

    def _save_cache(self) -> None:
        """Save cached results to disk."""
        if not self.config.cache_enabled:
            return

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self._cache_dir / "eval_cache.json"

        data = {}
        for hash_key, result in self._cache.items():
            data[hash_key] = {
                "intent_correct": result.intent_correct,
                "relevance_score": result.relevance_score,
                "explanation": result.explanation,
                "conversation_id": result.conversation_id,
                "turn_id": result.turn_id,
            }

        with cache_file.open("w") as f:
            json.dump(data, f, indent=2)

    def _get_structured_llm(self):
        """Get or create the structured LLM instance."""
        if self._structured_llm is None:
            provider = get_provider(self.config.provider)
            base_llm = provider.create_llm(self.config)
            # Use langchain's with_structured_output for reliable JSON
            self._structured_llm = base_llm.with_structured_output(EvalOutput)
        return self._structured_llm

    def evaluate(self, eval_input: EvalInput) -> EvalResult:
        """Evaluate a single turn for semantic correctness.

        Args:
            eval_input: The evaluation input containing user transcript
                       and agent response.

        Returns:
            EvalResult with intent correctness and relevance score.

        Raises:
            ImportError: If langchain dependencies are not installed.
            ValueError: If the LLM response cannot be parsed.
        """
        # Check cache first
        content_hash = eval_input.content_hash()
        if self.config.cache_enabled and content_hash in self._cache:
            cached_result = self._cache[content_hash]
            # Update with current input's IDs
            return EvalResult(
                intent_correct=cached_result.intent_correct,
                relevance_score=cached_result.relevance_score,
                explanation=cached_result.explanation,
                conversation_id=eval_input.conversation_id,
                turn_id=eval_input.turn_id,
                content_hash=content_hash,
                cached=True,
            )

        # Build prompt and call LLM with structured output
        prompt = _build_prompt(eval_input)
        structured_llm = self._get_structured_llm()

        output: EvalOutput = structured_llm.invoke(prompt)

        result = EvalResult(
            intent_correct=output.intent_correct,
            relevance_score=output.relevance_score,
            explanation=output.explanation,
            conversation_id=eval_input.conversation_id,
            turn_id=eval_input.turn_id,
            content_hash=content_hash,
            cached=False,
        )

        # Cache the result
        if self.config.cache_enabled:
            self._cache[content_hash] = result
            self._save_cache()

        return result

    def evaluate_batch(self, inputs: list[EvalInput]) -> list[EvalResult]:
        """Evaluate multiple turns.

        Args:
            inputs: List of evaluation inputs.

        Returns:
            List of evaluation results in the same order.
        """
        return [self.evaluate(inp) for inp in inputs]

    def clear_cache(self) -> None:
        """Clear the evaluation cache."""
        self._cache = {}
        if self.config.cache_enabled:
            cache_file = self._cache_dir / "eval_cache.json"
            if cache_file.exists():
                cache_file.unlink()
