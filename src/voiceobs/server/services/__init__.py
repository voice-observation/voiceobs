"""Server services package."""

from voiceobs.server.services.deepgram_tts import DeepgramTTSService
from voiceobs.server.services.openai_tts import OpenAITTSService
from voiceobs.server.services.tts import TTSService
from voiceobs.server.services.tts_factory import TTSServiceFactory

# Register providers with factory
TTSServiceFactory.register_provider("openai", OpenAITTSService)
TTSServiceFactory.register_provider("deepgram", DeepgramTTSService)

__all__ = ["TTSService", "TTSServiceFactory", "OpenAITTSService", "DeepgramTTSService"]
