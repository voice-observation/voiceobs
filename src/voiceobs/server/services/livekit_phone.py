"""LiveKit phone service implementation."""

import asyncio
import logging
import os
from typing import Any

from livekit import api

from voiceobs.server.services.phone import CallResult, PhoneService

logger = logging.getLogger(__name__)


class LiveKitPhoneService(PhoneService):
    """LiveKit phone service provider implementation.

    Uses LiveKit SIP to make verification calls.
    Requires LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, and
    SIP_OUTBOUND_TRUNK_ID environment variables to be set.

    Example:
        >>> service = LiveKitPhoneService()
        >>> result = await service.make_verification_call("+1234567890")
        >>> if result.answered and result.agent_responded:
        ...     print("Agent verified!")
    """

    def __init__(self) -> None:
        """Initialize LiveKit phone service.

        Raises:
            ValueError: If required LiveKit credentials are not set
        """
        livekit_url = os.getenv("LIVEKIT_URL")
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        sip_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")

        if not livekit_url:
            raise ValueError("LIVEKIT_URL environment variable is required for LiveKit phone service")
        if not api_key:
            raise ValueError("LIVEKIT_API_KEY environment variable is required for LiveKit phone service")
        if not api_secret:
            raise ValueError("LIVEKIT_API_SECRET environment variable is required for LiveKit phone service")
        if not sip_trunk_id:
            raise ValueError("SIP_OUTBOUND_TRUNK_ID environment variable is required for LiveKit phone service")

        self._livekit_url = livekit_url
        self._api_key = api_key
        self._api_secret = api_secret
        self._sip_trunk_id = sip_trunk_id
        self._api_client = api.LiveKitAPI(url=livekit_url, api_key=api_key, api_secret=api_secret)

    async def make_verification_call(
        self,
        phone_number: str,
        timeout_seconds: int = 30,
        test_message: str | None = None,
    ) -> CallResult:
        """Make a verification call using LiveKit SIP.

        This implementation:
        1. Creates a LiveKit room
        2. Dispatches a call verifier agent job
        3. Waits for the call to be answered
        4. Verifies the agent responds

        Args:
            phone_number: Phone number to call (E.164 format, e.g., +1234567890)
            timeout_seconds: Maximum time to wait for call to be answered (default: 30)
            test_message: Optional test message to play. If provided, will verify
                         the agent responds to the message.

        Returns:
            CallResult with verification details

        Raises:
            ValueError: If phone_number format is invalid
            Exception: On LiveKit API errors
        """
        # Validate phone number format
        if not phone_number.startswith("+") or not phone_number[1:].isdigit():
            return CallResult(
                connected=False,
                answered=False,
                agent_responded=False,
                error_message=f"Invalid phone number format: {phone_number}. Expected E.164 format.",
            )

        try:
            # Import the call verifier agent helper functions
            import json

            from voiceobs.server.services.call_verifier_agent import (
                create_verification_room,
                wait_for_verification_result,
            )

            logger.info(f"Initiating verification call to {phone_number} via LiveKit")

            # Create a room for the verification call
            room_name = await create_verification_room(self._api_client)

            # Dispatch the call verifier agent job

            metadata = {
                "phone_number": phone_number,
                "test_message": test_message or "This is a verification call. Please respond to confirm your agent is active.",
            }
            job = await self._api_client.agent.dispatch_agent(
                api.DispatchAgentRequest(
                    agent_name="call-verifier",
                    room=room_name,
                    metadata=json.dumps(metadata),
                )
            )

            # Wait for verification result with timeout
            try:
                result = await asyncio.wait_for(
                    wait_for_verification_result(room_name, timeout_seconds),
                    timeout=timeout_seconds + 10,  # Add buffer for agent startup
                )

                return CallResult(
                    connected=result.get("connected", False),
                    answered=result.get("answered", False),
                    agent_responded=result.get("agent_responded", False),
                    duration_seconds=result.get("duration_seconds"),
                    error_message=result.get("error_message"),
                )

            except asyncio.TimeoutError:
                logger.warning(f"Verification call to {phone_number} timed out")
                return CallResult(
                    connected=True,
                    answered=False,
                    agent_responded=False,
                    error_message=f"Call verification timed out after {timeout_seconds} seconds",
                )

        except ImportError as e:
            logger.error(f"Failed to import call verifier agent: {e}")
            return CallResult(
                connected=False,
                answered=False,
                agent_responded=False,
                error_message=f"Call verifier agent not available: {str(e)}",
            )
        except Exception as e:
            logger.error(f"LiveKit verification call error: {e}", exc_info=True)
            return CallResult(
                connected=False,
                answered=False,
                agent_responded=False,
                error_message=f"LiveKit verification call failed: {str(e)}",
            )
