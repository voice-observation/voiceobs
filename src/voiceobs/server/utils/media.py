"""Media-related utility functions."""


def get_extension_from_content_type(content_type: str | None) -> str:
    """Get file extension from content type.

    Args:
        content_type: MIME type of the audio.

    Returns:
        File extension (e.g., ".mp3", ".wav").
    """
    if content_type == "audio/mpeg" or content_type == "audio/mp3":
        return ".mp3"
    if content_type == "audio/wav":
        return ".wav"
    if content_type == "audio/ogg":
        return ".ogg"
    if content_type == "audio/flac":
        return ".flac"
    return ".wav"
