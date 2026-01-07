"""Tests for TTS service base class."""

from typing import Any

import pytest

from voiceobs.server.services.tts import TTSService


class MockTTSService(TTSService):
    """Mock TTS service for testing."""

    async def synthesize(
        self, text: str, config: dict[str, Any]
    ) -> tuple[bytes, str, float]:
        """Mock synthesize implementation."""
        return b"mock_audio_data", "audio/mpeg", 1500.0


class TestTTSService:
    """Tests for TTSService abstract base class."""

    def test_tts_service_is_abstract(self) -> None:
        """Test that TTSService cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TTSService()  # type: ignore

    def test_mock_tts_service_can_be_instantiated(self) -> None:
        """Test that a concrete implementation can be instantiated."""
        service = MockTTSService()
        assert isinstance(service, TTSService)

    async def test_mock_tts_service_synthesize(self) -> None:
        """Test that mock TTS service synthesize works."""
        service = MockTTSService()
        audio_bytes, mime_type, duration_ms = await service.synthesize(
            "Hello world", {"voice": "alloy"}
        )
        assert audio_bytes == b"mock_audio_data"
        assert mime_type == "audio/mpeg"
        assert duration_ms == 1500.0
