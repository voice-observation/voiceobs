#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#
# Modified to include voiceobs instrumentation for voice turn tracing.
#

"""OpenAI Bot Implementation with voiceobs instrumentation.

This module implements a chatbot using OpenAI's GPT-4 model for natural language
processing, instrumented with voiceobs for voice turn observability.

The bot runs as part of a pipeline that processes audio/video frames and manages
the conversation flow, with each user and agent turn tracked as OpenTelemetry spans.
"""

import os

from dotenv import load_dotenv
from loguru import logger
from PIL import Image
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    Frame,
    LLMRunFrame,
    OutputImageRawFrame,
    SpriteFrame,
    TranscriptionFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.daily.transport import DailyParams, DailyTransport

# voiceobs imports
from voiceobs import ensure_tracing_initialized, voice_conversation, voice_turn

load_dotenv(override=True)

# Initialize voiceobs tracing (uses ConsoleSpanExporter by default)
ensure_tracing_initialized()
logger.info("voiceobs tracing initialized")

sprites = []
script_dir = os.path.dirname(__file__)
assets_dir = os.path.join(script_dir, "simple-chatbot/server/assets")

# Load sequential animation frames
for i in range(1, 26):
    full_path = os.path.join(assets_dir, f"robot0{i}.png")
    with Image.open(full_path) as img:
        sprites.append(OutputImageRawFrame(image=img.tobytes(), size=img.size, format=img.format))

# Create a smooth animation by adding reversed frames
flipped = sprites[::-1]
sprites.extend(flipped)

# Define static and animated states
quiet_frame = sprites[0]
talking_frame = SpriteFrame(images=sprites)


class TalkingAnimation(FrameProcessor):
    """Manages the bot's visual animation states."""

    def __init__(self):
        super().__init__()
        self._is_talking = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, BotStartedSpeakingFrame):
            if not self._is_talking:
                await self.push_frame(talking_frame)
                self._is_talking = True
        elif isinstance(frame, BotStoppedSpeakingFrame):
            await self.push_frame(quiet_frame)
            self._is_talking = False

        await self.push_frame(frame, direction)


class VoiceObsUserTurnTracker(FrameProcessor):
    """Tracks user turns using voiceobs.

    Creates a voice.turn span for each user utterance detected via transcription.
    """

    def __init__(self):
        super().__init__()
        self._user_turn_context = None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        # Track user turns when we receive transcription
        if isinstance(frame, TranscriptionFrame):
            # End previous user turn if any
            if self._user_turn_context:
                self._user_turn_context.__exit__(None, None, None)
                self._user_turn_context = None

            # Start new user turn
            self._user_turn_context = voice_turn("user")
            self._user_turn_context.__enter__()
            logger.debug(f"voiceobs: User turn started - '{frame.text[:50]}...'")

        await self.push_frame(frame, direction)


class VoiceObsAgentTurnTracker(FrameProcessor):
    """Tracks agent turns using voiceobs.

    Creates a voice.turn span for each agent response (speaking period).
    """

    def __init__(self):
        super().__init__()
        self._agent_turn_context = None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, BotStartedSpeakingFrame):
            # Start agent turn
            if not self._agent_turn_context:
                self._agent_turn_context = voice_turn("agent")
                self._agent_turn_context.__enter__()
                logger.debug("voiceobs: Agent turn started")

        elif isinstance(frame, BotStoppedSpeakingFrame):
            # End agent turn
            if self._agent_turn_context:
                self._agent_turn_context.__exit__(None, None, None)
                self._agent_turn_context = None
                logger.debug("voiceobs: Agent turn ended")

        await self.push_frame(frame, direction)


async def run_bot(transport: BaseTransport):
    """Main bot execution function with voiceobs instrumentation."""

    tts = ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY", ""),
        voice_id="pNInz6obpgDQGcFmaJgB",
    )

    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY", ""))

    messages = [
        {
            "role": "system",
            "content": "You are Chatbot, a friendly, helpful robot. Your goal is to demonstrate your capabilities in a succinct way. Your output will be converted to audio so don't include special characters in your answers. Respond to what the user said in a creative and helpful way, but keep your responses brief. Start by introducing yourself.",
        },
    ]

    context = LLMContext(messages)
    context_aggregator = LLMContextAggregatorPair(context)

    ta = TalkingAnimation()
    user_tracker = VoiceObsUserTurnTracker()
    agent_tracker = VoiceObsAgentTurnTracker()

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # Pipeline with voiceobs trackers inserted
    pipeline = Pipeline(
        [
            transport.input(),
            user_tracker,  # Track user turns from transcription
            rtvi,
            context_aggregator.user(),
            llm,
            tts,
            agent_tracker,  # Track agent turns from speaking frames
            ta,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )
    await task.queue_frame(quiet_frame)

    # Use voiceobs to wrap the entire conversation
    conversation_ctx = voice_conversation()
    conv = conversation_ctx.__enter__()
    logger.info(f"voiceobs: Conversation started - {conv.conversation_id}")

    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        await rtvi.set_bot_ready()
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, participant):
        logger.info("Client connected")
        await transport.capture_participant_transcription(participant["id"])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        # End the conversation context
        conversation_ctx.__exit__(None, None, None)
        logger.info(f"voiceobs: Conversation ended - {conv.conversation_id}")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)

    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud."""

    transport = DailyTransport(
        runner_args.room_url,
        runner_args.token,
        "Pipecat Bot",
        params=DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            video_out_enabled=True,
            video_out_width=1024,
            video_out_height=576,
            vad_analyzer=SileroVADAnalyzer(),
            transcription_enabled=True,
        ),
    )

    await run_bot(transport)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
