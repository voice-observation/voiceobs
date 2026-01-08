"""OpenAI TTS service implementation."""

import io
import os
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from voiceobs.server.services.tts import TTSService


class OpenAITTSService(TTSService):
    """OpenAI TTS provider implementation.

    Uses the OpenAI TTS API to synthesize text to speech.
    Requires OPENAI_API_KEY environment variable to be set.

    Example:
        >>> service = OpenAITTSService()
        >>> config = {"model": "tts-1", "voice": "alloy", "speed": 1.0}
        >>> audio, mime, duration = await service.synthesize("Hello", config)
    """

    # Default configuration constants
    DEFAULT_MODEL = "tts-1"
    DEFAULT_VOICE = "alloy"
    DEFAULT_SPEED = 1.0
    DEFAULT_MIME_TYPE = "audio/mpeg"

    # Audio estimation constants (for duration calculation fallback)
    DEFAULT_BITRATE_KBPS = 128  # OpenAI tts-1 typically uses 128kbps

    def _get_client_and_config(
        self, config: dict[str, Any]
    ) -> tuple[AsyncOpenAI, str, str, float]:
        """Get OpenAI client and extract configuration.

        Args:
            config: Provider-specific configuration

        Returns:
            Tuple of (client, model, voice, speed)

        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set
        """
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for OpenAI TTS"
            )

        # Extract config with defaults
        model = config.get("model", self.DEFAULT_MODEL)
        voice = config.get("voice", self.DEFAULT_VOICE)
        speed = config.get("speed", self.DEFAULT_SPEED)

        # Create OpenAI client
        client = AsyncOpenAI(api_key=api_key)

        return client, model, voice, speed

    async def synthesize(
        self, text: str, config: dict[str, Any]
    ) -> tuple[bytes, str, float]:
        """Synthesize text to audio using OpenAI TTS API.

        Args:
            text: Text to synthesize
            config: Provider-specific configuration with keys:
                - model: TTS model to use (default: "tts-1")
                - voice: Voice to use (default: "alloy")
                - speed: Speech speed (default: 1.0)

        Returns:
            Tuple of (audio_bytes, mime_type, duration_ms)
                - audio_bytes: Raw audio data as bytes (MP3 format)
                - mime_type: MIME type of the audio ("audio/mpeg")
                - duration_ms: Duration of the audio in milliseconds

        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set
            Exception: On OpenAI API errors
        """
        # Get client and config
        client, model, voice, speed = self._get_client_and_config(config)

        # Call TTS API
        response = await client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            speed=speed,
        )

        # Get audio bytes
        audio_bytes = response.content

        # Calculate duration from audio data
        duration_ms = self._calculate_duration(audio_bytes)

        return audio_bytes, self.DEFAULT_MIME_TYPE, duration_ms

    async def synthesize_streaming(
        self, text: str, config: dict[str, Any]
    ) -> AsyncIterator[bytes]:
        """Synthesize text to audio with streaming response using OpenAI TTS API.

        Args:
            text: Text to synthesize
            config: Provider-specific configuration with keys:
                - model: TTS model to use (default: "tts-1")
                - voice: Voice to use (default: "alloy")
                - speed: Speech speed (default: 1.0)

        Yields:
            Audio data chunks as bytes (MP3 format)

        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set
            Exception: On OpenAI API errors
        """
        # Get client and config
        client, model, voice, speed = self._get_client_and_config(config)

        # Call TTS API with streaming
        async with client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=text,
            speed=speed,
        ) as response:
            # Stream audio chunks
            async for chunk in response.iter_bytes():
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
