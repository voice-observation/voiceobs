"""Tests for OpenAI TTS service implementation."""

import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voiceobs.server.services.tts import TTSService


class TestOpenAITTSService:
    """Tests for OpenAITTSService class."""

    @pytest.fixture
    def mock_openai_client(self) -> MagicMock:
        """Create a mock OpenAI client."""
        mock_client = MagicMock()
        mock_audio = MagicMock()
        mock_speech = MagicMock()

        # Mock the response
        mock_response = MagicMock()
        mock_response.content = b"fake_audio_data"
        mock_speech.create = AsyncMock(return_value=mock_response)

        mock_audio.speech = mock_speech
        mock_client.audio = mock_audio

        return mock_client

    @pytest.fixture
    def mock_env_with_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set OPENAI_API_KEY environment variable."""
        monkeypatch.setenv("OPENAI_API_KEY", "test_api_key_123")

    def test_openai_tts_service_inherits_from_tts_service(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that OpenAITTSService inherits from TTSService."""
        from voiceobs.server.services.openai_tts import OpenAITTSService

        service = OpenAITTSService()
        assert isinstance(service, TTSService)

    async def test_synthesize_with_default_config(
        self, mock_env_with_api_key: None, mock_openai_client: MagicMock
    ) -> None:
        """Test synthesize with default configuration."""
        from voiceobs.server.services.openai_tts import OpenAITTSService

        with patch("voiceobs.server.services.openai_tts.AsyncOpenAI") as mock_openai:
            mock_openai.return_value = mock_openai_client

            service = OpenAITTSService()
            audio_bytes, mime_type, duration_ms = await service.synthesize(
                "Hello world", {}
            )

            # Verify OpenAI client was created with API key
            mock_openai.assert_called_once_with(api_key="test_api_key_123")

            # Verify audio.speech.create was called with correct defaults
            mock_openai_client.audio.speech.create.assert_called_once_with(
                model="tts-1",
                voice="alloy",
                input="Hello world",
                speed=1.0,
            )

            # Verify return values
            assert audio_bytes == b"fake_audio_data"
            assert mime_type == "audio/mpeg"
            assert isinstance(duration_ms, float)
            assert duration_ms > 0

    async def test_synthesize_with_custom_config(
        self, mock_env_with_api_key: None, mock_openai_client: MagicMock
    ) -> None:
        """Test synthesize with custom configuration."""
        from voiceobs.server.services.openai_tts import OpenAITTSService

        with patch("voiceobs.server.services.openai_tts.AsyncOpenAI") as mock_openai:
            mock_openai.return_value = mock_openai_client

            service = OpenAITTSService()
            config: dict[str, Any] = {
                "model": "tts-1-hd",
                "voice": "nova",
                "speed": 1.25,
            }

            await service.synthesize("Test text", config)

            # Verify custom config was used
            mock_openai_client.audio.speech.create.assert_called_once_with(
                model="tts-1-hd",
                voice="nova",
                input="Test text",
                speed=1.25,
            )

    async def test_synthesize_with_partial_config(
        self, mock_env_with_api_key: None, mock_openai_client: MagicMock
    ) -> None:
        """Test synthesize with partial configuration (some defaults)."""
        from voiceobs.server.services.openai_tts import OpenAITTSService

        with patch("voiceobs.server.services.openai_tts.AsyncOpenAI") as mock_openai:
            mock_openai.return_value = mock_openai_client

            service = OpenAITTSService()
            config: dict[str, Any] = {"voice": "echo"}

            await service.synthesize("Test", config)

            # Verify partial config merged with defaults
            mock_openai_client.audio.speech.create.assert_called_once_with(
                model="tts-1",  # default
                voice="echo",   # custom
                input="Test",
                speed=1.0,      # default
            )

    async def test_synthesize_raises_error_when_api_key_missing(self) -> None:
        """Test that synthesize raises error when OPENAI_API_KEY is not set."""
        from voiceobs.server.services.openai_tts import OpenAITTSService

        # Make sure OPENAI_API_KEY is not set
        with patch.dict(os.environ, {}, clear=True):
            service = OpenAITTSService()

            with pytest.raises(ValueError) as exc_info:
                await service.synthesize("Hello", {})

            assert "OPENAI_API_KEY" in str(exc_info.value)

    async def test_synthesize_handles_openai_api_error(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that synthesize handles OpenAI API errors."""
        from voiceobs.server.services.openai_tts import OpenAITTSService

        with patch("voiceobs.server.services.openai_tts.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.audio.speech.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_openai.return_value = mock_client

            service = OpenAITTSService()

            with pytest.raises(Exception) as exc_info:
                await service.synthesize("Test", {})

            assert "API Error" in str(exc_info.value)

    async def test_synthesize_calculates_duration_from_audio(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that synthesize calculates duration from audio data."""
        from voiceobs.server.services.openai_tts import OpenAITTSService

        # Create mock with realistic audio data (MP3 format)
        # A simple MP3 header pattern for testing
        fake_mp3_data = b"\xff\xfb" + b"\x00" * 1000  # Simplified MP3 data

        with patch("voiceobs.server.services.openai_tts.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = fake_mp3_data
            mock_client.audio.speech.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            service = OpenAITTSService()
            audio_bytes, mime_type, duration_ms = await service.synthesize("Test", {})

            # Verify duration is calculated (should be > 0)
            assert audio_bytes == fake_mp3_data
            assert duration_ms > 0
            assert isinstance(duration_ms, float)

    async def test_synthesize_returns_correct_mime_type(
        self, mock_env_with_api_key: None, mock_openai_client: MagicMock
    ) -> None:
        """Test that synthesize returns correct MIME type."""
        from voiceobs.server.services.openai_tts import OpenAITTSService

        with patch("voiceobs.server.services.openai_tts.AsyncOpenAI") as mock_openai:
            mock_openai.return_value = mock_openai_client

            service = OpenAITTSService()
            _, mime_type, _ = await service.synthesize("Test", {})

            # OpenAI TTS returns MP3 format
            assert mime_type == "audio/mpeg"

    def test_openai_tts_service_registered_with_factory(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that OpenAITTSService is registered with the factory."""
        from voiceobs.server.services.openai_tts import OpenAITTSService
        from voiceobs.server.services.tts_factory import TTSServiceFactory

        # Ensure the provider is registered
        TTSServiceFactory.register_provider("openai", OpenAITTSService)

        # Verify it's in the providers list
        assert "openai" in TTSServiceFactory.list_providers()

        # Verify we can create it
        service = TTSServiceFactory.create("openai")
        assert isinstance(service, OpenAITTSService)

    async def test_synthesize_streaming_with_default_config(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test synthesize_streaming with default configuration."""
        from voiceobs.server.services.openai_tts import OpenAITTSService

        # Mock streaming response
        mock_chunks = [b"chunk1", b"chunk2", b"chunk3"]

        async def mock_iter_bytes():
            for chunk in mock_chunks:
                yield chunk

        with patch("voiceobs.server.services.openai_tts.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.iter_bytes = mock_iter_bytes
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_client.audio.speech.with_streaming_response.create = MagicMock(
                return_value=mock_response
            )
            mock_openai.return_value = mock_client

            service = OpenAITTSService()
            chunks = []
            async for chunk in service.synthesize_streaming("Hello world", {}):
                chunks.append(chunk)

            # Verify we got all chunks
            assert chunks == mock_chunks

            # Verify OpenAI client was called with correct defaults
            mock_client.audio.speech.with_streaming_response.create.assert_called_once_with(
                model="tts-1",
                voice="alloy",
                input="Hello world",
                speed=1.0,
            )

    async def test_synthesize_streaming_with_custom_config(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test synthesize_streaming with custom configuration."""
        from voiceobs.server.services.openai_tts import OpenAITTSService

        mock_chunks = [b"audio_data"]

        async def mock_iter_bytes():
            for chunk in mock_chunks:
                yield chunk

        with patch("voiceobs.server.services.openai_tts.AsyncOpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.iter_bytes = mock_iter_bytes
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_client.audio.speech.with_streaming_response.create = MagicMock(
                return_value=mock_response
            )
            mock_openai.return_value = mock_client

            service = OpenAITTSService()
            config: dict[str, Any] = {
                "model": "tts-1-hd",
                "voice": "nova",
                "speed": 1.5,
            }

            chunks = []
            async for chunk in service.synthesize_streaming("Test", config):
                chunks.append(chunk)

            # Verify custom config was used
            mock_client.audio.speech.with_streaming_response.create.assert_called_once_with(
                model="tts-1-hd",
                voice="nova",
                input="Test",
                speed=1.5,
            )

    async def test_synthesize_streaming_raises_error_when_api_key_missing(
        self,
    ) -> None:
        """Test that synthesize_streaming raises error when OPENAI_API_KEY is not set."""
        from voiceobs.server.services.openai_tts import OpenAITTSService

        with patch.dict(os.environ, {}, clear=True):
            service = OpenAITTSService()

            with pytest.raises(ValueError) as exc_info:
                async for _ in service.synthesize_streaming("Hello", {}):
                    pass

            assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_default_constants_are_defined(self) -> None:
        """Test that default constants are defined correctly."""
        from voiceobs.server.services.openai_tts import OpenAITTSService

        assert OpenAITTSService.DEFAULT_MODEL == "tts-1"
        assert OpenAITTSService.DEFAULT_VOICE == "alloy"
        assert OpenAITTSService.DEFAULT_SPEED == 1.0
        assert OpenAITTSService.DEFAULT_MIME_TYPE == "audio/mpeg"
        assert OpenAITTSService.DEFAULT_BITRATE_KBPS == 128
