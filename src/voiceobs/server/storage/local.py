"""Local filesystem storage provider for audio files."""

from __future__ import annotations

from pathlib import Path


class LocalFileStorage:
    """Local filesystem storage provider for audio files.

    Saves audio files to a local directory with .wav extension.
    """

    def __init__(self, base_path: str) -> None:
        """Initialize local file storage.

        Args:
            base_path: Base directory path for storing audio files.
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, conversation_id: str, audio_type: str | None = None) -> Path:
        """Generate file path for a conversation ID.

        Args:
            conversation_id: Conversation identifier.
            audio_type: Optional audio type identifier (e.g., "asr", "tts", "user", "agent").
                If provided, will be included in the filename.

        Returns:
            Path object for the audio file.
        """
        if audio_type:
            filename = f"{conversation_id}-{audio_type}.wav"
        else:
            filename = f"{conversation_id}.wav"
        return self.base_path / filename

    def _get_url(self, conversation_id: str, audio_type: str | None = None) -> str:
        """Generate URL/path for a conversation ID.

        Args:
            conversation_id: Conversation identifier.
            audio_type: Optional audio type identifier.

        Returns:
            URL path string.
        """
        if audio_type:
            return f"/audio/{conversation_id}?type={audio_type}"
        return f"/audio/{conversation_id}"

    async def save(
        self, audio_data: bytes, conversation_id: str, audio_type: str | None = None
    ) -> str:
        """Save audio data to local filesystem.

        Args:
            audio_data: Raw audio data bytes.
            conversation_id: Conversation identifier.
            audio_type: Optional audio type identifier (e.g., "asr", "tts", "user", "agent").

        Returns:
            URL path to the stored file.
        """
        import asyncio

        file_path = self._get_file_path(conversation_id, audio_type)
        # Run file I/O in executor to make it truly async
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, file_path.write_bytes, audio_data)
        return self._get_url(conversation_id, audio_type)

    async def get(self, audio_id: str) -> bytes | None:
        """Retrieve audio data from local filesystem.

        Args:
            audio_id: Conversation ID (filename without extension).

        Returns:
            Audio data bytes or None if not found.
        """
        import asyncio

        file_path = self._get_file_path(audio_id)
        if not file_path.exists():
            return None
        # Run file I/O in executor to make it truly async
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, file_path.read_bytes)

    async def exists(self, audio_id: str) -> bool:
        """Check if audio file exists.

        Args:
            audio_id: Conversation ID.

        Returns:
            True if file exists, False otherwise.
        """
        import asyncio

        file_path = self._get_file_path(audio_id)
        # Run file check in executor to make it truly async
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, file_path.exists)

    async def delete(self, audio_id: str) -> bool:
        """Delete audio file from local filesystem.

        Args:
            audio_id: Conversation ID.

        Returns:
            True if deleted, False if not found.
        """
        import asyncio

        file_path = self._get_file_path(audio_id)
        if not file_path.exists():
            return False
        # Run file deletion in executor to make it truly async
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, file_path.unlink)
        return True
