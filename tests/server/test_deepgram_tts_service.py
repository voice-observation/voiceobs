"""Tests for Deepgram TTS service implementation."""

import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from voiceobs.server.services.tts import TTSService


class TestDeepgramTTSService:
    """Tests for DeepgramTTSService class."""

    @pytest.fixture
    def mock_deepgram_client(self) -> MagicMock:
        """Create a mock Deepgram client."""
        mock_client = MagicMock()
        mock_speak = MagicMock()
        mock_v1 = MagicMock()
        mock_audio = MagicMock()

        # Create realistic WAV data with proper header
        # Minimal WAV header (44 bytes) + some data
        fake_wav_data = b"RIFF" + b"\x00" * 36 + b"data" + b"\x00" * 1000

        # Mock the generate method to return an iterator
        mock_audio.generate = MagicMock(return_value=iter([fake_wav_data]))

        mock_v1.audio = mock_audio
        mock_speak.v1 = mock_v1
        mock_client.speak = mock_speak

        return mock_client

    @pytest.fixture
    def mock_env_with_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set DEEPGRAM_API_KEY environment variable."""
        monkeypatch.setenv("DEEPGRAM_API_KEY", "test_deepgram_key_123")

    def test_deepgram_tts_service_inherits_from_tts_service(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that DeepgramTTSService inherits from TTSService."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        service = DeepgramTTSService()
        assert isinstance(service, TTSService)

    async def test_synthesize_with_default_config(
        self, mock_env_with_api_key: None, mock_deepgram_client: MagicMock
    ) -> None:
        """Test synthesize with default configuration."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_deepgram.return_value = mock_deepgram_client

            service = DeepgramTTSService()
            audio_bytes, mime_type, duration_ms = await service.synthesize("Hello world", {})

            # Verify Deepgram client was created (it reads from env)
            mock_deepgram.assert_called_once()

            # Verify speak.v1.audio.generate was called with correct defaults
            call_args = mock_deepgram_client.speak.v1.audio.generate.call_args
            assert call_args is not None

            # Check the keyword arguments
            kwargs = call_args[1]
            assert kwargs["text"] == "Hello world"
            assert kwargs["model"] == "aura-asteria-en"
            assert kwargs["encoding"] == "linear16"
            assert kwargs["container"] == "wav"

            # Verify return values (should match the fake_wav_data from fixture)
            assert len(audio_bytes) > 0
            assert mime_type == "audio/wav"
            assert isinstance(duration_ms, float)
            assert duration_ms > 0

    async def test_synthesize_with_custom_config(
        self, mock_env_with_api_key: None, mock_deepgram_client: MagicMock
    ) -> None:
        """Test synthesize with custom configuration."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_deepgram.return_value = mock_deepgram_client

            service = DeepgramTTSService()
            config: dict[str, Any] = {
                "model": "aura-luna-en",
                "voice": "custom-voice",
            }

            await service.synthesize("Test text", config)

            # Verify custom config was used (encoding and container are fixed to defaults)
            call_args = mock_deepgram_client.speak.v1.audio.generate.call_args
            assert call_args is not None

            kwargs = call_args[1]
            assert kwargs["text"] == "Test text"
            assert kwargs["model"] == "aura-luna-en"
            assert kwargs["encoding"] == "linear16"  # Fixed encoding
            assert kwargs["container"] == "wav"  # Fixed container

    async def test_synthesize_with_partial_config(
        self, mock_env_with_api_key: None, mock_deepgram_client: MagicMock
    ) -> None:
        """Test synthesize with partial configuration (some defaults)."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_deepgram.return_value = mock_deepgram_client

            service = DeepgramTTSService()
            config: dict[str, Any] = {"model": "aura-hera-en"}

            await service.synthesize("Test", config)

            # Verify partial config merged with defaults
            call_args = mock_deepgram_client.speak.v1.audio.generate.call_args
            assert call_args is not None

            kwargs = call_args[1]
            assert kwargs["model"] == "aura-hera-en"  # custom
            assert kwargs["encoding"] == "linear16"  # default
            assert kwargs["container"] == "wav"  # default

    async def test_synthesize_raises_error_when_api_key_missing(self) -> None:
        """Test that synthesize raises error when DEEPGRAM_API_KEY is not set."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        # Make sure DEEPGRAM_API_KEY is not set
        with patch.dict(os.environ, {}, clear=True):
            service = DeepgramTTSService()

            with pytest.raises(ValueError) as exc_info:
                await service.synthesize("Hello", {})

            assert "DEEPGRAM_API_KEY" in str(exc_info.value)

    async def test_synthesize_handles_deepgram_api_error(self, mock_env_with_api_key: None) -> None:
        """Test that synthesize handles Deepgram API errors."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_client = MagicMock()
            mock_client.speak.v1.audio.generate = MagicMock(side_effect=Exception("API Error"))
            mock_deepgram.return_value = mock_client

            service = DeepgramTTSService()

            with pytest.raises(Exception) as exc_info:
                await service.synthesize("Test", {})

            assert "API Error" in str(exc_info.value)

    async def test_synthesize_calculates_duration_from_audio(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that synthesize calculates duration from audio data."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        # Create mock with realistic audio data (WAV format)
        # A simple WAV header pattern for testing
        fake_wav_data = b"RIFF" + b"\x00" * 36 + b"data" + b"\x00" * 1000

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_client = MagicMock()
            mock_client.speak.v1.audio.generate = MagicMock(return_value=iter([fake_wav_data]))
            mock_deepgram.return_value = mock_client

            service = DeepgramTTSService()
            audio_bytes, mime_type, duration_ms = await service.synthesize("Test", {})

            # Verify duration is calculated (should be > 0)
            assert audio_bytes == fake_wav_data
            assert duration_ms > 0
            assert isinstance(duration_ms, float)

    async def test_synthesize_returns_correct_mime_type_for_wav(
        self, mock_env_with_api_key: None, mock_deepgram_client: MagicMock
    ) -> None:
        """Test that synthesize returns correct MIME type for WAV."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_deepgram.return_value = mock_deepgram_client

            service = DeepgramTTSService()
            _, mime_type, _ = await service.synthesize("Test", {})

            # Default container is WAV
            assert mime_type == "audio/wav"

    async def test_synthesize_returns_correct_mime_type_for_wav_only(
        self, mock_env_with_api_key: None, mock_deepgram_client: MagicMock
    ) -> None:
        """Test that synthesize returns correct MIME type (WAV only supported)."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_deepgram.return_value = mock_deepgram_client

            service = DeepgramTTSService()
            # Config is ignored for container/encoding (fixed to WAV)
            config: dict[str, Any] = {}
            _, mime_type, _ = await service.synthesize("Test", config)

            assert mime_type == "audio/wav"

    def test_deepgram_tts_service_registered_with_factory(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test that DeepgramTTSService is registered with the factory."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService
        from voiceobs.server.services.tts_factory import TTSServiceFactory

        # Ensure the provider is registered
        TTSServiceFactory.register_provider("deepgram", DeepgramTTSService)

        # Verify it's in the providers list
        assert "deepgram" in TTSServiceFactory.list_providers()

        # Verify we can create it
        service = TTSServiceFactory.create("deepgram")
        assert isinstance(service, DeepgramTTSService)

    async def test_synthesize_streaming_with_default_config(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test synthesize_streaming with default configuration."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        # Mock streaming response
        mock_chunks = [b"chunk1", b"chunk2", b"chunk3"]

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_client = MagicMock()
            # The generate method returns a regular iterator (not async)
            mock_client.speak.v1.audio.generate = MagicMock(return_value=iter(mock_chunks))
            mock_deepgram.return_value = mock_client

            service = DeepgramTTSService()
            chunks = []
            async for chunk in service.synthesize_streaming("Hello world", {}):
                chunks.append(chunk)

            # Verify we got all chunks
            assert chunks == mock_chunks

            # Verify Deepgram client was called with correct defaults
            call_args = mock_client.speak.v1.audio.generate.call_args
            assert call_args is not None

            kwargs = call_args[1]
            assert kwargs["text"] == "Hello world"
            assert kwargs["model"] == "aura-asteria-en"

    async def test_synthesize_streaming_with_custom_config(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test synthesize_streaming with custom configuration."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        mock_chunks = [b"audio_data"]

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_client = MagicMock()
            mock_client.speak.v1.audio.generate = MagicMock(return_value=iter(mock_chunks))
            mock_deepgram.return_value = mock_client

            service = DeepgramTTSService()
            config: dict[str, Any] = {
                "model": "aura-zeus-en",
            }

            chunks = []
            async for chunk in service.synthesize_streaming("Test", config):
                chunks.append(chunk)

            # Verify custom config was used (encoding is fixed to linear16)
            call_args = mock_client.speak.v1.audio.generate.call_args
            assert call_args is not None

            kwargs = call_args[1]
            assert kwargs["model"] == "aura-zeus-en"
            assert kwargs["encoding"] == "linear16"  # Fixed encoding
            assert kwargs["container"] == "wav"  # Fixed container

    async def test_synthesize_streaming_raises_error_when_api_key_missing(
        self,
    ) -> None:
        """Test that synthesize_streaming raises error when DEEPGRAM_API_KEY is not set."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        with patch.dict(os.environ, {}, clear=True):
            service = DeepgramTTSService()

            with pytest.raises(ValueError) as exc_info:
                async for _ in service.synthesize_streaming("Hello", {}):
                    pass

            assert "DEEPGRAM_API_KEY" in str(exc_info.value)

    def test_default_constants_are_defined(self) -> None:
        """Test that default constants are defined correctly."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        assert DeepgramTTSService.DEFAULT_MODEL == "aura-asteria-en"
        assert DeepgramTTSService.ENCODING == "linear16"
        assert DeepgramTTSService.CONTAINER == "wav"

    async def test_synthesize_with_voice_parameter(
        self, mock_env_with_api_key: None, mock_deepgram_client: MagicMock
    ) -> None:
        """Test synthesize with voice parameter (for future compatibility)."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_deepgram.return_value = mock_deepgram_client

            service = DeepgramTTSService()
            config: dict[str, Any] = {"voice": "custom-voice-id"}

            # Voice parameter should be accepted without error
            await service.synthesize("Test", config)

            # Should complete without raising an exception
            assert mock_deepgram_client.speak.v1.audio.generate.called

    async def test_calculate_duration_wav_fallback(self, mock_env_with_api_key: None) -> None:
        """Test duration calculation fallback for invalid WAV."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        # Invalid WAV data that will cause wave.open to fail
        # Use valid WAV header but with invalid structure to trigger fallback
        invalid_wav_data = b"RIFF" + b"\x00" * 8 + b"WAVE" + b"INVA" + b"\x00" * 100

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_client = MagicMock()
            mock_client.speak.v1.audio.generate = MagicMock(return_value=iter([invalid_wav_data]))
            mock_deepgram.return_value = mock_client

            service = DeepgramTTSService()
            _, _, duration_ms = await service.synthesize("Test", {})

            # Should fall back to estimation and still return valid duration
            assert duration_ms > 0
            assert isinstance(duration_ms, float)

    async def test_estimate_duration_for_invalid_wav_fallback(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test duration estimation fallback when WAV parsing fails."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        # Invalid WAV data that will cause parsing to fail
        invalid_wav_data = b"RIFF" + b"\x00" * 8 + b"WAVE" + b"INVA" + b"\x00" * 1000

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_client = MagicMock()
            mock_client.speak.v1.audio.generate = MagicMock(return_value=iter([invalid_wav_data]))
            mock_deepgram.return_value = mock_client

            service = DeepgramTTSService()
            # Config is ignored - always uses WAV/linear16
            _, _, duration_ms = await service.synthesize("Test", {})

            # Should fall back to estimation and still return valid duration
            assert duration_ms > 0
            assert isinstance(duration_ms, float)

    async def test_calculate_duration_exception_in_outer_handler(
        self, mock_env_with_api_key: None
    ) -> None:
        """Test exception handling in outer _calculate_duration method."""
        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_client = MagicMock()
            # Create a minimal WAV that will trigger inner exception
            # when trying to parse it
            bad_data = b"RIFF" + b"\x00" * 100

            mock_client.speak.v1.audio.generate = MagicMock(return_value=iter([bad_data]))
            mock_deepgram.return_value = mock_client

            service = DeepgramTTSService()

            # Patch the internal methods to raise an exception
            # This will trigger the outer exception handler
            with patch.object(service, "_calculate_wav_duration", side_effect=RuntimeError("Test")):
                _, _, duration_ms = await service.synthesize("Test", {})

                # Should fall back to estimation via outer exception handler
                assert duration_ms > 0
                assert isinstance(duration_ms, float)

    async def test_calculate_wav_duration_success_path(self, mock_env_with_api_key: None) -> None:
        """Test successful WAV duration calculation with valid WAV data."""
        import io
        import wave

        from voiceobs.server.services.deepgram_tts import DeepgramTTSService

        # Create a valid WAV file in memory
        # 1 second of audio: 24000 samples at 24000 Hz = 1 second
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(24000)  # 24kHz
            # 24000 frames = 1 second (24000 samples / 24000 Hz)
            wav_file.writeframes(b"\x00" * (24000 * 2))  # 24000 frames * 2 bytes per sample

        valid_wav_data = wav_buffer.getvalue()

        with patch("voiceobs.server.services.deepgram_tts.DeepgramClient") as mock_deepgram:
            mock_client = MagicMock()
            mock_client.speak.v1.audio.generate = MagicMock(return_value=iter([valid_wav_data]))
            mock_deepgram.return_value = mock_client

            service = DeepgramTTSService()
            _, _, duration_ms = await service.synthesize("Test", {})

            # Should get the duration from WAV file (approximately 1000ms for 1 second)
            assert abs(duration_ms - 1000.0) < 100  # Allow some tolerance
            assert isinstance(duration_ms, float)
            assert duration_ms > 0
