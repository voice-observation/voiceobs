"""Factory for creating TTS service instances."""

from voiceobs.server.services.tts import TTSService


class TTSServiceFactory:
    """Factory for creating TTS service instances based on provider.

    This factory manages the registration and creation of TTS service providers.
    Providers can be registered dynamically using register_provider().

    Example:
        >>> TTSServiceFactory.register_provider("openai", OpenAITTSService)
        >>> service = TTSServiceFactory.create("openai")
        >>> audio, mime, duration = await service.synthesize("Hello", {})
    """

    _providers: dict[str, type[TTSService]] = {}

    @classmethod
    def create(cls, provider: str) -> TTSService:
        """Create a TTS service instance for the specified provider.

        Args:
            provider: TTS provider identifier (case-insensitive)

        Returns:
            TTSService instance for the specified provider

        Raises:
            ValueError: If provider is not supported
        """
        provider_lower = provider.lower()
        service_class = cls._providers.get(provider_lower)

        if service_class is None:
            supported = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unsupported TTS provider: {provider}. "
                f"Supported providers: {supported}"
            )

        return service_class()

    @classmethod
    def register_provider(
        cls, provider_id: str, service_class: type[TTSService]
    ) -> None:
        """Register a new TTS provider.

        Args:
            provider_id: Unique identifier for the provider (case-insensitive)
            service_class: TTSService subclass implementation
        """
        cls._providers[provider_id.lower()] = service_class

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider IDs.

        Returns:
            List of registered provider identifiers
        """
        return list(cls._providers.keys())
