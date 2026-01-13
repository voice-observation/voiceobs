"""LLM service abstraction for managing language model providers."""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMService(ABC):
    """Abstract base class for LLM providers.

    All LLM provider implementations must inherit from this class and implement
    the generate_structured method.
    """

    @abstractmethod
    async def generate_structured(
        self, prompt: str, output_schema: type[T], temperature: float = 0.7
    ) -> T:
        """Generate structured output from a prompt.

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
        pass
