"""Tests for services package initialization."""

import pytest


class TestServicesInit:
    """Tests for services package __init__.py."""

    def test_base_exports_available(self):
        """Should export TTS and agent verification services."""
        from voiceobs.server.services import (
            AgentVerificationService,
            AgentVerifierFactory,
            DeepgramTTSService,
            ElevenLabsTTSService,
            OpenAITTSService,
            TTSService,
            TTSServiceFactory,
        )

        assert TTSService is not None
        assert TTSServiceFactory is not None
        assert OpenAITTSService is not None
        assert DeepgramTTSService is not None
        assert ElevenLabsTTSService is not None
        assert AgentVerificationService is not None
        assert AgentVerifierFactory is not None

    def test_tts_providers_registered(self):
        """Should have TTS providers registered with factory."""
        from voiceobs.server.services import TTSServiceFactory

        providers = TTSServiceFactory.list_providers()
        assert "openai" in providers
        assert "deepgram" in providers
        assert "elevenlabs" in providers

    def test_llm_exports_when_available(self):
        """Should export LLM services when available."""
        try:
            from voiceobs.server.services import (
                GeminiLLMService,
                LLMServiceFactory,
                OpenAILLMService,
            )

            assert LLMServiceFactory is not None
            assert OpenAILLMService is not None
            assert GeminiLLMService is not None
        except ImportError:
            # LLM services not available - this is OK
            pytest.skip("LLM services not available")

    def test_llm_providers_registered_when_available(self):
        """Should have LLM providers registered with factory when available."""
        try:
            from voiceobs.server.services import LLMServiceFactory

            providers = LLMServiceFactory.list_providers()
            assert "openai" in providers
            assert "gemini" in providers
        except ImportError:
            # LLM services not available - this is OK
            pytest.skip("LLM services not available")

    def test_all_includes_base_exports(self):
        """Should include base exports in __all__."""
        from voiceobs.server import services

        assert "TTSService" in services.__all__
        assert "TTSServiceFactory" in services.__all__
        assert "OpenAITTSService" in services.__all__
        assert "DeepgramTTSService" in services.__all__
        assert "ElevenLabsTTSService" in services.__all__
        assert "AgentVerificationService" in services.__all__
        assert "AgentVerifierFactory" in services.__all__
