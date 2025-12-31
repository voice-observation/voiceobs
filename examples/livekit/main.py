"""LiveKit Voice Agent with voiceobs instrumentation.

Usage:
    1. Copy .env.example to .env and fill in your API keys
    2. Run: uv sync
    3. Run: uv run python main.py dev
"""

from dotenv import load_dotenv

load_dotenv()

from livekit import agents, rtc
from livekit.agents import Agent, AgentServer, AgentSession, room_io
from livekit.plugins import deepgram, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
# from livekit.agents.voice import VoicePipelineAgent
# from livekit.plugins import deepgram, openai, silero
from voiceobs import ensure_tracing_initialized
from voiceobs.integrations import instrument_livekit_session


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.""",
        )


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: agents.JobContext):
    """Main entrypoint for the voice agent."""
    ensure_tracing_initialized()

    session = AgentSession(
        stt=deepgram.STT(),
        llm="openai/gpt-4.1-mini",
        tts=openai.TTS(),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    # Instrument the session for voiceobs tracing
    instrumented_session = instrument_livekit_session(session)

    await instrumented_session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
                if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                else noise_cancellation.BVC(),
            ),
        ),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance.",
    )

    # await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # agent = VoicePipelineAgent(
    #     vad=silero.VAD.load(),
    #     stt=deepgram.STT(),
    #     llm=openai.LLM(),
    #     tts=openai.TTS(),
    # )

    # instrumented_agent = instrument_livekit_agent(agent)
    # instrumented_agent.start(ctx.room)

    # print(f"Voice agent started with voiceobs instrumentation")
    # print(f"Conversation ID: {instrumented_agent.conversation.conversation_id}")


if __name__ == "__main__":
    agents.cli.run_app(server)
