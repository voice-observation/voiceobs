"""TTS service abstraction for managing text-to-speech providers."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class TTSService(ABC):
    """Abstract base class for TTS providers.

    All TTS provider implementations must inherit from this class and implement
    the synthesize and synthesize_streaming methods.
    """

    @abstractmethod
    async def synthesize(self, text: str, config: dict[str, Any]) -> tuple[bytes, str, float]:
        """Synthesize text to audio.

        Args:
            text: Text to synthesize
            config: Provider-specific configuration (e.g., voice, model, speed)

        Returns:
            Tuple of (audio_bytes, mime_type, duration_ms)
                - audio_bytes: Raw audio data as bytes
                - mime_type: MIME type of the audio (e.g., "audio/mpeg")
                - duration_ms: Duration of the audio in milliseconds

        Raises:
            Exception: Provider-specific errors during synthesis
        """
        pass

    @abstractmethod
    async def synthesize_streaming(self, text: str, config: dict[str, Any]) -> AsyncIterator[bytes]:
        """Synthesize text to audio with streaming response.

        Args:
            text: Text to synthesize
            config: Provider-specific configuration (e.g., voice, model, speed)

        Yields:
            Audio data chunks as bytes

        Raises:
            Exception: Provider-specific errors during synthesis
        """
        pass
