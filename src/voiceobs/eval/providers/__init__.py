"""LLM providers for the semantic evaluator.

This module provides a factory pattern for LLM providers, making it
easy to add new providers without modifying existing code.

Built-in providers:
- gemini: Google Gemini (default)
- openai: OpenAI GPT models
- anthropic: Anthropic Claude models

Example:
    # Use a built-in provider
    from voiceobs.eval.providers import get_provider

    provider = get_provider("gemini")
    llm = provider.create_llm(config)

    # Register a custom provider
    from voiceobs.eval.providers import register_provider, LLMProvider

    class MyProvider(LLMProvider):
        @property
        def name(self) -> str:
            return "my_provider"

        @property
        def default_model(self) -> str:
            return "my-model"

        def create_llm(self, config):
            ...

    register_provider(MyProvider())
"""

from voiceobs.eval.providers.base import LLMProvider
from voiceobs.eval.providers.registry import ProviderRegistry, get_registry


def get_provider(name: str) -> LLMProvider:
    """Get a provider from the default registry.

    Args:
        name: The provider name (e.g., "gemini", "openai", "anthropic").

    Returns:
        The provider instance.

    Raises:
        ValueError: If the provider is not registered.
    """
    return get_registry().get(name)


def register_provider(provider: LLMProvider) -> None:
    """Register a provider in the default registry.

    Args:
        provider: The provider instance to register.
    """
    get_registry().register(provider)


def list_providers() -> list[str]:
    """List all available provider names.

    Returns:
        Sorted list of provider names.
    """
    return get_registry().list_providers()


__all__ = [
    "LLMProvider",
    "ProviderRegistry",
    "get_provider",
    "get_registry",
    "list_providers",
    "register_provider",
]
