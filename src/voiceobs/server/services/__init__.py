"""Server services package."""

from voiceobs.server.services.deepgram_tts import DeepgramTTSService
from voiceobs.server.services.elevenlabs_tts import ElevenLabsTTSService
from voiceobs.server.services.openai_tts import OpenAITTSService
from voiceobs.server.services.tts import TTSService
from voiceobs.server.services.tts_factory import TTSServiceFactory

# Register TTS providers with factory
TTSServiceFactory.register_provider("openai", OpenAITTSService)
TTSServiceFactory.register_provider("deepgram", DeepgramTTSService)
TTSServiceFactory.register_provider("elevenlabs", ElevenLabsTTSService)

# LLM services
try:
    from voiceobs.server.services.gemini_llm import GeminiLLMService
    from voiceobs.server.services.llm import LLMService
    from voiceobs.server.services.llm_factory import LLMServiceFactory
    from voiceobs.server.services.openai_llm import OpenAILLMService

    # Register LLM providers with factory
    LLMServiceFactory.register_provider("openai", OpenAILLMService)
    LLMServiceFactory.register_provider("gemini", GeminiLLMService)

    __all__ = [
        "TTSService",
        "TTSServiceFactory",
        "OpenAITTSService",
        "DeepgramTTSService",
        "ElevenLabsTTSService",
        "LLMService",
        "LLMServiceFactory",
        "OpenAILLMService",
        "GeminiLLMService",
    ]
except ImportError:
    __all__ = [
        "TTSService",
        "TTSServiceFactory",
        "OpenAITTSService",
        "DeepgramTTSService",
        "ElevenLabsTTSService",
    ]
