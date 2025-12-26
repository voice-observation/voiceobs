"""Anthropic Claude LLM provider."""

from __future__ import annotations

from typing import TYPE_CHECKING

from voiceobs.eval.providers.base import LLMProvider

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

    from voiceobs.eval.types import EvalConfig


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider using langchain-anthropic."""

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return "claude-3-5-haiku-latest"

    def create_llm(self, config: EvalConfig) -> BaseChatModel:
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as e:
            raise ImportError(
                "langchain-anthropic is required for Anthropic. "
                "Install with: pip install langchain-anthropic"
            ) from e

        model = config.model or self.default_model
        kwargs = {"model": model, "temperature": config.temperature}
        if config.api_key:
            kwargs["api_key"] = config.api_key
        return ChatAnthropic(**kwargs)
