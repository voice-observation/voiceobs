"""Test version information."""

from voiceobs import __version__


def test_version():
    """Test that version is set correctly."""
    assert __version__ == "0.0.1"
