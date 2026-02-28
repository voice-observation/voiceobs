"""Audio storage module for voiceobs server.

Provides storage providers for audio files with support for local filesystem
and S3 storage backends.
"""

from voiceobs.server.clients.s3 import S3Storage
from voiceobs.server.storage.base import (
    AudioStorage,
    AudioStorageProvider,
    get_extension_from_content_type,
)
from voiceobs.server.storage.local import LocalFileStorage

__all__ = [
    "AudioStorage",
    "AudioStorageProvider",
    "LocalFileStorage",
    "S3Storage",
    "get_extension_from_content_type",
]
