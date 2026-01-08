"""Tests for audio storage utility functions."""

from voiceobs.server.storage import get_extension_from_content_type


class TestGetExtensionFromContentType:
    """Tests for get_extension_from_content_type utility function."""

    def test_audio_mpeg_returns_mp3(self):
        """Test that audio/mpeg returns .mp3 extension."""
        assert get_extension_from_content_type("audio/mpeg") == ".mp3"

    def test_audio_mp3_returns_mp3(self):
        """Test that audio/mp3 returns .mp3 extension."""
        assert get_extension_from_content_type("audio/mp3") == ".mp3"

    def test_audio_wav_returns_wav(self):
        """Test that audio/wav returns .wav extension."""
        assert get_extension_from_content_type("audio/wav") == ".wav"

    def test_audio_ogg_returns_ogg(self):
        """Test that audio/ogg returns .ogg extension."""
        assert get_extension_from_content_type("audio/ogg") == ".ogg"

    def test_audio_flac_returns_flac(self):
        """Test that audio/flac returns .flac extension."""
        assert get_extension_from_content_type("audio/flac") == ".flac"

    def test_none_returns_wav_default(self):
        """Test that None returns .wav as default."""
        assert get_extension_from_content_type(None) == ".wav"

    def test_unknown_type_returns_wav_default(self):
        """Test that unknown content type returns .wav as default."""
        assert get_extension_from_content_type("audio/unknown") == ".wav"
        assert get_extension_from_content_type("video/mp4") == ".wav"
        assert get_extension_from_content_type("text/plain") == ".wav"
