"""Local filesystem storage provider for audio files."""

from __future__ import annotations

import uuid
from pathlib import Path

from voiceobs.server.storage.base import get_extension_from_content_type


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

    async def store_audio(
        self, audio_data: bytes, prefix: str, content_type: str | None = None
    ) -> str:
        """Store audio data with a custom prefix pattern.

        Args:
            audio_data: Raw audio data bytes.
            prefix: Prefix pattern for file storage (e.g., "personas/preview/persona-id").
            content_type: MIME type of the audio (e.g., "audio/mpeg", "audio/wav").
                Defaults to "audio/wav" if not provided.

        Returns:
            URL path to the stored file.
        """
        import asyncio

        # Determine file extension from content type
        extension = get_extension_from_content_type(content_type)

        # Generate unique filename with prefix
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}{extension}"

        # Create full path with prefix (prefix can contain subdirectories)
        file_path = self.base_path / prefix / filename

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file asynchronously
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, file_path.write_bytes, audio_data)

        # Return URL path
        # Format: /audio/prefix/filename
        return f"/audio/{prefix}/{filename}"

    async def delete_by_url(self, url: str) -> bool:
        """Delete audio file by its URL.

        Args:
            url: The URL returned from store_audio (e.g., "/audio/prefix/file.mp3").

        Returns:
            True if deleted, False if not found or invalid URL.
        """
        import asyncio

        # Parse URL format: /audio/prefix/filename
        if not url.startswith("/audio/"):
            return False

        # Extract path after /audio/
        relative_path = url[7:]  # Remove "/audio/"
        if not relative_path:
            return False

        file_path = self.base_path / relative_path

        # Security: Ensure the resolved path is within base_path (prevent path traversal)
        try:
            resolved_path = file_path.resolve()
            base_resolved = self.base_path.resolve()
            if not str(resolved_path).startswith(str(base_resolved)):
                return False
        except (ValueError, OSError):
            return False

        if not file_path.exists():
            return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, file_path.unlink)
            return True
        except Exception:
            return False
