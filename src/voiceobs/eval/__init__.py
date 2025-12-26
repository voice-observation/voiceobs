"""Semantic evaluation module for voice conversations.

This module provides LLM-as-judge evaluation for assessing the quality
of voice AI responses. It uses langchain for LLM abstraction, with
Google Gemini as the default provider.

Note: This module requires the 'eval' optional dependencies:
    pip install voiceobs[eval]

Example:
    from voiceobs.eval import SemanticEvaluator, EvalInput

    evaluator = SemanticEvaluator()
    result = evaluator.evaluate(EvalInput(
        user_transcript="What's the weather like?",
        agent_response="It's currently 72 degrees and sunny.",
    ))

    print(f"Intent correct: {result.intent_correct}")
    print(f"Relevance: {result.relevance_score}")
    print(f"Explanation: {result.explanation}")
"""

from voiceobs.eval.evaluator import SemanticEvaluator
from voiceobs.eval.types import (
    EvalConfig,
    EvalInput,
    EvalResult,
)

__all__ = [
    "EvalConfig",
    "EvalInput",
    "EvalResult",
    "SemanticEvaluator",
]
