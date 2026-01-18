"""Factory for creating phone service instances."""

import logging
import os

from voiceobs.server.services.phone import PhoneService

logger = logging.getLogger(__name__)


class PhoneServiceFactory:
    """Factory for creating phone service instances based on provider.

    This factory manages the registration and creation of phone service providers.
    Providers can be registered dynamically using register_provider().

    Example:
        >>> PhoneServiceFactory.register_provider("livekit", LiveKitPhoneService)
        >>> service = PhoneServiceFactory.create()  # Auto-detects provider
        >>> result = await service.make_verification_call("+1234567890")
    """

    _providers: dict[str, type[PhoneService]] = {}

    @classmethod
    def create(cls, provider: str | None = None) -> PhoneService | None:
        """Create a phone service instance.

        Args:
            provider: Optional provider identifier. If not provided, auto-detects
                     based on available credentials (currently supports LiveKit).

        Returns:
            PhoneService instance for the specified or auto-detected provider,
            or None if no provider is available

        Raises:
            ValueError: If provider is specified but not supported
        """
        if provider:
            provider_lower = provider.lower()
            service_class = cls._providers.get(provider_lower)

            if service_class is None:
                supported = ", ".join(cls._providers.keys())
                raise ValueError(
                    f"Unsupported phone provider: {provider}. Supported providers: {supported}"
                )

            try:
                return service_class()
            except ValueError as e:
                logger.warning(f"Failed to create {provider} phone service: {e}")
                return None

        # Auto-detect provider based on available credentials
        # Currently supports LiveKit
        if all(
            os.getenv(key)
            for key in [
                "LIVEKIT_URL",
                "LIVEKIT_API_KEY",
                "LIVEKIT_API_SECRET",
                "SIP_OUTBOUND_TRUNK_ID",
            ]
        ):
            service_class = cls._providers.get("livekit")
            if service_class:
                try:
                    return service_class()
                except ValueError as e:
                    logger.warning(f"Failed to create LiveKit phone service: {e}")
                    return None

        # No provider available
        return None

    @classmethod
    def register_provider(cls, provider_id: str, service_class: type[PhoneService]) -> None:
        """Register a new phone service provider.

        Args:
            provider_id: Unique identifier for the provider (case-insensitive)
            service_class: PhoneService subclass implementation
        """
        cls._providers[provider_id.lower()] = service_class

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider IDs.

        Returns:
            List of registered provider identifiers
        """
        return list(cls._providers.keys())
