"""Prompt templates for server-side LLM operations."""

from voiceobs.server.prompts.evaluation import (
    EVALUATION_PROMPT_TEMPLATE,
    STRICTNESS_GUIDANCE,
)
from voiceobs.server.prompts.persona import PERSONA_ATTRIBUTES_PROMPT
from voiceobs.server.prompts.scenario_call import SCENARIO_CALL_SYSTEM_PROMPT

__all__ = [
    "EVALUATION_PROMPT_TEMPLATE",
    "PERSONA_ATTRIBUTES_PROMPT",
    "SCENARIO_CALL_SYSTEM_PROMPT",
    "STRICTNESS_GUIDANCE",
]
