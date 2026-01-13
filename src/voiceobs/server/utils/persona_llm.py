"""LLM-based persona attribute generation utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from voiceobs.server.prompts.persona import PERSONA_ATTRIBUTES_PROMPT

# LLM service imports
try:
    from voiceobs.server.services.llm_factory import LLMServiceFactory

    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class PersonaAttributesOutput(BaseModel):
    """Structured output schema for LLM-generated persona attributes."""

    aggression: float = Field(
        description="Aggression level from 0.0 (passive) to 1.0 (assertive)",
        ge=0.0,
        le=1.0,
    )
    patience: float = Field(
        description="Patience level from 0.0 (impatient) to 1.0 (patient)",
        ge=0.0,
        le=1.0,
    )
    verbosity: float = Field(
        description="Verbosity level from 0.0 (concise) to 1.0 (verbose)",
        ge=0.0,
        le=1.0,
    )
    tts_provider: str = Field(
        description="Recommended TTS provider: 'openai', 'elevenlabs', or 'deepgram'"
    )
    tts_model_key: str = Field(
        description="Recommended TTS model key from the provider's available models"
    )


async def generate_persona_attributes_with_llm(
    name: str,
    description: str | None,
    models_path: Path,
) -> tuple[float, float, float, str, dict[str, Any]]:
    """Generate persona attributes using LLM based on name and description.

    Args:
        name: Persona name.
        description: Persona description.
        models_path: Path to the TTS provider models JSON file.

    Returns:
        Tuple of (aggression, patience, verbosity, tts_provider, tts_config).

    Raises:
        ValueError: If LLM is not available or generation fails.
    """
    if not LLM_AVAILABLE:
        raise ValueError(
            "LLM dependencies not available. Install with: "
            "pip install langchain-openai langchain-google-genai langchain-anthropic"
        )

    # Load available TTS models
    try:
        with open(models_path, encoding="utf-8") as f:
            models_data = json.load(f)
            available_models = models_data.get("models", {})
    except FileNotFoundError:
        raise ValueError(f"TTS models file not found at {models_path}")

    # Build prompt using template
    prompt = PERSONA_ATTRIBUTES_PROMPT.format(
        name=name,
        description=description or "No description provided",
        available_models=json.dumps(available_models, indent=2),
    )

    try:
        # Get LLM service (auto-detects provider based on available API keys)
        llm_service = LLMServiceFactory.create()

        # Generate structured output
        output: PersonaAttributesOutput = await llm_service.generate_structured(
            prompt=prompt,
            output_schema=PersonaAttributesOutput,
            temperature=0.7,  # Use some creativity
        )

        # Get the TTS config for the selected model
        tts_config = available_models.get(output.tts_provider, {}).get(output.tts_model_key, {})
        if not tts_config:
            # Fallback to first available model if selected model not found
            provider_models = available_models.get(output.tts_provider, {})
            if provider_models:
                first_model_key = list(provider_models.keys())[0]
                tts_config = provider_models[first_model_key]
            else:
                raise ValueError(f"No models available for provider: {output.tts_provider}")

        return (
            output.aggression,
            output.patience,
            output.verbosity,
            output.tts_provider,
            tts_config,
        )
    except Exception as e:
        raise ValueError(f"Failed to generate persona attributes with LLM: {str(e)}") from e
