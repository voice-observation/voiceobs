"""Audio storage module for voiceobs server.

Provides storage providers for audio files with support for local filesystem
and S3 storage backends.
"""

from voiceobs.server.storage.base import AudioStorage, AudioStorageProvider
from voiceobs.server.storage.local import LocalFileStorage
from voiceobs.server.storage.s3 import S3Storage

__all__ = [
    "AudioStorage",
    "AudioStorageProvider",
    "LocalFileStorage",
    "S3Storage",
]
