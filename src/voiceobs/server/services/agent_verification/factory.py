"""Factory for creating agent verifier instances."""

from voiceobs.server.services.agent_verification.base import AgentVerifier


class AgentVerifierFactory:
    """Factory for creating agent verifier instances based on agent type.

    This factory manages the registration and creation of agent verifier strategies.
    Verifiers can be registered dynamically using register_verifier().

    Example:
        >>> AgentVerifierFactory.register_verifier("phone", PhoneAgentVerifier)
        >>> verifier = AgentVerifierFactory.create("phone")
        >>> is_verified, error = await verifier.verify({"phone_number": "+1234567890"})
    """

    _verifiers: dict[str, type[AgentVerifier]] = {}

    @classmethod
    def create(cls, agent_type: str) -> AgentVerifier:
        """Create an agent verifier instance for the specified agent type.

        Args:
            agent_type: Agent type identifier (e.g., "phone", "web")

        Returns:
            AgentVerifier instance for the specified agent type

        Raises:
            ValueError: If agent_type is not supported
        """
        agent_type_lower = agent_type.lower()
        verifier_class = cls._verifiers.get(agent_type_lower)

        if verifier_class is None:
            supported = ", ".join(cls._verifiers.keys())
            raise ValueError(
                f"Unsupported agent type: {agent_type}. Supported types: {supported}"
            )

        return verifier_class()

    @classmethod
    def register_verifier(cls, agent_type: str, verifier_class: type[AgentVerifier]) -> None:
        """Register a new agent verifier.

        Args:
            agent_type: Unique identifier for the agent type (case-insensitive)
            verifier_class: AgentVerifier subclass implementation
        """
        cls._verifiers[agent_type.lower()] = verifier_class

    @classmethod
    def list_verifiers(cls) -> list[str]:
        """List all registered agent type identifiers.

        Returns:
            List of registered agent type identifiers
        """
        return list(cls._verifiers.keys())
