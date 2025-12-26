"""Base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

    from voiceobs.eval.types import EvalConfig


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    To add a new provider, subclass this and implement the required methods,
    then register it with the ProviderRegistry.

    Example:
        class MyProvider(LLMProvider):
            @property
            def name(self) -> str:
                return "my_provider"

            @property
            def default_model(self) -> str:
                return "my-model-v1"

            def create_llm(self, config: EvalConfig) -> BaseChatModel:
                from my_langchain_package import MyChat
                return MyChat(model=config.model or self.default_model)

        # Register it
        from voiceobs.eval.providers import register_provider
        register_provider(MyProvider())
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The provider name (e.g., 'gemini', 'openai').

        This is used as the identifier when selecting a provider.
        """
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """The default model for this provider.

        Used when no model is specified in the config.
        """
        ...

    @abstractmethod
    def create_llm(self, config: EvalConfig) -> BaseChatModel:
        """Create a langchain chat model instance.

        Args:
            config: Evaluation configuration containing model, temperature,
                   and optional API key.

        Returns:
            A langchain BaseChatModel instance.

        Raises:
            ImportError: If the required langchain package is not installed.
        """
        ...
