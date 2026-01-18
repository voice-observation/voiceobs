"""Phone agent verification implementation."""

import logging
from typing import Any

from voiceobs.server.services.agent_verification.base import AgentVerifier
from voiceobs.server.services.phone import PhoneService
from voiceobs.server.services.phone_factory import PhoneServiceFactory

logger = logging.getLogger(__name__)


class PhoneAgentVerifier(AgentVerifier):
    """Verifier for phone-based agents.

    Verifies that a phone number is reachable and can accept calls.
    Currently implements a basic validation, but can be extended to:
    - Make a test call to verify connectivity
    - Check if the number is active
    - Verify the agent responds correctly
    """

    def __init__(self) -> None:
        """Initialize the phone agent verifier."""
        # Initialize phone service using factory (provider-agnostic)
        self._phone_service: PhoneService | None = PhoneServiceFactory.create()
        if self._phone_service:
            logger.info("Initialized phone service for agent verification")
        else:
            logger.warning(
                "No phone service provider available. Phone verification will use format validation only."
            )

    async def verify(self, contact_info: dict[str, Any]) -> tuple[bool, str | None]:
        """Verify that a phone agent is reachable.

        Args:
            contact_info: Contact information dict containing "phone_number" key

        Returns:
            Tuple of (is_verified, error_message)
                - is_verified: True if phone number is valid and reachable
                - error_message: Error message if verification failed

        Raises:
            ValueError: If phone_number is missing from contact_info
        """
        phone_number = contact_info.get("phone_number")
        if not phone_number:
            raise ValueError("phone_number is required in contact_info for phone agents")

        # Basic validation: check phone number format (E.164 format)
        if not self._is_valid_phone_number(phone_number):
            return False, f"Invalid phone number format: {phone_number}. Expected E.164 format (e.g., +1234567890)"

        # If phone service is available, make an actual verification call
        if self._phone_service:
            try:
                logger.info(f"Making verification call to {phone_number}")
                # Make a verification call with a test message
                test_message = "This is a verification call. Please respond to confirm your agent is active."
                call_result = await self._phone_service.make_verification_call(
                    phone_number=phone_number,
                    timeout_seconds=30,
                    test_message=test_message,
                )

                if call_result.connected and call_result.answered and call_result.agent_responded:
                    logger.info(f"Phone verification successful for {phone_number}")
                    return True, None
                else:
                    error_msg = call_result.error_message or "Call not answered or agent did not respond"
                    logger.warning(f"Phone verification failed for {phone_number}: {error_msg}")
                    return False, error_msg

            except Exception as e:
                logger.error(f"Phone verification error for {phone_number}: {e}", exc_info=True)
                return False, f"Phone verification failed: {str(e)}"
        else:
            # Fallback: if phone service is not available, only validate format
            logger.info(f"Phone service not available. Only format validation performed for {phone_number}")
            return True, None

    def _is_valid_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format (E.164).

        Args:
            phone_number: Phone number to validate

        Returns:
            True if phone number format is valid (E.164), False otherwise
        """
        # E.164 format: +[country code][number] (max 15 digits total)
        if not phone_number.startswith("+"):
            return False

        # Remove the + and check if remaining characters are digits
        digits = phone_number[1:]
        if not digits.isdigit():
            return False

        # E.164 allows 1-15 digits after the +
        if len(digits) < 1 or len(digits) > 15:
            return False

        return True

    def get_agent_type(self) -> str:
        """Get the agent type this verifier handles.

        Returns:
            "phone"
        """
        return "phone"
