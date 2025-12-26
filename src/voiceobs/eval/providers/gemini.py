"""Google Gemini LLM provider."""

from __future__ import annotations

from typing import TYPE_CHECKING

from voiceobs.eval.providers.base import LLMProvider

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

    from voiceobs.eval.types import EvalConfig


class GeminiProvider(LLMProvider):
    """Google Gemini provider using langchain-google-genai."""

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return "gemini-2.0-flash"

    def create_llm(self, config: EvalConfig) -> BaseChatModel:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as e:
            raise ImportError(
                "langchain-google-genai is required for Gemini. "
                "Install with: pip install voiceobs[eval]"
            ) from e

        model = config.model or self.default_model
        kwargs = {"model": model, "temperature": config.temperature}
        if config.api_key:
            kwargs["google_api_key"] = config.api_key
        return ChatGoogleGenerativeAI(**kwargs)
