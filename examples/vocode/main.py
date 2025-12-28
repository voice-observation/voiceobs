"""Vocode Streaming Conversation with voiceobs instrumentation.

This example adapts the Vocode quickstart to use voiceobs annotations
for observability of the voice pipeline:
  - Deepgram for ASR (speech-to-text)
  - OpenAI GPT for LLM (conversation)
  - Deepgram for TTS (text-to-speech)

Usage:
    1. Copy .env.example to .env and fill in your API keys
    2. Run: uv sync
    3. Run: uv run python main.py
    4. After conversation: uv run voiceobs analyze --input voiceobs_traces.jsonl
"""

import asyncio
import io
import signal

from pydantic_settings import BaseSettings, SettingsConfigDict
from deepgram import DeepgramClient

from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.logging import configure_pretty_logging
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.audio import AudioEncoding
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.synthesizer import SynthesizerConfig
from vocode.streaming.models.transcriber import (
    DeepgramTranscriberConfig,
    PunctuationEndpointingConfig,
)
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.streaming.synthesizer.base_synthesizer import BaseSynthesizer, SynthesisResult
from vocode.streaming.transcriber.deepgram_transcriber import DeepgramTranscriber

from voiceobs import ensure_tracing_initialized, voice_conversation, mark_speech_end, mark_speech_start
from voiceobs.decorators import voice_stage_decorator, voice_turn_decorator

configure_pretty_logging()


class Settings(BaseSettings):
    """Settings for the streaming conversation with voiceobs."""

    openai_api_key: str = "ENTER_YOUR_OPENAI_API_KEY_HERE"
    deepgram_api_key: str = "ENTER_YOUR_DEEPGRAM_API_KEY_HERE"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


# Custom Deepgram TTS Synthesizer Config
class DeepgramSynthesizerConfig(SynthesizerConfig, type="synthesizer_deepgram"):
    api_key: str
    model: str = "aura-2-thalia-en"


# Custom Deepgram TTS Synthesizer
class DeepgramSynthesizer(BaseSynthesizer[DeepgramSynthesizerConfig]):
    """Deepgram TTS Synthesizer for Vocode."""

    def __init__(self, synthesizer_config: DeepgramSynthesizerConfig):
        super().__init__(synthesizer_config)
        self.client = DeepgramClient(api_key=synthesizer_config.api_key)
        self.model = synthesizer_config.model
        self.words_per_minute = 150

    @classmethod
    def get_voice_identifier(cls, synthesizer_config: DeepgramSynthesizerConfig) -> str:
        return f"deepgram-{synthesizer_config.model}"

    async def create_speech_uncached(
        self,
        message: BaseMessage,
        chunk_size: int,
        is_first_text_chunk: bool = False,
        is_sole_text_chunk: bool = False,
    ) -> SynthesisResult:
        self.total_chars += len(message.text)

        # Use Deepgram TTS API (v6 SDK)
        response = self.client.speak.v1.audio.generate(
            text=message.text,
            model=self.model,
            encoding="linear16",
            sample_rate=self.synthesizer_config.sampling_rate,
            container="wav",
        )

        # Read audio data from response iterator
        audio_data = b"".join(response)

        # Create synthesis result from WAV audio
        return self.create_synthesis_result_from_wav(
            synthesizer_config=self.synthesizer_config,
            file=io.BytesIO(audio_data),
            message=message,
            chunk_size=chunk_size,
        )


# Decorated helper functions for voiceobs instrumentation
@voice_turn_decorator(actor="user")
@voice_stage_decorator(stage="asr", provider="deepgram", model="nova-2")
def record_user_turn(transcript: str) -> str:
    """Record a user turn with ASR stage instrumentation."""
    mark_speech_end()
    return transcript


# Instrumented Transcriber with voiceobs ASR stage annotation
class InstrumentedDeepgramTranscriber(DeepgramTranscriber):
    """DeepgramTranscriber with voiceobs ASR instrumentation."""

    def is_endpoint(self, current_buffer, deepgram_response, time_silent):
        """Check if user finished speaking and record user turn."""
        result = super().is_endpoint(current_buffer, deepgram_response, time_silent)
        if result and current_buffer:
            # User finished speaking - record user turn with ASR stage
            record_user_turn(current_buffer)
        return result


# Note: ChatGPTAgent.generate_response is an async generator, so we can't use
# the voice_stage_decorator on it directly. The LLM calls happen inside the
# generator. For full LLM instrumentation, you would need to patch the OpenAI
# client calls directly or use OpenTelemetry's openai instrumentation.


# Decorated helper for agent turn with TTS stage
@voice_turn_decorator(actor="agent")
@voice_stage_decorator(stage="tts", provider="deepgram", model="aura-2-thalia-en")
async def record_agent_turn(synthesizer, message, chunk_size, is_first_text_chunk, is_sole_text_chunk):
    """Record an agent turn with TTS stage instrumentation."""
    mark_speech_start()
    # Call the parent class method directly
    return await DeepgramSynthesizer.create_speech_uncached(
        synthesizer, message, chunk_size, is_first_text_chunk, is_sole_text_chunk
    )


# Instrumented Synthesizer with voiceobs TTS stage annotation
class InstrumentedDeepgramSynthesizer(DeepgramSynthesizer):
    """DeepgramSynthesizer with voiceobs TTS instrumentation."""

    async def create_speech_uncached(self, message, chunk_size, is_first_text_chunk=False, is_sole_text_chunk=False):
        """Instrumented speech synthesis with agent turn tracking."""
        return await record_agent_turn(self, message, chunk_size, is_first_text_chunk, is_sole_text_chunk)


async def main():
    # Initialize voiceobs tracing
    ensure_tracing_initialized()

    (
        microphone_input,
        speaker_output,
    ) = create_streaming_microphone_input_and_speaker_output(
        use_default_devices=False,
    )

    # Wrap entire conversation in voiceobs conversation context
    with voice_conversation() as conv:
        print(f"Conversation ID: {conv.conversation_id}")

        conversation = StreamingConversation(
            output_device=speaker_output,
            transcriber=InstrumentedDeepgramTranscriber(
                DeepgramTranscriberConfig.from_input_device(
                    microphone_input,
                    endpointing_config=PunctuationEndpointingConfig(),
                    api_key=settings.deepgram_api_key,
                ),
            ),
            agent=ChatGPTAgent(
                ChatGPTAgentConfig(
                    openai_api_key=settings.openai_api_key,
                    initial_message=BaseMessage(text="What up"),
                    prompt_preamble="""The AI is having a pleasant conversation about life""",
                )
            ),
            synthesizer=InstrumentedDeepgramSynthesizer(
                DeepgramSynthesizerConfig.from_output_device(
                    speaker_output,
                    api_key=settings.deepgram_api_key,
                ),
            ),
        )

        await conversation.start()
        print("Conversation started, press Ctrl+C to end")

        signal.signal(
            signal.SIGINT,
            lambda _0, _1: asyncio.create_task(conversation.terminate()),
        )

        while conversation.is_active():
            chunk = await microphone_input.get_audio()
            conversation.receive_audio(chunk)

    print("\nConversation ended.")
    print("To analyze traces: uv run voiceobs analyze --input voiceobs_traces.jsonl")


if __name__ == "__main__":
    asyncio.run(main())
