"""OpenAI LLM service implementation."""

import os
from typing import TypeVar

from pydantic import BaseModel

from voiceobs.server.services.llm import LLMService

# LLM imports
try:
    from voiceobs.eval.providers import get_provider
    from voiceobs.eval.types import EvalConfig

    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

T = TypeVar("T", bound=BaseModel)


class OpenAILLMService(LLMService):
    """OpenAI LLM provider implementation.

    Uses the OpenAI API via langchain for structured output generation.
    Requires OPENAI_API_KEY environment variable to be set.

    Example:
        >>> service = OpenAILLMService()
        >>> result = await service.generate_structured(prompt, OutputSchema, temperature=0.7)
    """

    def __init__(self) -> None:
        """Initialize OpenAI LLM service."""
        if not LLM_AVAILABLE:
            raise ValueError(
                "LLM dependencies not available. Install with: pip install langchain-openai"
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI LLM")

        self._api_key = api_key

    def _get_structured_llm(self, output_schema: type[BaseModel], temperature: float):
        """Get or create the structured LLM instance for a specific schema."""
        config = EvalConfig(
            provider="openai",
            temperature=temperature,
            api_key=self._api_key,
        )

        provider = get_provider(config.provider)
        base_llm = provider.create_llm(config)
        return base_llm.with_structured_output(output_schema)

    async def generate_structured(
        self, prompt: str, output_schema: type[T], temperature: float = 0.7
    ) -> T:
        """Generate structured output from a prompt using OpenAI.

        Args:
            prompt: The prompt text to send to the LLM
            output_schema: Pydantic model class for structured output
            temperature: Sampling temperature (0.0 = deterministic, higher = more creative)

        Returns:
            Instance of output_schema with LLM-generated data

        Raises:
            ValueError: If the LLM response cannot be parsed or API key is missing
            Exception: Provider-specific errors during generation
        """
        structured_llm = self._get_structured_llm(output_schema, temperature)
        # Note: langchain's invoke is synchronous, but we wrap it in async for consistency
        output: T = structured_llm.invoke(prompt)
        return output
