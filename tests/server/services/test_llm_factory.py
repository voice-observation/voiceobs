"""Tests for the LLMServiceFactory class."""

import os
from unittest.mock import MagicMock, patch

import pytest

from voiceobs.server.services.llm import LLMService
from voiceobs.server.services.llm_factory import LLMServiceFactory


class MockLLMService(LLMService):
    """Mock LLM service for testing."""

    async def generate_structured(self, prompt: str, output_schema, temperature: float = 0.7):
        """Mock implementation."""
        pass


class TestLLMServiceFactory:
    """Tests for the LLMServiceFactory class."""

    def teardown_method(self):
        """Reset factory state after each test."""
        # Don't clear providers, just ensure defaults are registered
        # The factory should maintain its state across tests
        pass

    def test_register_provider(self):
        """Test registering a new provider."""
        LLMServiceFactory._providers.clear()
        LLMServiceFactory.register_provider("test", MockLLMService)

        assert "test" in LLMServiceFactory._providers
        assert LLMServiceFactory._providers["test"] == MockLLMService

    def test_register_provider_case_insensitive(self):
        """Test that provider registration is case-insensitive."""
        LLMServiceFactory._providers.clear()
        LLMServiceFactory.register_provider("TEST", MockLLMService)
        LLMServiceFactory.register_provider("Test", MockLLMService)

        assert "test" in LLMServiceFactory._providers
        assert len(LLMServiceFactory._providers) == 1

    def test_list_providers(self):
        """Test listing registered providers."""
        LLMServiceFactory._providers.clear()
        LLMServiceFactory.register_provider("provider1", MockLLMService)
        LLMServiceFactory.register_provider("provider2", MockLLMService)

        providers = LLMServiceFactory.list_providers()

        assert "provider1" in providers
        assert "provider2" in providers
        assert len(providers) == 2

    def test_list_providers_empty(self):
        """Test listing providers when none are registered."""
        LLMServiceFactory._providers.clear()

        providers = LLMServiceFactory.list_providers()

        assert providers == []

    @patch.dict(os.environ, {}, clear=True)
    def test_create_with_provider(self):
        """Test creating a service with explicit provider."""
        LLMServiceFactory._providers.clear()
        LLMServiceFactory.register_provider("test", MockLLMService)

        service = LLMServiceFactory.create(provider="test")

        assert isinstance(service, MockLLMService)

    @patch.dict(os.environ, {}, clear=True)
    def test_create_with_provider_case_insensitive(self):
        """Test that provider name is case-insensitive."""
        LLMServiceFactory._providers.clear()
        LLMServiceFactory.register_provider("test", MockLLMService)

        service1 = LLMServiceFactory.create(provider="TEST")
        service2 = LLMServiceFactory.create(provider="Test")

        assert isinstance(service1, MockLLMService)
        assert isinstance(service2, MockLLMService)

    @patch.dict(os.environ, {}, clear=True)
    def test_create_with_unsupported_provider(self):
        """Test creating a service with unsupported provider raises error."""
        LLMServiceFactory._providers.clear()
        LLMServiceFactory.register_provider("test", MockLLMService)

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            LLMServiceFactory.create(provider="unsupported")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("voiceobs.server.services.openai_llm.OpenAILLMService")
    def test_create_auto_detect_openai(self, mock_openai_class):
        """Test auto-detection prefers OpenAI when available."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        # Temporarily replace the provider
        original_provider = LLMServiceFactory._providers.get("openai")
        LLMServiceFactory._providers["openai"] = mock_openai_class

        try:
            service = LLMServiceFactory.create()
            assert service == mock_service
            mock_openai_class.assert_called_once()
        finally:
            # Restore original provider
            if original_provider:
                LLMServiceFactory._providers["openai"] = original_provider
            elif "openai" in LLMServiceFactory._providers:
                del LLMServiceFactory._providers["openai"]

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=True)
    @patch("voiceobs.server.services.gemini_llm.GeminiLLMService")
    def test_create_auto_detect_gemini(self, mock_gemini_class):
        """Test auto-detection uses Gemini when OpenAI not available."""
        mock_service = MagicMock()
        mock_gemini_class.return_value = mock_service
        # Temporarily replace the provider
        original_provider = LLMServiceFactory._providers.get("gemini")
        LLMServiceFactory._providers["gemini"] = mock_gemini_class

        try:
            service = LLMServiceFactory.create()
            assert service == mock_service
            mock_gemini_class.assert_called_once()
        finally:
            # Restore original provider
            if original_provider:
                LLMServiceFactory._providers["gemini"] = original_provider
            elif "gemini" in LLMServiceFactory._providers:
                del LLMServiceFactory._providers["gemini"]

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "GOOGLE_API_KEY": "test-key2"})
    @patch("voiceobs.server.services.openai_llm.OpenAILLMService")
    def test_create_auto_detect_prefers_openai_over_gemini(self, mock_openai_class):
        """Test auto-detection prefers OpenAI over Gemini."""
        mock_openai_service = MagicMock()
        mock_openai_class.return_value = mock_openai_service
        # Temporarily replace the provider
        original_provider = LLMServiceFactory._providers.get("openai")
        LLMServiceFactory._providers["openai"] = mock_openai_class

        try:
            service = LLMServiceFactory.create()
            assert service == mock_openai_service
            mock_openai_class.assert_called_once()
        finally:
            # Restore original provider
            if original_provider:
                LLMServiceFactory._providers["openai"] = original_provider
            elif "openai" in LLMServiceFactory._providers:
                del LLMServiceFactory._providers["openai"]

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
    def test_create_auto_detect_anthropic_not_registered(self):
        """Test auto-detection fails when Anthropic key exists but provider not registered."""
        # Anthropic is not currently registered in the factory
        # So even with the key, it should raise ValueError
        with pytest.raises(ValueError, match="No LLM API key found"):
            LLMServiceFactory.create()

    @patch.dict(os.environ, {}, clear=True)
    def test_create_no_api_keys(self):
        """Test creating a service with no API keys raises error."""
        LLMServiceFactory._providers.clear()

        with pytest.raises(ValueError, match="No LLM API key found"):
            LLMServiceFactory.create()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_create_provider_not_registered(self):
        """Test that auto-detection works when provider is registered."""
        # OpenAI should be registered by default, so this should work
        # But we can test the case where it's not available by temporarily removing it
        original_provider = LLMServiceFactory._providers.get("openai")
        if "openai" in LLMServiceFactory._providers:
            del LLMServiceFactory._providers["openai"]

        try:
            with pytest.raises(ValueError, match="No LLM API key found"):
                LLMServiceFactory.create()
        finally:
            # Restore original provider
            if original_provider:
                LLMServiceFactory._providers["openai"] = original_provider
