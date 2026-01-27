"""Tests for LiveKit provider factory."""

from unittest.mock import MagicMock, patch

from voiceobs.server.services.agent_verification.livekit_providers import (
    LiveKitProviderFactory,
)


class TestLiveKitProviderFactory:
    """Tests for LiveKitProviderFactory."""

    def test_init_without_http_session(self):
        """Should initialize without HTTP session."""
        factory = LiveKitProviderFactory()
        assert factory._http_session is None

    def test_init_with_http_session(self):
        """Should initialize with HTTP session."""
        mock_session = MagicMock()
        factory = LiveKitProviderFactory(http_session=mock_session)
        assert factory._http_session is mock_session


class TestCreateLLM:
    """Tests for LLM provider creation."""

    @patch("voiceobs.server.services.agent_verification.livekit_providers.openai.LLM")
    def test_creates_llm_with_default_model(self, mock_llm_class):
        """Should create LLM with default model."""
        factory = LiveKitProviderFactory()
        factory.create_llm()

        mock_llm_class.assert_called_once_with(model="gpt-4o-mini")

    @patch("voiceobs.server.services.agent_verification.livekit_providers.openai.LLM")
    def test_creates_llm_with_custom_model(self, mock_llm_class):
        """Should create LLM with custom model."""
        factory = LiveKitProviderFactory()
        factory.create_llm(model="gpt-4o")

        mock_llm_class.assert_called_once_with(model="gpt-4o")

    @patch("voiceobs.server.services.agent_verification.livekit_providers.openai.LLM")
    def test_returns_llm_instance(self, mock_llm_class):
        """Should return the LLM instance."""
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm

        factory = LiveKitProviderFactory()
        result = factory.create_llm()

        assert result is mock_llm


class TestCreateTTS:
    """Tests for TTS provider creation."""

    @patch("voiceobs.server.services.agent_verification.livekit_providers.elevenlabs.TTS")
    def test_creates_tts_with_default_model(self, mock_tts_class):
        """Should create TTS with default model."""
        factory = LiveKitProviderFactory()
        factory.create_tts()

        mock_tts_class.assert_called_once_with(
            model="eleven_flash_v2_5",
            streaming_latency=3,
            http_session=None,
        )

    @patch("voiceobs.server.services.agent_verification.livekit_providers.elevenlabs.TTS")
    def test_creates_tts_with_custom_model(self, mock_tts_class):
        """Should create TTS with custom model."""
        factory = LiveKitProviderFactory()
        factory.create_tts(model="eleven_monolingual_v1")

        mock_tts_class.assert_called_once_with(
            model="eleven_monolingual_v1",
            streaming_latency=3,
            http_session=None,
        )

    @patch("voiceobs.server.services.agent_verification.livekit_providers.elevenlabs.TTS")
    def test_creates_tts_with_custom_latency(self, mock_tts_class):
        """Should create TTS with custom streaming latency."""
        factory = LiveKitProviderFactory()
        factory.create_tts(streaming_latency=1)

        mock_tts_class.assert_called_once_with(
            model="eleven_flash_v2_5",
            streaming_latency=1,
            http_session=None,
        )

    @patch("voiceobs.server.services.agent_verification.livekit_providers.elevenlabs.TTS")
    def test_creates_tts_with_http_session(self, mock_tts_class):
        """Should pass HTTP session to TTS."""
        mock_session = MagicMock()
        factory = LiveKitProviderFactory(http_session=mock_session)
        factory.create_tts()

        mock_tts_class.assert_called_once_with(
            model="eleven_flash_v2_5",
            streaming_latency=3,
            http_session=mock_session,
        )

    @patch("voiceobs.server.services.agent_verification.livekit_providers.elevenlabs.TTS")
    def test_returns_tts_instance(self, mock_tts_class):
        """Should return the TTS instance."""
        mock_tts = MagicMock()
        mock_tts_class.return_value = mock_tts

        factory = LiveKitProviderFactory()
        result = factory.create_tts()

        assert result is mock_tts


class TestCreateSTT:
    """Tests for STT provider creation."""

    @patch("voiceobs.server.services.agent_verification.livekit_providers.deepgram.STT")
    def test_creates_stt_with_defaults(self, mock_stt_class):
        """Should create STT with default settings."""
        factory = LiveKitProviderFactory()
        factory.create_stt()

        mock_stt_class.assert_called_once_with(
            http_session=None,
            interim_results=True,
        )

    @patch("voiceobs.server.services.agent_verification.livekit_providers.deepgram.STT")
    def test_creates_stt_without_interim_results(self, mock_stt_class):
        """Should create STT without interim results."""
        factory = LiveKitProviderFactory()
        factory.create_stt(interim_results=False)

        mock_stt_class.assert_called_once_with(
            http_session=None,
            interim_results=False,
        )

    @patch("voiceobs.server.services.agent_verification.livekit_providers.deepgram.STT")
    def test_creates_stt_with_http_session(self, mock_stt_class):
        """Should pass HTTP session to STT."""
        mock_session = MagicMock()
        factory = LiveKitProviderFactory(http_session=mock_session)
        factory.create_stt()

        mock_stt_class.assert_called_once_with(
            http_session=mock_session,
            interim_results=True,
        )

    @patch("voiceobs.server.services.agent_verification.livekit_providers.deepgram.STT")
    def test_returns_stt_instance(self, mock_stt_class):
        """Should return the STT instance."""
        mock_stt = MagicMock()
        mock_stt_class.return_value = mock_stt

        factory = LiveKitProviderFactory()
        result = factory.create_stt()

        assert result is mock_stt


class TestCreateAgentSession:
    """Tests for AgentSession creation."""

    @patch("voiceobs.server.services.agent_verification.livekit_providers.silero.VAD")
    @patch("voiceobs.server.services.agent_verification.livekit_providers.AgentSession")
    def test_creates_agent_session_with_providers(self, mock_agent_session, mock_vad):
        """Should create AgentSession with all providers."""
        mock_vad_instance = MagicMock()
        mock_vad.load.return_value = mock_vad_instance

        factory = LiveKitProviderFactory()

        # Mock the individual provider creation
        with (
            patch.object(factory, "create_llm") as mock_create_llm,
            patch.object(factory, "create_tts") as mock_create_tts,
            patch.object(factory, "create_stt") as mock_create_stt,
        ):
            mock_llm = MagicMock()
            mock_tts = MagicMock()
            mock_stt = MagicMock()
            mock_create_llm.return_value = mock_llm
            mock_create_tts.return_value = mock_tts
            mock_create_stt.return_value = mock_stt

            factory.create_agent_session()

            mock_agent_session.assert_called_once_with(
                vad=mock_vad_instance,
                stt=mock_stt,
                tts=mock_tts,
                llm=mock_llm,
            )

    @patch("voiceobs.server.services.agent_verification.livekit_providers.silero.VAD")
    @patch("voiceobs.server.services.agent_verification.livekit_providers.AgentSession")
    def test_returns_agent_session_instance(self, mock_agent_session, mock_vad):
        """Should return the AgentSession instance."""
        mock_session = MagicMock()
        mock_agent_session.return_value = mock_session

        factory = LiveKitProviderFactory()

        with (
            patch.object(factory, "create_llm"),
            patch.object(factory, "create_tts"),
            patch.object(factory, "create_stt"),
        ):
            result = factory.create_agent_session()

        assert result is mock_session
