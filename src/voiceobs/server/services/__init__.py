"""Server services package."""

from voiceobs.server.services.agent_verification import (
    AgentVerificationService,
    AgentVerifierFactory,
)
from voiceobs.server.services.deepgram_tts import DeepgramTTSService
from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService
from voiceobs.server.services.openai_tts import OpenAITTSService
from voiceobs.server.services.phone import PhoneService
from voiceobs.server.services.phone_factory import PhoneServiceFactory
from voiceobs.server.services.tts import TTSService
from voiceobs.server.services.tts_factory import TTSServiceFactory

# Register TTS providers with factory
TTSServiceFactory.register_provider("openai", OpenAITTSService)
TTSServiceFactory.register_provider("deepgram", DeepgramTTSService)
TTSServiceFactory.register_provider("elevenlabs", ElevenLabsTTSService)

# Initialize __all__ with base exports
__all__ = [
    "TTSService",
    "TTSServiceFactory",
    "OpenAITTSService",
    "DeepgramTTSService",
    "ElevenLabsTTSService",
    "AgentVerificationService",
    "AgentVerifierFactory",
    "PhoneService",
    "PhoneServiceFactory",
]

# Register phone service providers with factory
# Try to import LiveKit phone service (may not be available if livekit-agents not installed)
try:
    from voiceobs.server.services.livekit_phone import LiveKitPhoneService

    PhoneServiceFactory.register_provider("livekit", LiveKitPhoneService)
    __all__.append("LiveKitPhoneService")
except ImportError:
    pass  # LiveKit not available

# LLM services
try:
    from voiceobs.server.services.gemini_llm import GeminiLLMService
    from voiceobs.server.services.llm import LLMService
    from voiceobs.server.services.llm_factory import LLMServiceFactory
    from voiceobs.server.services.openai_llm import OpenAILLMService

    # Register LLM providers with factory
    LLMServiceFactory.register_provider("openai", OpenAILLMService)
    LLMServiceFactory.register_provider("gemini", GeminiLLMService)

    # Add LLM services to __all__
    __all__.extend(["LLMService", "LLMServiceFactory", "OpenAILLMService", "GeminiLLMService"])
except ImportError:
    pass  # LLM services not available
