"""ElevenLabs TTS service implementation."""

import io
import os
from collections.abc import AsyncIterator
from typing import Any

from elevenlabs import AsyncElevenLabs

from voiceobs.server.services.tts import TTSService


class ElevenLabsTTSService(TTSService):
    """ElevenLabs TTS provider implementation.

    Uses the ElevenLabs TTS API to synthesize text to speech.
    Requires ELEVENLABS_API_KEY environment variable to be set.

    Example:
        >>> service = ElevenLabsTTSService()
        >>> config = {
        ...     "voice_id": "21m00Tcm4TlvDq8ikWAM",
        ...     "model_id": "eleven_turbo_v2",
        ...     "stability": 0.5,
        ...     "similarity_boost": 0.75
        ... }
        >>> audio, mime, duration = await service.synthesize("Hello", config)
    """

    # Default configuration constants
    DEFAULT_MODEL_ID = "eleven_turbo_v2"  # Updated from deprecated eleven_monolingual_v1
    DEFAULT_STABILITY = 0.5
    DEFAULT_SIMILARITY_BOOST = 0.75
    DEFAULT_MIME_TYPE = "audio/mpeg"

    # Audio estimation constants (for duration calculation fallback)
    DEFAULT_BITRATE_KBPS = 128  # ElevenLabs typically uses 128kbps

    def _get_client_and_config(
        self, config: dict[str, Any]
    ) -> tuple[AsyncElevenLabs, str, str, dict[str, float]]:
        """Get ElevenLabs client and extract configuration.

        Args:
            config: Provider-specific configuration

        Returns:
            Tuple of (client, voice_id, model_id, voice_settings)

        Raises:
            ValueError: If ELEVENLABS_API_KEY environment variable is not set
                or if voice_id is not provided in config
        """
        # Get API key from environment
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY environment variable is required for ElevenLabs TTS"
            )

        # Extract voice_id (required)
        voice_id = config.get("voice_id")
        if not voice_id:
            raise ValueError("voice_id is required in config for ElevenLabs TTS")

        # Extract config with defaults
        model_id = config.get("model_id", self.DEFAULT_MODEL_ID)
        stability = config.get("stability", self.DEFAULT_STABILITY)
        similarity_boost = config.get("similarity_boost", self.DEFAULT_SIMILARITY_BOOST)

        # Create voice settings dict
        voice_settings = {
            "stability": stability,
            "similarity_boost": similarity_boost,
        }

        # Create ElevenLabs client
        client = AsyncElevenLabs(api_key=api_key)

        return client, voice_id, model_id, voice_settings

    async def synthesize(self, text: str, config: dict[str, Any]) -> tuple[bytes, str, float]:
        """Synthesize text to audio using ElevenLabs TTS API.

        Args:
            text: Text to synthesize
            config: Provider-specific configuration with keys:
                - voice_id: Voice ID to use (required)
                - model_id: TTS model to use (default: "eleven_turbo_v2")
                - stability: Voice stability (default: 0.5)
                - similarity_boost: Voice similarity boost (default: 0.75)

        Returns:
            Tuple of (audio_bytes, mime_type, duration_ms)
                - audio_bytes: Raw audio data as bytes (MP3 format)
                - mime_type: MIME type of the audio ("audio/mpeg")
                - duration_ms: Duration of the audio in milliseconds

        Raises:
            ValueError: If ELEVENLABS_API_KEY environment variable is not set
                or if voice_id is not provided
            Exception: On ElevenLabs API errors
        """
        # Get client and config
        client, voice_id, model_id, voice_settings = self._get_client_and_config(config)

        # Call TTS API - convert returns an async generator of bytes
        audio_chunks = []
        async for chunk in client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            voice_settings=voice_settings,
        ):
            audio_chunks.append(chunk)

        # Combine all chunks into a single bytes object
        audio_bytes = b"".join(audio_chunks)

        # Calculate duration from audio data
        duration_ms = self._calculate_duration(audio_bytes)

        return audio_bytes, self.DEFAULT_MIME_TYPE, duration_ms

    async def synthesize_streaming(self, text: str, config: dict[str, Any]) -> AsyncIterator[bytes]:
        """Synthesize text to audio with streaming response using ElevenLabs TTS API.

        Args:
            text: Text to synthesize
            config: Provider-specific configuration with keys:
                - voice_id: Voice ID to use (required)
                - model_id: TTS model to use (default: "eleven_turbo_v2")
                - stability: Voice stability (default: 0.5)
                - similarity_boost: Voice similarity boost (default: 0.75)

        Yields:
            Audio data chunks as bytes (MP3 format)

        Raises:
            ValueError: If ELEVENLABS_API_KEY environment variable is not set
                or if voice_id is not provided
            Exception: On ElevenLabs API errors
        """
        # Get client and config
        client, voice_id, model_id, voice_settings = self._get_client_and_config(config)

        # Call TTS API with streaming - use text_to_speech.stream method
        stream = client.text_to_speech.stream(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            voice_settings=voice_settings,
        )

        # Stream audio chunks
        async for chunk in stream:
            yield chunk

    def _calculate_duration(self, audio_bytes: bytes) -> float:
        """Calculate audio duration from MP3 data.

        Args:
            audio_bytes: MP3 audio data

        Returns:
            Duration in milliseconds
        """
        try:
            # Use mutagen to parse MP3 and get duration
            from mutagen.mp3 import MP3

            audio_file = MP3(io.BytesIO(audio_bytes))
            return audio_file.info.length * 1000.0  # Convert to milliseconds
        except Exception:
            # If mutagen is not available or parsing fails,
            # estimate duration based on file size and bitrate
            # bitrate (kbps) / 8 = KB/s
            bytes_per_second = (self.DEFAULT_BITRATE_KBPS * 1000) / 8
            size_bytes = len(audio_bytes)
            duration_seconds = size_bytes / bytes_per_second
            return duration_seconds * 1000.0  # Convert to milliseconds
