"""Tests for LLM service factory."""

import os
from unittest.mock import patch

import pytest

from voiceobs.server.services.llm import LLMService
from voiceobs.server.services.llm_factory import LLMServiceFactory


class MockLLMService(LLMService):
    """Mock LLM service for testing."""

    async def generate_structured(self, prompt, output_schema, temperature=0.7):
        """Mock generate_structured implementation."""
        return output_schema()


class TestLLMServiceFactory:
    """Tests for LLMServiceFactory."""

    def setup_method(self):
        """Reset factory state before each test."""
        # Save original providers
        self._original_providers = LLMServiceFactory._providers.copy()

    def teardown_method(self):
        """Restore original factory state after each test."""
        LLMServiceFactory._providers = self._original_providers

    def test_register_provider(self):
        """Should register a provider."""
        LLMServiceFactory.register_provider("test_provider", MockLLMService)
        assert "test_provider" in LLMServiceFactory._providers
        assert LLMServiceFactory._providers["test_provider"] is MockLLMService

    def test_register_provider_case_insensitive(self):
        """Should register providers case-insensitively."""
        LLMServiceFactory.register_provider("TEST_PROVIDER", MockLLMService)
        assert "test_provider" in LLMServiceFactory._providers

    def test_list_providers(self):
        """Should list all registered providers."""
        LLMServiceFactory._providers = {}
        LLMServiceFactory.register_provider("provider_a", MockLLMService)
        LLMServiceFactory.register_provider("provider_b", MockLLMService)

        providers = LLMServiceFactory.list_providers()
        assert "provider_a" in providers
        assert "provider_b" in providers

    def test_create_with_explicit_provider(self):
        """Should create service for explicit provider."""
        LLMServiceFactory.register_provider("test", MockLLMService)
        service = LLMServiceFactory.create("test")
        assert isinstance(service, MockLLMService)

    def test_create_with_explicit_provider_case_insensitive(self):
        """Should create service case-insensitively."""
        LLMServiceFactory.register_provider("test", MockLLMService)
        service = LLMServiceFactory.create("TEST")
        assert isinstance(service, MockLLMService)

    def test_create_unsupported_provider_raises(self):
        """Should raise ValueError for unsupported provider."""
        LLMServiceFactory._providers = {"openai": MockLLMService}
        with pytest.raises(ValueError) as exc_info:
            LLMServiceFactory.create("unsupported")
        assert "Unsupported LLM provider" in str(exc_info.value)
        assert "unsupported" in str(exc_info.value)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
    def test_create_auto_detect_openai(self):
        """Should auto-detect OpenAI provider when API key is set."""
        LLMServiceFactory._providers = {"openai": MockLLMService}
        service = LLMServiceFactory.create()
        assert isinstance(service, MockLLMService)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=True)
    def test_create_auto_detect_gemini(self):
        """Should auto-detect Gemini provider when API key is set."""
        LLMServiceFactory._providers = {"gemini": MockLLMService}
        service = LLMServiceFactory.create()
        assert isinstance(service, MockLLMService)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
    def test_create_auto_detect_anthropic(self):
        """Should auto-detect Anthropic provider when API key is set."""
        LLMServiceFactory._providers = {"anthropic": MockLLMService}
        service = LLMServiceFactory.create()
        assert isinstance(service, MockLLMService)

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "openai-key", "GOOGLE_API_KEY": "google-key"},
        clear=True,
    )
    def test_create_auto_detect_prefers_openai(self):
        """Should prefer OpenAI over Gemini when both are available."""

        class OpenAIMock(LLMService):
            async def generate_structured(self, prompt, output_schema, temperature=0.7):
                return "openai"

        class GeminiMock(LLMService):
            async def generate_structured(self, prompt, output_schema, temperature=0.7):
                return "gemini"

        LLMServiceFactory._providers = {"openai": OpenAIMock, "gemini": GeminiMock}
        service = LLMServiceFactory.create()
        assert isinstance(service, OpenAIMock)

    @patch.dict(os.environ, {}, clear=True)
    def test_create_no_api_key_raises(self):
        """Should raise ValueError when no API keys are found."""
        # Ensure no env vars
        for key in ["OPENAI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"]:
            os.environ.pop(key, None)

        with pytest.raises(ValueError) as exc_info:
            LLMServiceFactory.create()
        assert "No LLM API key found" in str(exc_info.value)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
    def test_create_auto_detect_returns_none_if_provider_not_registered(self):
        """Should continue to next provider if current one not registered."""
        # Only register gemini, not openai
        LLMServiceFactory._providers = {}

        with pytest.raises(ValueError) as exc_info:
            LLMServiceFactory.create()
        assert "No LLM API key found" in str(exc_info.value)

    @patch.dict(
        os.environ,
        {"GOOGLE_API_KEY": "google-key", "ANTHROPIC_API_KEY": "anthropic-key"},
        clear=True,
    )
    def test_create_auto_detect_gemini_before_anthropic(self):
        """Should prefer Gemini over Anthropic."""

        class GeminiMock(LLMService):
            async def generate_structured(self, prompt, output_schema, temperature=0.7):
                return "gemini"

        class AnthropicMock(LLMService):
            async def generate_structured(self, prompt, output_schema, temperature=0.7):
                return "anthropic"

        LLMServiceFactory._providers = {"gemini": GeminiMock, "anthropic": AnthropicMock}
        service = LLMServiceFactory.create()
        assert isinstance(service, GeminiMock)
