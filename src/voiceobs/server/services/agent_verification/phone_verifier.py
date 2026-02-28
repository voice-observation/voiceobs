"""Phone agent verification implementation using LiveKit."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from livekit import rtc
from livekit.agents import Agent, AgentSession, RoomInputOptions

from voiceobs.server.config.verification import get_verification_settings
from voiceobs.server.prompts.verification import (
    INITIATE_GREETING_INSTRUCTIONS,
    RESPOND_GREETING_INSTRUCTIONS,
    VERIFICATION_SYSTEM_PROMPT,
)
from voiceobs.server.services.agent_verification.base import AgentVerifier
from voiceobs.server.services.agent_verification.constants import (
    MAX_CONVERSATION_WAIT_SECONDS,
    MIN_VERIFICATION_TURNS,
    ROOM_NAME_PREFIX,
    VERIFIER_AGENT_IDENTITY,
)
from voiceobs.server.services.livekit_sip import run_livekit_sip_call
from voiceobs.server.utils.validators import is_valid_e164_phone_number

logger = logging.getLogger(__name__)


class PhoneAgentVerifier(AgentVerifier):
    """Verifier for phone-based agents using LiveKit SIP.

    This verifier:
    1. Creates a LiveKit room
    2. Dials the phone number via SIP trunk
    3. Runs a brief conversation using AgentSession
    4. Evaluates if the agent responded adequately
    """

    def __init__(self) -> None:
        """Initialize the phone agent verifier."""
        self._settings = get_verification_settings()
        self._transcript: list[dict[str, str]] = []
        self._turns = 0
        self._last_user_input_time: float | None = None
        self._last_agent_response_time: float | None = None
        self._tts_start_time: float | None = None
        self._turn_timings: list[dict[str, float]] = []
        self._other_party_spoke_first: bool = False
        self._speech_detected_event: asyncio.Event = asyncio.Event()

    async def verify(
        self, contact_info: dict[str, Any]
    ) -> tuple[bool, str | None, list[dict[str, str]] | None]:
        """Verify that a phone agent is reachable.

        Args:
            contact_info: Contact information dict containing "phone_number" key

        Returns:
            Tuple of (is_verified, error_message, transcript)

        Raises:
            ValueError: If phone_number is missing from contact_info
        """
        overall_start = time.monotonic()
        phone_number = contact_info.get("phone_number")
        if not phone_number:
            raise ValueError("phone_number is required in contact_info for phone agents")

        # Validate phone number format
        if not is_valid_e164_phone_number(phone_number):
            return (
                False,
                f"Invalid phone number format: {phone_number}. Expected E.164 format.",
                None,
            )

        # Check LiveKit configuration
        if not self._settings.livekit_url:
            return (False, "LiveKit not configured", None)

        # Reset state
        self._transcript = []
        self._turns = 0
        self._turn_timings = []
        self._other_party_spoke_first = False
        self._speech_detected_event.clear()

        try:
            async with run_livekit_sip_call(
                phone_number=phone_number,
                identity=VERIFIER_AGENT_IDENTITY,
                room_prefix=ROOM_NAME_PREFIX,
                settings=self._settings,
            ) as (room, session, _room_name):
                await self._run_conversation(room, session)

            # Evaluate
            verified = self._turns >= MIN_VERIFICATION_TURNS
            reasoning = (
                None
                if verified
                else (
                    f"Insufficient conversation - only {self._turns} turns "
                    f"(needed {MIN_VERIFICATION_TURNS})"
                )
            )

            overall_duration = time.monotonic() - overall_start
            result = "verified" if verified else "failed"
            logger.info(
                f"Verification completed for {phone_number} in {overall_duration:.2f}s, "
                f"result: {result}"
            )
            return (verified, reasoning, self._transcript)

        except Exception as e:
            overall_duration = time.monotonic() - overall_start
            error_msg = getattr(e, "message", str(e))
            logger.warning(
                f"Verification failed for {phone_number} in {overall_duration:.2f}s: {e}"
            )
            return (False, error_msg, self._transcript)

    async def _wait_for_speech(self, timeout: float) -> bool:
        """Wait for speech detection or timeout.

        Args:
            timeout: Maximum seconds to wait for speech

        Returns:
            True if speech was detected, False if timeout expired
        """
        try:
            await asyncio.wait_for(self._speech_detected_event.wait(), timeout=timeout)
            self._other_party_spoke_first = True
            return True
        except asyncio.TimeoutError:
            self._other_party_spoke_first = False
            return False

    def _on_user_state_changed(self, event: Any) -> None:
        """Handle user state changes to detect when other party starts speaking.

        Args:
            event: User state change event from AgentSession
        """
        if event.new_state == "speaking":
            self._speech_detected_event.set()
            logger.debug("Other party started speaking")

    async def _run_conversation(self, room: rtc.Room, session: AgentSession) -> None:
        """Run the verification conversation.

        Args:
            room: LiveKit room to run conversation in
            session: AgentSession to use for conversation
        """
        conversation_start = time.monotonic()

        # Register speech event handlers
        @session.on("agent_state_changed")
        def on_agent_state_changed(event: Any) -> None:
            if event.new_state == "speaking" and self._tts_start_time is None:
                self._tts_start_time = time.monotonic()
                logger.debug("TTS started")
            elif event.old_state == "speaking" and event.new_state == "listening":
                if self._tts_start_time is not None:
                    tts_duration = time.monotonic() - self._tts_start_time
                    logger.info(f"TTS processing took {tts_duration:.3f}s")
                    if self._turn_timings and "tts_duration" not in self._turn_timings[-1]:
                        self._turn_timings[-1]["tts_duration"] = tts_duration
                    self._tts_start_time = None

        @session.on("user_state_changed")
        def on_user_state_changed(event: Any) -> None:
            self._on_user_state_changed(event)

        @session.on("user_input_transcribed")
        def on_user_input_transcribed(_transcript: Any) -> None:
            current_time = time.monotonic()
            if self._last_agent_response_time is not None:
                stt_duration = current_time - self._last_agent_response_time
                logger.info(f"STT processing took {stt_duration:.3f}s")
                if self._turn_timings and "stt_duration" not in self._turn_timings[-1]:
                    self._turn_timings[-1]["stt_duration"] = stt_duration

        @session.on("conversation_item_added")
        def on_conversation_item(event: Any) -> None:
            current_time = time.monotonic()
            text = event.item.text_content
            if event.item.role == "user":
                logger.info(f"USER: {text}")
                self._transcript.append({"role": "user", "content": text})
                self._turns += 1
                self._last_user_input_time = current_time
            elif event.item.role == "assistant":
                logger.info(f"AGENT: {text}")
                self._transcript.append({"role": "assistant", "content": text})
                self._last_agent_response_time = current_time

                if self._last_user_input_time is not None:
                    llm_duration = current_time - self._last_user_input_time
                    logger.info(f"LLM processing for turn {self._turns} took {llm_duration:.3f}s")
                    self._turn_timings.append({"turn": self._turns, "llm_duration": llm_duration})
                    self._last_user_input_time = None

        # Start session
        await session.start(
            agent=Agent(instructions=VERIFICATION_SYSTEM_PROMPT),
            room=room,
            room_input_options=RoomInputOptions(),
        )

        # Wait for other party to speak first, or timeout
        other_party_spoke = await self._wait_for_speech(
            timeout=self._settings.verification_initial_wait_timeout
        )

        if other_party_spoke:
            logger.info("Other party spoke first, responding contextually")
            await session.generate_reply(instructions=RESPOND_GREETING_INSTRUCTIONS)
        else:
            logger.info("Timeout expired, initiating greeting")
            speech_handle = await session.generate_reply(
                instructions=INITIATE_GREETING_INSTRUCTIONS
            )

            if self._speech_detected_event.is_set():
                logger.info("Other party started speaking during our greeting, yielding")
                speech_handle.interrupt()
                self._other_party_spoke_first = True

        max_turns = self._settings.verification_max_turns
        elapsed = 0
        while self._turns < max_turns and elapsed < MAX_CONVERSATION_WAIT_SECONDS:
            await asyncio.sleep(1)
            elapsed += 1

        conversation_duration = time.monotonic() - conversation_start
        logger.info(
            f"Conversation completed in {conversation_duration:.2f}s with {self._turns} turns"
        )

        self._log_timing_summary()

    def _log_timing_summary(self) -> None:
        """Log summary of turn timings."""
        if not self._turn_timings:
            return

        avg_llm_time = sum(t["llm_duration"] for t in self._turn_timings) / len(self._turn_timings)
        logger.info(f"Average LLM processing time per turn: {avg_llm_time:.3f}s")

        stt_timings = [t["stt_duration"] for t in self._turn_timings if "stt_duration" in t]
        if stt_timings:
            avg_stt_time = sum(stt_timings) / len(stt_timings)
            logger.info(f"Average STT processing time per turn: {avg_stt_time:.3f}s")

        tts_timings = [t["tts_duration"] for t in self._turn_timings if "tts_duration" in t]
        if tts_timings:
            avg_tts_time = sum(tts_timings) / len(tts_timings)
            logger.info(f"Average TTS processing time per turn: {avg_tts_time:.3f}s")

        for timing in self._turn_timings:
            llm_info = f"LLM {timing['llm_duration']:.3f}s"
            stt_info = f", STT {timing['stt_duration']:.3f}s" if "stt_duration" in timing else ""
            tts_info = f", TTS {timing['tts_duration']:.3f}s" if "tts_duration" in timing else ""
            logger.info(f"Turn {timing['turn']}: {llm_info}{stt_info}{tts_info}")

    def get_agent_type(self) -> str:
        """Get the agent type this verifier handles.

        Returns:
            "phone"
        """
        return "phone"
