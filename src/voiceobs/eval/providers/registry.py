"""Provider registry for managing LLM providers."""

from __future__ import annotations

from voiceobs.eval.providers.base import LLMProvider


class ProviderRegistry:
    """Registry for LLM providers.

    Supports dynamic registration of new providers at runtime.

    Example:
        # Register a custom provider
        from voiceobs.eval.providers import get_registry

        registry = get_registry()
        registry.register(MyCustomProvider())

        # Get a provider
        provider = registry.get("my_custom")
        llm = provider.create_llm(config)
    """

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}

    def register(self, provider: LLMProvider) -> None:
        """Register a provider.

        Args:
            provider: The provider instance to register.
        """
        self._providers[provider.name] = provider

    def get(self, name: str) -> LLMProvider:
        """Get a provider by name.

        Args:
            name: The provider name.

        Returns:
            The provider instance.

        Raises:
            ValueError: If the provider is not registered.
        """
        if name not in self._providers:
            available = ", ".join(sorted(self._providers.keys()))
            raise ValueError(f"Unknown provider: {name}. Available providers: {available}")
        return self._providers[name]

    def list_providers(self) -> list[str]:
        """List all registered provider names.

        Returns:
            Sorted list of provider names.
        """
        return sorted(self._providers.keys())

    def is_registered(self, name: str) -> bool:
        """Check if a provider is registered.

        Args:
            name: The provider name.

        Returns:
            True if the provider is registered.
        """
        return name in self._providers


# Default registry instance - lazily populated
_default_registry: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    """Get the default provider registry.

    The registry is lazily initialized with built-in providers
    on first access.

    Returns:
        The default ProviderRegistry instance.
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = ProviderRegistry()
        _register_builtin_providers(_default_registry)
    return _default_registry


def _register_builtin_providers(registry: ProviderRegistry) -> None:
    """Register the built-in providers."""
    from voiceobs.eval.providers.anthropic import AnthropicProvider
    from voiceobs.eval.providers.gemini import GeminiProvider
    from voiceobs.eval.providers.openai import OpenAIProvider

    registry.register(GeminiProvider())
    registry.register(OpenAIProvider())
    registry.register(AnthropicProvider())
