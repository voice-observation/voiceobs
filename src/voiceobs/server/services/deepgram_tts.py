"""Deepgram TTS service implementation."""

import io
import os
from collections.abc import AsyncIterator
from typing import Any

from deepgram import DeepgramClient

from voiceobs.server.services.tts import TTSService


class DeepgramTTSService(TTSService):
    """Deepgram TTS provider implementation.

    Uses the Deepgram TTS API to synthesize text to speech.
    Requires DEEPGRAM_API_KEY environment variable to be set.

    Example:
        >>> service = DeepgramTTSService()
        >>> config = {"model": "aura-asteria-en"}
        >>> audio, mime, duration = await service.synthesize("Hello", config)
    """

    # Default configuration constants
    DEFAULT_MODEL = "aura-asteria-en"
    ENCODING = "linear16"  # Fixed encoding
    CONTAINER = "wav"  # Fixed container format
    MIME_TYPE = "audio/wav"  # Fixed MIME type

    # Audio estimation constants (for duration calculation fallback)
    DEFAULT_SAMPLE_RATE = 24000  # Deepgram default
    DEFAULT_BITS_PER_SAMPLE = 16
    DEFAULT_CHANNELS = 1

    def _get_client_and_model(
        self, config: dict[str, Any]
    ) -> tuple[DeepgramClient, str]:
        """Get Deepgram client and extract model from configuration.

        Args:
            config: Provider-specific configuration

        Returns:
            Tuple of (client, model)

        Raises:
            ValueError: If DEEPGRAM_API_KEY environment variable is not set
        """
        # Get API key from environment
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            raise ValueError(
                "DEEPGRAM_API_KEY environment variable is required for Deepgram TTS"
            )

        # Extract model with default
        model = config.get("model", self.DEFAULT_MODEL)

        # Create Deepgram client
        client = DeepgramClient(api_key=api_key)

        return client, model

    async def synthesize(
        self, text: str, config: dict[str, Any]
    ) -> tuple[bytes, str, float]:
        """Synthesize text to audio using Deepgram TTS API.

        Args:
            text: Text to synthesize
            config: Provider-specific configuration with keys:
                - model: TTS model to use (default: "aura-asteria-en")

        Returns:
            Tuple of (audio_bytes, mime_type, duration_ms)
                - audio_bytes: Raw audio data as bytes (WAV format)
                - mime_type: MIME type of the audio ("audio/wav")
                - duration_ms: Duration of the audio in milliseconds

        Raises:
            ValueError: If DEEPGRAM_API_KEY environment variable is not set
            Exception: On Deepgram API errors
        """
        # Get client and model
        client, model = self._get_client_and_model(config)

        # Call TTS API - generate returns an iterator of bytes
        response = client.speak.v1.audio.generate(
            text=text,
            model=model,
            encoding=self.ENCODING,
            container=self.CONTAINER,
        )

        # Collect all audio chunks - response is an iterator of bytes
        audio_bytes = b"".join(response)

        # Verify we have valid audio data
        if len(audio_bytes) == 0:
            raise ValueError("Received empty audio data from Deepgram API")

        # Verify WAV header
        if len(audio_bytes) >= 4 and audio_bytes[:4] != b"RIFF":
            raise ValueError(
                f"Invalid WAV file: expected RIFF header, got {audio_bytes[:4]}"
            )

        # Calculate duration from audio data
        duration_ms = self._calculate_duration(audio_bytes)

        return audio_bytes, self.MIME_TYPE, duration_ms

    async def synthesize_streaming(
        self, text: str, config: dict[str, Any]
    ) -> AsyncIterator[bytes]:
        """Synthesize text to audio with streaming response using Deepgram TTS API.

        Args:
            text: Text to synthesize
            config: Provider-specific configuration with keys:
                - model: TTS model to use (default: "aura-asteria-en")

        Yields:
            Audio data chunks as bytes (WAV format)

        Raises:
            ValueError: If DEEPGRAM_API_KEY environment variable is not set
            Exception: On Deepgram API errors
        """
        # Get client and model
        client, model = self._get_client_and_model(config)

        # Call TTS API with streaming - generate returns an iterator
        response = client.speak.v1.audio.generate(
            text=text,
            model=model,
            encoding=self.ENCODING,
            container=self.CONTAINER,
        )

        # Stream audio chunks as they arrive
        for chunk in response:
            yield chunk

    def _calculate_duration(self, audio_bytes: bytes) -> float:
        """Calculate audio duration from WAV audio data.

        Args:
            audio_bytes: WAV audio data

        Returns:
            Duration in milliseconds
        """
        try:
            return self._calculate_wav_duration(audio_bytes)
        except Exception:
            # If parsing fails, estimate duration based on file size
            return self._estimate_duration(audio_bytes)

    def _calculate_wav_duration(self, audio_bytes: bytes) -> float:
        """Calculate duration from WAV file.

        Args:
            audio_bytes: WAV audio data

        Returns:
            Duration in milliseconds
        """
        try:
            import wave

            with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                if rate > 0 and frames > 0:
                    duration_seconds = frames / float(rate)
                    duration_ms = duration_seconds * 1000.0
                    # Sanity check: duration should be reasonable
                    if 0 < duration_ms < 3600000:  # Less than 1 hour
                        return duration_ms
        except Exception:
            pass
        # Fallback to estimation if parsing fails or result is unreasonable
        return self._estimate_duration(audio_bytes)

    def _estimate_duration(self, audio_bytes: bytes) -> float:
        """Estimate audio duration based on file size for WAV/linear16.

        Args:
            audio_bytes: WAV audio data

        Returns:
            Duration in milliseconds
        """
        size_bytes = len(audio_bytes)

        # For WAV/linear16, calculate based on uncompressed PCM
        # bytes_per_second = sample_rate * (bits_per_sample / 8) * channels
        bytes_per_second = (
            self.DEFAULT_SAMPLE_RATE
            * (self.DEFAULT_BITS_PER_SAMPLE / 8)
            * self.DEFAULT_CHANNELS
        )
        # WAV header is typically 44 bytes
        data_bytes = max(0, size_bytes - 44)
        duration_seconds = data_bytes / bytes_per_second
        duration_ms = duration_seconds * 1000.0
        # Sanity check
        if 0 < duration_ms < 3600000:
            return duration_ms
        # Conservative fallback
        return min(duration_ms, size_bytes / 1000.0)
