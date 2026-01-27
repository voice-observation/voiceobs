"""Tests for agent verification error classes."""

from voiceobs.server.services.agent_verification.errors import (
    CallDisconnectedError,
    CallNotAnsweredError,
    ProviderError,
    VerificationError,
)


class TestVerificationErrors:
    """Tests for verification error hierarchy."""

    def test_verification_error_is_exception(self):
        """Test VerificationError is an Exception."""
        error = VerificationError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_call_not_answered_error_inherits_verification_error(self):
        """Test CallNotAnsweredError inherits from VerificationError."""
        error = CallNotAnsweredError("no answer")
        assert isinstance(error, VerificationError)
        assert isinstance(error, Exception)

    def test_call_disconnected_error_inherits_verification_error(self):
        """Test CallDisconnectedError inherits from VerificationError."""
        error = CallDisconnectedError("disconnected")
        assert isinstance(error, VerificationError)

    def test_provider_error_inherits_verification_error(self):
        """Test ProviderError inherits from VerificationError."""
        error = ProviderError("provider failed")
        assert isinstance(error, VerificationError)
