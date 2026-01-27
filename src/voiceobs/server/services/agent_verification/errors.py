"""Custom exceptions for verification failures."""


class VerificationError(Exception):
    """Base error for verification failures."""

    pass


class CallNotAnsweredError(VerificationError):
    """Target didn't pick up within timeout."""

    pass


class CallDisconnectedError(VerificationError):
    """Call dropped unexpectedly during conversation."""

    pass


class ProviderError(VerificationError):
    """Error with LLM/TTS/STT provider."""

    pass
