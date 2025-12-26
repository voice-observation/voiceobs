"""OpenAI LLM provider."""

from __future__ import annotations

from typing import TYPE_CHECKING

from voiceobs.eval.providers.base import LLMProvider

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

    from voiceobs.eval.types import EvalConfig


class OpenAIProvider(LLMProvider):
    """OpenAI provider using langchain-openai."""

    @property
    def name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return "gpt-4o-mini"

    def create_llm(self, config: EvalConfig) -> BaseChatModel:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            raise ImportError(
                "langchain-openai is required for OpenAI. "
                "Install with: pip install langchain-openai"
            ) from e

        model = config.model or self.default_model
        kwargs = {"model": model, "temperature": config.temperature}
        if config.api_key:
            kwargs["api_key"] = config.api_key
        return ChatOpenAI(**kwargs)
