"""Base class for agent verification strategies."""

from abc import ABC, abstractmethod
from typing import Any


class AgentVerifier(ABC):
    """Abstract base class for agent verification strategies.

    Each agent type (phone, web, etc.) should have its own verifier implementation
    that inherits from this class and implements the verify method.
    """

    @abstractmethod
    async def verify(
        self, contact_info: dict[str, Any]
    ) -> tuple[bool, str | None, list[dict[str, str]] | None]:
        """Verify that an agent is reachable and responsive.

        Args:
            contact_info: Contact information dictionary containing agent-specific
                         contact details (e.g., {"phone_number": "..."} for phone agents,
                         {"web_url": "..."} for web agents)

        Returns:
            Tuple of (is_verified, error_message, transcript)
                - is_verified: True if agent is verified, False otherwise
                - error_message: Error message if verification failed, None if successful
                - transcript: Conversation transcript from verification, None if not available

        Raises:
            ValueError: If contact_info is missing required fields
            Exception: Provider-specific errors during verification
        """
        pass

    @abstractmethod
    def get_agent_type(self) -> str:
        """Get the agent type this verifier handles.

        Returns:
            Agent type identifier (e.g., "phone", "web")
        """
        pass
