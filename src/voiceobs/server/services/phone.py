"""Phone service abstraction for making phone calls."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CallResult:
    """Result of a phone call verification attempt."""

    connected: bool
    """Whether the call was successfully connected."""
    answered: bool
    """Whether the call was answered."""
    agent_responded: bool
    """Whether the agent responded (e.g., played greeting or responded to test message)."""
    duration_seconds: float | None = None
    """Duration of the call in seconds, if available."""
    error_message: str | None = None
    """Error message if the call failed."""


class PhoneService(ABC):
    """Abstract base class for phone service providers.

    All phone service provider implementations must inherit from this class
    and implement the make_verification_call method.
    """

    @abstractmethod
    async def make_verification_call(
        self,
        phone_number: str,
        timeout_seconds: int = 30,
        test_message: str | None = None,
    ) -> CallResult:
        """Make a verification call to a phone number.

        This method should:
        1. Initiate a call to the phone number
        2. Wait for the call to be answered
        3. Optionally play a test message and wait for response
        4. Return the result of the verification

        Args:
            phone_number: Phone number to call (E.164 format)
            timeout_seconds: Maximum time to wait for call to be answered
            test_message: Optional test message to play and verify response

        Returns:
            CallResult with verification details

        Raises:
            ValueError: If phone_number format is invalid
            Exception: Provider-specific errors during the call
        """
        pass
