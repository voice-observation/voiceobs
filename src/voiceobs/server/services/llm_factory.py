"""Factory for creating LLM service instances."""

import os

from voiceobs.server.services.llm import LLMService


class LLMServiceFactory:
    """Factory for creating LLM service instances based on provider.

    This factory manages the registration and creation of LLM service providers.
    Providers can be registered dynamically using register_provider().

    Example:
        >>> LLMServiceFactory.register_provider("openai", OpenAILLMService)
        >>> service = LLMServiceFactory.create()
        >>> result = await service.generate_structured(prompt, OutputSchema)
    """

    _providers: dict[str, type[LLMService]] = {}

    @classmethod
    def create(cls, provider: str | None = None) -> LLMService:
        """Create an LLM service instance.

        Args:
            provider: Optional provider identifier. If not provided, auto-detects
                     based on available API keys (prefers OpenAI, then Gemini).

        Returns:
            LLMService instance for the specified or auto-detected provider

        Raises:
            ValueError: If provider is not supported or no API keys are found
        """
        if provider:
            provider_lower = provider.lower()
            service_class = cls._providers.get(provider_lower)

            if service_class is None:
                supported = ", ".join(cls._providers.keys())
                raise ValueError(
                    f"Unsupported LLM provider: {provider}. Supported providers: {supported}"
                )

            return service_class()

        # Auto-detect provider based on available API keys
        # Prefer OpenAI, then Gemini
        if os.getenv("OPENAI_API_KEY"):
            service_class = cls._providers.get("openai")
            if service_class:
                return service_class()

        if os.getenv("GOOGLE_API_KEY"):
            service_class = cls._providers.get("gemini")
            if service_class:
                return service_class()

        if os.getenv("ANTHROPIC_API_KEY"):
            service_class = cls._providers.get("anthropic")
            if service_class:
                return service_class()

        raise ValueError(
            "No LLM API key found. Set OPENAI_API_KEY, GOOGLE_API_KEY, "
            "or ANTHROPIC_API_KEY environment variable."
        )

    @classmethod
    def register_provider(cls, provider_id: str, service_class: type[LLMService]) -> None:
        """Register a new LLM provider.

        Args:
            provider_id: Unique identifier for the provider (case-insensitive)
            service_class: LLMService subclass implementation
        """
        cls._providers[provider_id.lower()] = service_class

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider IDs.

        Returns:
            List of registered provider identifiers
        """
        return list(cls._providers.keys())
