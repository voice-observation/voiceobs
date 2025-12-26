"""Type definitions for the evaluation module."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal


@dataclass
class EvalInput:
    """Input for semantic evaluation of a voice turn.

    Represents a single turn in a voice conversation that needs
    to be evaluated for intent correctness and relevance.

    Attributes:
        user_transcript: What the user said (ASR output).
        agent_response: What the agent responded with.
        expected_intent: Optional expected intent for stricter evaluation.
        conversation_context: Optional prior conversation context.
        conversation_id: Optional conversation identifier for tracking.
        turn_id: Optional turn identifier for tracking.
    """

    user_transcript: str
    agent_response: str
    expected_intent: str | None = None
    conversation_context: str | None = None
    conversation_id: str | None = None
    turn_id: str | None = None

    def content_hash(self) -> str:
        """Generate a hash of the evaluation input for caching.

        Returns:
            A SHA-256 hash of the input content.
        """
        content = json.dumps(
            {
                "user_transcript": self.user_transcript,
                "agent_response": self.agent_response,
                "expected_intent": self.expected_intent,
                "conversation_context": self.conversation_context,
            },
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class EvalResult:
    """Result of semantic evaluation.

    Attributes:
        intent_correct: Whether the agent correctly understood the user's intent.
        relevance_score: How relevant the response was (0.0 to 1.0).
        explanation: Brief explanation of the evaluation.
        conversation_id: Conversation identifier (from input).
        turn_id: Turn identifier (from input).
        content_hash: Hash of the input that was evaluated.
        cached: Whether this result was retrieved from cache.
    """

    intent_correct: bool
    relevance_score: float
    explanation: str
    conversation_id: str | None = None
    turn_id: str | None = None
    content_hash: str | None = None
    cached: bool = False

    def to_dict(self) -> dict:
        """Convert result to a dictionary."""
        return {
            "intent_correct": self.intent_correct,
            "relevance_score": self.relevance_score,
            "explanation": self.explanation,
            "conversation_id": self.conversation_id,
            "turn_id": self.turn_id,
            "content_hash": self.content_hash,
            "cached": self.cached,
        }

    @property
    def passed(self) -> bool:
        """Check if the evaluation passed (intent correct and relevance >= 0.5)."""
        return self.intent_correct and self.relevance_score >= 0.5


# LLM provider types
LLMProvider = Literal["gemini", "openai", "anthropic"]


@dataclass
class EvalConfig:
    """Configuration for the semantic evaluator.

    Attributes:
        provider: The LLM provider to use ("gemini", "openai", "anthropic").
        model: The model name to use. Defaults vary by provider.
        temperature: Sampling temperature (0.0 for deterministic).
        cache_enabled: Whether to cache evaluation results.
        cache_dir: Directory for cache storage. Defaults to .voiceobs_cache.
        api_key: Optional API key (otherwise uses environment variables).
    """

    provider: LLMProvider = "gemini"
    model: str | None = None
    temperature: float = 0.0
    cache_enabled: bool = True
    cache_dir: str = ".voiceobs_cache"
    api_key: str | None = None

    def get_model(self) -> str:
        """Get the model name, using defaults if not specified."""
        if self.model:
            return self.model

        # Default models by provider
        defaults = {
            "gemini": "gemini-2.0-flash",
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-haiku-latest",
        }
        return defaults.get(self.provider, "gemini-2.0-flash")
