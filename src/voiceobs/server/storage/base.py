"""Base classes and protocols for audio storage providers."""

from __future__ import annotations

from typing import Protocol


class AudioStorageProvider(Protocol):
    """Protocol for audio storage providers.

    All storage providers must implement these methods.
    """

    async def save(
        self, audio_data: bytes, conversation_id: str, audio_type: str | None = None
    ) -> str:
        """Save audio data and return a URL/path to the stored file.

        Args:
            audio_data: Raw audio data bytes (typically WAV format).
            conversation_id: Conversation identifier for file naming.
            audio_type: Optional audio type identifier (e.g., "asr", "tts", "user", "agent").
                If provided, will be included in the filename to support multiple audio files
                per conversation.

        Returns:
            URL or path to the stored audio file.
        """
        ...

    async def get(self, audio_id: str) -> bytes | None:
        """Retrieve audio data by ID.

        Args:
            audio_id: Audio file identifier (conversation_id or full path).

        Returns:
            Audio data bytes or None if not found.
        """
        ...

    async def exists(self, audio_id: str) -> bool:
        """Check if audio file exists.

        Args:
            audio_id: Audio file identifier.

        Returns:
            True if file exists, False otherwise.
        """
        ...

    async def delete(self, audio_id: str) -> bool:
        """Delete audio file.

        Args:
            audio_id: Audio file identifier.

        Returns:
            True if deleted, False if not found.
        """
        ...


class AudioStorage:
    """Audio storage service that uses a configured provider.

    This class acts as a factory and wrapper around storage providers,
    allowing easy switching between local and S3 storage.
    """

    def __init__(
        self,
        provider: str = "local",
        base_path: str | None = None,
        **kwargs: str,
    ) -> None:
        """Initialize audio storage with a provider.

        Args:
            provider: Storage provider name ("local" or "s3").
            base_path: Base path for local storage or S3 bucket name.
            **kwargs: Additional provider-specific configuration.
        """
        self._provider_name = provider
        self._provider: AudioStorageProvider

        if provider == "local":
            if base_path is None:
                raise ValueError("base_path is required for local storage")
            from voiceobs.server.storage.local import LocalFileStorage

            self._provider = LocalFileStorage(base_path=base_path)
        elif provider == "s3":
            if base_path is None:
                raise ValueError("base_path (bucket name) is required for S3 storage")
            from voiceobs.server.storage.s3 import S3Storage

            self._provider = S3Storage(
                bucket_name=base_path,
                **kwargs,
            )
        else:
            raise ValueError(f"Unknown storage provider: {provider}")

    async def save(
        self, audio_data: bytes, conversation_id: str, audio_type: str | None = None
    ) -> str:
        """Save audio data using the configured provider.

        Args:
            audio_data: Raw audio data bytes.
            conversation_id: Conversation identifier.
            audio_type: Optional audio type identifier (e.g., "asr", "tts", "user", "agent").

        Returns:
            URL or path to the stored audio file.
        """
        return await self._provider.save(audio_data, conversation_id, audio_type)

    async def get(self, audio_id: str) -> bytes | None:
        """Retrieve audio data by ID.

        Args:
            audio_id: Audio file identifier.

        Returns:
            Audio data bytes or None if not found.
        """
        return await self._provider.get(audio_id)

    async def exists(self, audio_id: str) -> bool:
        """Check if audio file exists.

        Args:
            audio_id: Audio file identifier.

        Returns:
            True if file exists, False otherwise.
        """
        return await self._provider.exists(audio_id)

    async def delete(self, audio_id: str) -> bool:
        """Delete audio file.

        Args:
            audio_id: Audio file identifier.

        Returns:
            True if deleted, False if not found.
        """
        return await self._provider.delete(audio_id)
