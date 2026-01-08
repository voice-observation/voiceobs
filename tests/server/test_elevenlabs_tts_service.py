"""Tests for ElevenLabs TTS service implementation."""

import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voiceobs.server.services.tts import TTSService


class TestElevenLabsTTSService:
    """Tests for ElevenLabsTTSService class."""

    @pytest.fixture
    def mock_elevenlabs_client(self) -> MagicMock:
        """Create a mock ElevenLabs client."""
        mock_client = MagicMock()

        # Mock the generate method
        mock_audio_data = b"fake_elevenlabs_audio_data"
        mock_client.generate = AsyncMock(return_value=mock_audio_data)

        return mock_client

    @pytest.fixture
    def mock_env_with_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set ELEVENLABS_API_KEY environment variable."""
        monkeypatch.setenv("ELEVENLABS_API_KEY", "test_elevenlabs_key_123")

    def test_elevenlabs_tts_service_inherits_from_tts_service(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that ElevenLabsTTSService inherits from TTSService."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        service = ElevenLabsTTSService()
        assert isinstance(service, TTSService)

    async def test_synthesize_with_required_config(
        self, mock_env_with_api_key: None, mock_elevenlabs_client: MagicMock
    ) -> None:
        """Test synthesize with required voice_id configuration."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        with patch("voiceobs.server.services.elevenlabs_tts.AsyncElevenLabs") as mock_elevenlabs:
            mock_elevenlabs.return_value = mock_elevenlabs_client

            service = ElevenLabsTTSService()
            config = {"voice_id": "21m00Tcm4TlvDq8ikWAM"}

            audio_bytes, mime_type, duration_ms = await service.synthesize("Hello world", config)

            # Verify ElevenLabs client was created with API key
            mock_elevenlabs.assert_called_once_with(api_key="test_elevenlabs_key_123")

            # Verify generate was called with correct defaults
            mock_elevenlabs_client.generate.assert_called_once_with(
                text="Hello world",
                voice="21m00Tcm4TlvDq8ikWAM",
                model="eleven_monolingual_v1",
                voice_settings={
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            )

            # Verify return values
            assert audio_bytes == b"fake_elevenlabs_audio_data"
            assert mime_type == "audio/mpeg"
            assert isinstance(duration_ms, float)
            assert duration_ms > 0

    async def test_synthesize_with_custom_config(
        self, mock_env_with_api_key: None, mock_elevenlabs_client: MagicMock
    ) -> None:
        """Test synthesize with custom configuration."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        with patch("voiceobs.server.services.elevenlabs_tts.AsyncElevenLabs") as mock_elevenlabs:
            mock_elevenlabs.return_value = mock_elevenlabs_client

            service = ElevenLabsTTSService()
            config: dict[str, Any] = {
                "voice_id": "custom_voice_id",
                "model_id": "eleven_multilingual_v2",
                "stability": 0.7,
                "similarity_boost": 0.8,
            }

            await service.synthesize("Test text", config)

            # Verify custom config was used
            mock_elevenlabs_client.generate.assert_called_once_with(
                text="Test text",
                voice="custom_voice_id",
                model="eleven_multilingual_v2",
                voice_settings={
                    "stability": 0.7,
                    "similarity_boost": 0.8,
                },
            )

    async def test_synthesize_with_partial_config(
        self, mock_env_with_api_key: None, mock_elevenlabs_client: MagicMock
    ) -> None:
        """Test synthesize with partial configuration (some defaults)."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        with patch("voiceobs.server.services.elevenlabs_tts.AsyncElevenLabs") as mock_elevenlabs:
            mock_elevenlabs.return_value = mock_elevenlabs_client

            service = ElevenLabsTTSService()
            config: dict[str, Any] = {
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
                "stability": 0.6,
            }

            await service.synthesize("Test", config)

            # Verify partial config merged with defaults
            mock_elevenlabs_client.generate.assert_called_once_with(
                text="Test",
                voice="21m00Tcm4TlvDq8ikWAM",
                model="eleven_monolingual_v1",  # default
                voice_settings={
                    "stability": 0.6,  # custom
                    "similarity_boost": 0.75,  # default
                },
            )

    async def test_synthesize_raises_error_when_api_key_missing(self) -> None:
        """Test that synthesize raises error when ELEVENLABS_API_KEY is not set."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        # Make sure ELEVENLABS_API_KEY is not set
        with patch.dict(os.environ, {}, clear=True):
            service = ElevenLabsTTSService()

            with pytest.raises(ValueError) as exc_info:
                await service.synthesize("Hello", {"voice_id": "test"})

            assert "ELEVENLABS_API_KEY" in str(exc_info.value)

    async def test_synthesize_raises_error_when_voice_id_missing(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that synthesize raises error when voice_id is not provided."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        service = ElevenLabsTTSService()

        with pytest.raises(ValueError) as exc_info:
            await service.synthesize("Hello", {})

        assert "voice_id" in str(exc_info.value).lower()

    async def test_synthesize_handles_elevenlabs_api_error(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that synthesize handles ElevenLabs API errors."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        with patch("voiceobs.server.services.elevenlabs_tts.AsyncElevenLabs") as mock_elevenlabs:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(side_effect=Exception("ElevenLabs API Error"))
            mock_elevenlabs.return_value = mock_client

            service = ElevenLabsTTSService()

            with pytest.raises(Exception) as exc_info:
                await service.synthesize("Test", {"voice_id": "test"})

            assert "ElevenLabs API Error" in str(exc_info.value)

    async def test_synthesize_calculates_duration_from_audio(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that synthesize calculates duration from audio data."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        # Create mock with realistic audio data (MP3 format)
        fake_mp3_data = b"\xff\xfb" + b"\x00" * 1000  # Simplified MP3 data

        with patch("voiceobs.server.services.elevenlabs_tts.AsyncElevenLabs") as mock_elevenlabs:
            mock_client = MagicMock()
            mock_client.generate = AsyncMock(return_value=fake_mp3_data)
            mock_elevenlabs.return_value = mock_client

            service = ElevenLabsTTSService()
            config = {"voice_id": "test_voice"}
            audio_bytes, mime_type, duration_ms = await service.synthesize("Test", config)

            # Verify duration is calculated (should be > 0)
            assert audio_bytes == fake_mp3_data
            assert duration_ms > 0
            assert isinstance(duration_ms, float)

    async def test_synthesize_returns_correct_mime_type(
        self, mock_env_with_api_key: None, mock_elevenlabs_client: MagicMock
    ) -> None:
        """Test that synthesize returns correct MIME type."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        with patch("voiceobs.server.services.elevenlabs_tts.AsyncElevenLabs") as mock_elevenlabs:
            mock_elevenlabs.return_value = mock_elevenlabs_client

            service = ElevenLabsTTSService()
            config = {"voice_id": "test_voice"}
            _, mime_type, _ = await service.synthesize("Test", config)

            # ElevenLabs TTS returns MP3 format
            assert mime_type == "audio/mpeg"

    def test_elevenlabs_tts_service_registered_with_factory(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that ElevenLabsTTSService is registered with the factory."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService
        from voiceobs.server.services.tts_factory import TTSServiceFactory

        # Ensure the provider is registered
        TTSServiceFactory.register_provider("elevenlabs", ElevenLabsTTSService)

        # Verify it's in the providers list
        assert "elevenlabs" in TTSServiceFactory.list_providers()

        # Verify we can create it
        service = TTSServiceFactory.create("elevenlabs")
        assert isinstance(service, ElevenLabsTTSService)

    async def test_synthesize_streaming_with_required_config(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test synthesize_streaming with required voice_id configuration."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        # Mock streaming response
        mock_chunks = [b"chunk1", b"chunk2", b"chunk3"]

        async def mock_stream_generator():
            for chunk in mock_chunks:
                yield chunk

        with patch("voiceobs.server.services.elevenlabs_tts.AsyncElevenLabs") as mock_elevenlabs:
            mock_client = MagicMock()
            mock_client.generate = MagicMock(return_value=mock_stream_generator())
            mock_elevenlabs.return_value = mock_client

            service = ElevenLabsTTSService()
            config = {"voice_id": "21m00Tcm4TlvDq8ikWAM"}

            chunks = []
            async for chunk in service.synthesize_streaming("Hello world", config):
                chunks.append(chunk)

            # Verify we got all chunks
            assert chunks == mock_chunks

            # Verify ElevenLabs client was called with correct defaults
            mock_client.generate.assert_called_once_with(
                text="Hello world",
                voice="21m00Tcm4TlvDq8ikWAM",
                model="eleven_monolingual_v1",
                voice_settings={
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
                stream=True,
            )

    async def test_synthesize_streaming_with_custom_config(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test synthesize_streaming with custom configuration."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        mock_chunks = [b"audio_data"]

        async def mock_stream_generator():
            for chunk in mock_chunks:
                yield chunk

        with patch("voiceobs.server.services.elevenlabs_tts.AsyncElevenLabs") as mock_elevenlabs:
            mock_client = MagicMock()
            mock_client.generate = MagicMock(return_value=mock_stream_generator())
            mock_elevenlabs.return_value = mock_client

            service = ElevenLabsTTSService()
            config: dict[str, Any] = {
                "voice_id": "custom_voice",
                "model_id": "eleven_multilingual_v2",
                "stability": 0.8,
                "similarity_boost": 0.9,
            }

            chunks = []
            async for chunk in service.synthesize_streaming("Test", config):
                chunks.append(chunk)

            # Verify custom config was used
            mock_client.generate.assert_called_once_with(
                text="Test",
                voice="custom_voice",
                model="eleven_multilingual_v2",
                voice_settings={
                    "stability": 0.8,
                    "similarity_boost": 0.9,
                },
                stream=True,
            )

    async def test_synthesize_streaming_raises_error_when_api_key_missing(
        self,
    ) -> None:
        """Test that synthesize_streaming raises error when ELEVENLABS_API_KEY is not set."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        with patch.dict(os.environ, {}, clear=True):
            service = ElevenLabsTTSService()

            with pytest.raises(ValueError) as exc_info:
                async for _ in service.synthesize_streaming("Hello", {"voice_id": "test"}):
                    pass

            assert "ELEVENLABS_API_KEY" in str(exc_info.value)

    async def test_synthesize_streaming_raises_error_when_voice_id_missing(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that synthesize_streaming raises error when voice_id is not provided."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        service = ElevenLabsTTSService()

        with pytest.raises(ValueError) as exc_info:
            async for _ in service.synthesize_streaming("Hello", {}):
                pass

        assert "voice_id" in str(exc_info.value).lower()

    def test_default_constants_are_defined(self) -> None:
        """Test that default constants are defined correctly."""
        from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService

        assert ElevenLabsTTSService.DEFAULT_MODEL_ID == "eleven_monolingual_v1"
        assert ElevenLabsTTSService.DEFAULT_STABILITY == 0.5
        assert ElevenLabsTTSService.DEFAULT_SIMILARITY_BOOST == 0.75
        assert ElevenLabsTTSService.DEFAULT_MIME_TYPE == "audio/mpeg"
        assert ElevenLabsTTSService.DEFAULT_BITRATE_KBPS == 128
