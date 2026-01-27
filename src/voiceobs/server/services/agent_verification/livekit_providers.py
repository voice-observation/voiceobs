"""Factory for creating LiveKit agent providers."""

from __future__ import annotations

from typing import Any

import aiohttp
from livekit.agents import AgentSession
from livekit.plugins import deepgram, elevenlabs, openai, silero

from voiceobs.server.services.agent_verification.constants import (
    DEFAULT_LLM_MODEL,
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_STREAMING_LATENCY,
)


class LiveKitProviderFactory:
    """Factory for creating LiveKit agent providers (LLM, TTS, STT).

    This factory encapsulates the creation of providers used by LiveKit agents,
    allowing for easy configuration and reuse across different agent types.

    Args:
        http_session: Optional aiohttp session to share across providers

    Examples:
        >>> async with aiohttp.ClientSession() as session:
        ...     factory = LiveKitProviderFactory(http_session=session)
        ...     agent_session = factory.create_agent_session()
    """

    def __init__(self, http_session: aiohttp.ClientSession | None = None) -> None:
        """Initialize the provider factory.

        Args:
            http_session: Optional aiohttp session to share across providers
        """
        self._http_session = http_session

    def create_llm(self, model: str = DEFAULT_LLM_MODEL) -> Any:
        """Create LLM provider for LiveKit agents.

        Uses OpenAI's gpt-4o-mini by default, which is sufficient for
        simple verification conversations and significantly faster than gpt-4o.

        Args:
            model: Model identifier to use (default: gpt-4o-mini)

        Returns:
            LLM provider instance
        """
        return openai.LLM(model=model)

    def create_tts(
        self,
        model: str = DEFAULT_TTS_MODEL,
        streaming_latency: int = DEFAULT_TTS_STREAMING_LATENCY,
    ) -> Any:
        """Create TTS provider for LiveKit agents.

        Uses ElevenLabs with turbo model and optimized streaming latency
        for fastest time-to-first-audio.

        Args:
            model: Model identifier to use (default: eleven_flash_v2_5)
            streaming_latency: Streaming latency setting (0-4, default: 3)

        Returns:
            TTS provider instance
        """
        return elevenlabs.TTS(
            model=model,
            streaming_latency=streaming_latency,
            http_session=self._http_session,
        )

    def create_stt(self, interim_results: bool = True) -> Any:
        """Create STT provider for LiveKit agents.

        Uses Deepgram with interim results enabled for faster
        response initiation.

        Args:
            interim_results: Enable interim transcription results (default: True)

        Returns:
            STT provider instance
        """
        return deepgram.STT(
            http_session=self._http_session,
            interim_results=interim_results,
        )

    def create_agent_session(self) -> AgentSession:
        """Create a fully configured AgentSession with all providers.

        Returns:
            Configured AgentSession instance ready for use
        """
        return AgentSession(
            vad=silero.VAD.load(),
            stt=self.create_stt(),
            tts=self.create_tts(),
            llm=self.create_llm(),
        )
