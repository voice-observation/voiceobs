"""LiveKit call verifier agent for verifying phone agent connections."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from livekit import api, rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RoomInputOptions,
    RunContext,
    cli,
    WorkerOptions,
    function_tool,
    get_job_context,
)
from livekit.plugins import deepgram, openai, silero
from livekit.plugins.turn_detector.english import EnglishModel

logger = logging.getLogger("call-verifier")
logger.setLevel(logging.INFO)

# Store verification results by room name
_verification_results: dict[str, dict[str, Any]] = {}
_verification_events: dict[str, asyncio.Event] = {}


class CallVerifierAgent(Agent):
    """Agent for verifying phone agent connections.

    This agent makes a call to verify that:
    1. The phone number is reachable
    2. The call is answered
    3. The agent responds to a test message
    """

    def __init__(
        self,
        *,
        phone_number: str,
        test_message: str,
    ):
        super().__init__(
            instructions=f"""
            You are a call verification agent. Your job is to verify that a phone agent is reachable and responsive.
            
            You will call the phone number {phone_number} and play the following test message:
            "{test_message}"
            
            After playing the message, wait briefly for a response. If you hear a response or greeting,
            use the call_answered tool to confirm the verification. If the call is not answered or goes to voicemail,
            use the call_failed tool.
            
            Keep the call brief - your goal is just to verify connectivity, not have a full conversation.
            """
        )
        self.phone_number = phone_number
        self.test_message = test_message
        self.participant: rtc.RemoteParticipant | None = None
        self.call_answered = False
        self.agent_responded = False
        self.call_start_time: float | None = None
        self.call_end_time: float | None = None

    def set_participant(self, participant: rtc.RemoteParticipant):
        """Set the SIP participant for the call."""
        self.participant = participant

    async def hangup(self, job_ctx: JobContext | None = None):
        """Hang up the call by deleting the room."""
        if job_ctx is None:
            job_ctx = get_job_context()
        if job_ctx:
            try:
                await job_ctx.api.room.delete_room(
                    api.DeleteRoomRequest(room=job_ctx.room.name)
                )
            except Exception as e:
                logger.error(f"Error deleting room: {e}")

    @function_tool()
    async def call_answered(self, ctx: RunContext):
        """Called when the call is answered and agent responds."""
        logger.info(f"Call answered and agent responded for {self.phone_number}")
        self.call_answered = True
        self.agent_responded = True
        self.call_end_time = asyncio.get_event_loop().time()
        job_ctx = get_job_context()
        await self._record_result(job_ctx, connected=True, answered=True, agent_responded=True)
        await self.hangup(job_ctx)

    @function_tool()
    async def call_failed(self, ctx: RunContext, reason: str):
        """Called when the call fails or is not answered.
        
        Args:
            reason: Reason for call failure (e.g., "no-answer", "voicemail", "busy")
        """
        logger.info(f"Call failed for {self.phone_number}: {reason}")
        self.call_answered = False
        self.agent_responded = False
        self.call_end_time = asyncio.get_event_loop().time()
        job_ctx = get_job_context()
        await self._record_result(
            job_ctx,
            connected=True,
            answered=False,
            agent_responded=False,
            error_message=reason,
        )
        await self.hangup(job_ctx)

    async def _record_result(
        self,
        job_ctx: JobContext | None,
        connected: bool,
        answered: bool,
        agent_responded: bool,
        error_message: str | None = None,
    ):
        """Record the verification result."""
        if job_ctx is None:
            job_ctx = get_job_context()
        
        if job_ctx:
            room_name = job_ctx.room.name
            duration = None
            if self.call_start_time and self.call_end_time:
                duration = self.call_end_time - self.call_start_time

            _verification_results[room_name] = {
                "connected": connected,
                "answered": answered,
                "agent_responded": agent_responded,
                "duration_seconds": duration,
                "error_message": error_message,
            }

            # Signal that result is ready
            if room_name in _verification_events:
                _verification_events[room_name].set()


async def entrypoint(ctx: JobContext):
    """Entrypoint for the call verifier agent job."""
    logger.info(f"Connecting to room {ctx.room.name} for verification call")
    await ctx.connect()

    # Parse metadata to get phone number and test message
    metadata = json.loads(ctx.job.metadata) if ctx.job.metadata else {}
    phone_number = metadata.get("phone_number")
    test_message = metadata.get(
        "test_message",
        "This is a verification call. Please respond to confirm your agent is active.",
    )

    if not phone_number:
        logger.error("No phone number provided in job metadata")
        ctx.shutdown()
        return

    # Create the call verifier agent
    agent = CallVerifierAgent(phone_number=phone_number, test_message=test_message)

    # Create agent session with voice pipeline
    session = AgentSession(
        turn_detection=EnglishModel(),
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        tts=openai.TTS(),
        llm=openai.LLM(model="gpt-4o"),
    )

    # Initialize verification tracking
    room_name = ctx.room.name
    if room_name not in _verification_events:
        _verification_events[room_name] = asyncio.Event()
    agent.call_start_time = asyncio.get_event_loop().time()

    # Start the session first before dialing
    session_started = asyncio.create_task(
        session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(),
        )
    )

    # Get SIP trunk ID from environment
    sip_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
    if not sip_trunk_id:
        logger.error("SIP_OUTBOUND_TRUNK_ID not set")
        await agent._record_result(
            connected=False,
            answered=False,
            agent_responded=False,
            error_message="SIP_OUTBOUND_TRUNK_ID not configured",
        )
        ctx.shutdown()
        return

    # Create SIP participant to dial the phone number
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=sip_trunk_id,
                sip_call_to=phone_number,
                participant_identity=phone_number,
                wait_until_answered=True,
            )
        )

        # Wait for session to start and participant to join
        await session_started
        participant = await ctx.wait_for_participant(identity=phone_number)
        logger.info(f"Participant joined: {participant.identity}")

        agent.set_participant(participant)
        agent.call_answered = True  # Call was answered

        # Generate initial greeting with test message
        await session.generate_reply(
            instructions=f"Say the following test message clearly: {test_message}. "
            "Then wait briefly for a response. If you hear any response, use the call_answered tool. "
            "If you don't hear a response after a few seconds, use the call_failed tool with reason 'no-response'.",
        )

        # Wait a bit for response, then check if agent responded
        await asyncio.sleep(5)

        # If we haven't recorded a result yet, check if we got a response
        if not agent.agent_responded:
            # Check if there was any audio activity (simple heuristic)
            # In production, you might want more sophisticated detection
            await agent._record_result(
                ctx,
                connected=True,
                answered=True,
                agent_responded=False,
                error_message="No response detected",
            )

    except api.TwirpError as e:
        logger.error(
            f"Error creating SIP participant: {e.message}, "
            f"SIP status: {e.metadata.get('sip_status_code')} "
            f"{e.metadata.get('sip_status')}"
        )
        await agent._record_result(
            ctx,
            connected=False,
            answered=False,
            agent_responded=False,
            error_message=f"SIP error: {e.message}",
        )
        ctx.shutdown()
    except Exception as e:
        logger.error(f"Unexpected error in call verifier: {e}", exc_info=True)
        await agent._record_result(
            ctx,
            connected=False,
            answered=False,
            agent_responded=False,
            error_message=f"Unexpected error: {str(e)}",
        )
        ctx.shutdown()




async def create_verification_room(api_client: api.LiveKitAPI) -> str:
    """Create a LiveKit room for verification call.

    Args:
        api_client: LiveKit API client

    Returns:
        Room name
    """
    import time
    from uuid import uuid4

    # Generate a unique room name
    room_name = f"verification-{int(time.time())}-{str(uuid4())[:8]}"
    await api_client.room.create_room(
        api.CreateRoomRequest(
            name=room_name,
            empty_timeout=300,  # 5 minutes
            max_participants=2,
        )
    )
    return room_name


async def wait_for_verification_result(room_name: str, timeout: int) -> dict[str, Any]:
    """Wait for verification result from the agent.

    Args:
        room_name: Name of the verification room
        timeout: Maximum time to wait in seconds

    Returns:
        Verification result dictionary
    """
    if room_name not in _verification_events:
        _verification_events[room_name] = asyncio.Event()

    try:
        await asyncio.wait_for(_verification_events[room_name].wait(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Timeout waiting for verification result for room {room_name}")

    # Get result or return default
    result = _verification_results.get(room_name, {})
    
    # Cleanup
    _verification_events.pop(room_name, None)
    _verification_results.pop(room_name, None)

    return result


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="call-verifier",
        )
    )
