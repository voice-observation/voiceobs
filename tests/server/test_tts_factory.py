"""Tests for TTS service factory."""

from collections.abc import AsyncIterator
from typing import Any

import pytest

from voiceobs.server.services.tts import TTSService
from voiceobs.server.services.tts_factory import TTSServiceFactory


class MockTTSService(TTSService):
    """Mock TTS service for testing."""

    async def synthesize(
        self, text: str, config: dict[str, Any]
    ) -> tuple[bytes, str, float]:
        """Mock synthesize implementation."""
        return b"mock_audio_data", "audio/mpeg", 1500.0

    async def synthesize_streaming(
        self, text: str, config: dict[str, Any]
    ) -> AsyncIterator[bytes]:
        """Mock synthesize_streaming implementation."""
        yield b"mock_chunk_1"
        yield b"mock_chunk_2"


class TestTTSServiceFactory:
    """Tests for TTSServiceFactory class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Clear any registered providers before each test
        TTSServiceFactory._providers = {}

    def test_factory_create_raises_value_error_for_unknown_provider(self) -> None:
        """Test that creating an unknown provider raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TTSServiceFactory.create("unknown_provider")

        error_message = str(exc_info.value)
        assert "Unsupported TTS provider: unknown_provider" in error_message
        assert "Supported providers:" in error_message

    def test_factory_create_with_registered_provider(self) -> None:
        """Test creating a service with a registered provider."""
        TTSServiceFactory.register_provider("mock", MockTTSService)
        service = TTSServiceFactory.create("mock")

        assert isinstance(service, MockTTSService)
        assert isinstance(service, TTSService)

    def test_factory_create_is_case_insensitive(self) -> None:
        """Test that provider names are case-insensitive."""
        TTSServiceFactory.register_provider("mock", MockTTSService)

        service_lower = TTSServiceFactory.create("mock")
        service_upper = TTSServiceFactory.create("MOCK")
        service_mixed = TTSServiceFactory.create("MoCk")

        assert isinstance(service_lower, MockTTSService)
        assert isinstance(service_upper, MockTTSService)
        assert isinstance(service_mixed, MockTTSService)

    def test_factory_register_provider(self) -> None:
        """Test registering a new provider."""
        TTSServiceFactory.register_provider("test_provider", MockTTSService)
        assert "test_provider" in TTSServiceFactory._providers
        assert TTSServiceFactory._providers["test_provider"] == MockTTSService

    def test_factory_register_provider_is_case_insensitive(self) -> None:
        """Test that provider registration is case-insensitive."""
        TTSServiceFactory.register_provider("TestProvider", MockTTSService)
        assert "testprovider" in TTSServiceFactory._providers

    def test_factory_list_providers(self) -> None:
        """Test listing registered providers."""
        TTSServiceFactory.register_provider("provider1", MockTTSService)
        TTSServiceFactory.register_provider("provider2", MockTTSService)

        providers = TTSServiceFactory.list_providers()

        assert isinstance(providers, list)
        assert "provider1" in providers
        assert "provider2" in providers
        assert len(providers) == 2

    def test_factory_list_providers_returns_empty_list_when_no_providers(
        self,
    ) -> None:
        """Test that list_providers returns empty list when no providers registered."""
        providers = TTSServiceFactory.list_providers()
        assert providers == []

    def test_factory_create_returns_new_instance_each_time(self) -> None:
        """Test that create() returns a new instance each time."""
        TTSServiceFactory.register_provider("mock", MockTTSService)

        service1 = TTSServiceFactory.create("mock")
        service2 = TTSServiceFactory.create("mock")

        assert service1 is not service2
        assert isinstance(service1, MockTTSService)
        assert isinstance(service2, MockTTSService)

    def test_factory_create_error_message_shows_available_providers(self) -> None:
        """Test that error message lists available providers."""
        TTSServiceFactory.register_provider("openai", MockTTSService)
        TTSServiceFactory.register_provider("elevenlabs", MockTTSService)

        with pytest.raises(ValueError) as exc_info:
            TTSServiceFactory.create("unknown")

        error_message = str(exc_info.value)
        assert "openai" in error_message
        assert "elevenlabs" in error_message

    def test_factory_providers_dict_is_class_variable(self) -> None:
        """Test that _providers is a class variable shared across instances."""
        TTSServiceFactory.register_provider("mock", MockTTSService)

        # Access through class
        assert "mock" in TTSServiceFactory._providers

        # Verify it's shared (not instance-specific)
        providers_list = TTSServiceFactory.list_providers()
        assert "mock" in providers_list
