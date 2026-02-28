"""Shared LiveKit SIP call runner for verification and scenario execution."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

import aiohttp
from google.protobuf import duration_pb2
from livekit import api, rtc
from livekit.agents import AgentSession

from voiceobs.server.config.verification import VerificationSettings
from voiceobs.server.services.agent_verification.constants import (
    DEFAULT_MAX_PARTICIPANTS,
    DEFAULT_ROOM_EMPTY_TIMEOUT,
    SIP_PARTICIPANT_PREFIX,
)
from voiceobs.server.services.agent_verification.livekit_providers import (
    LiveKitProviderFactory,
)
from voiceobs.server.utils.async_helpers import log_timing, safe_cleanup
from voiceobs.server.utils.livekit import create_room_token, generate_room_name

logger = logging.getLogger(__name__)


@asynccontextmanager
async def run_livekit_sip_call(
    phone_number: str,
    identity: str,
    room_prefix: str,
    settings: VerificationSettings,
    *,
    call_timeout: int | None = None,
    before_dial: Callable[[str], Awaitable[Any]] | None = None,
    after_conversation: Callable[[str], Awaitable[Any]] | None = None,
) -> AsyncIterator[tuple[rtc.Room, AgentSession, str]]:
    """Run a LiveKit SIP call: create room, dial, connect, yield for conversation, cleanup.

    Args:
        phone_number: E.164 phone number to dial.
        identity: Participant identity for our agent in the room.
        room_prefix: Prefix for generated room name (e.g. "verify", "exec-").
        settings: Verification settings (LiveKit URL, API keys, SIP trunk).
        call_timeout: SIP ringing timeout in seconds (default from settings).
        before_dial: Optional async hook called after room creation, before SIP dial.
        after_conversation: Optional async hook called after conversation ends, before cleanup.

    Yields:
        Tuple of (room, agent_session, room_name) for the caller to run the conversation.

    Raises:
        api.TwirpError: On SIP/LiveKit API errors.
        Exception: Propagates errors from hooks or conversation.
    """
    timeout = (
        call_timeout if call_timeout is not None else min(settings.verification_call_timeout, 60)
    )
    room_name = generate_room_name(prefix=room_prefix)
    participant_identity = f"{SIP_PARTICIPANT_PREFIX}{phone_number}"

    http_session = aiohttp.ClientSession()
    api_client = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )
    room: rtc.Room | None = None
    agent_session: AgentSession | None = None

    try:
        # Step 1: Create room
        logger.info("Creating room: %s", room_name)
        await api_client.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=DEFAULT_ROOM_EMPTY_TIMEOUT,
                max_participants=DEFAULT_MAX_PARTICIPANTS,
            )
        )

        # Step 2: Optional before_dial hook (e.g. start egress)
        if before_dial is not None:
            await before_dial(room_name)

        # Step 3: Dial phone via SIP
        logger.info("Dialing %s", phone_number)
        await api_client.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=settings.sip_outbound_trunk_id,
                sip_call_to=phone_number,
                room_name=room_name,
                participant_identity=participant_identity,
                ringing_timeout=duration_pb2.Duration(seconds=timeout),
                wait_until_answered=True,
            )
        )
        logger.info("Call answered: %s", phone_number)

        # Step 4: Connect to room and create AgentSession
        room = rtc.Room()
        token = create_room_token(
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
            room_name=room_name,
            identity=identity,
        )
        await room.connect(settings.livekit_url, token)

        with log_timing(logger, "AgentSession creation"):
            provider_factory = LiveKitProviderFactory(http_session=http_session)
            agent_session = provider_factory.create_agent_session()

        # Step 5: Yield for conversation
        yield (room, agent_session, room_name)

        # Step 6: Optional after_conversation hook (e.g. stop egress)
        if after_conversation is not None:
            await after_conversation(room_name)

    finally:
        # Step 7: Cleanup - AgentSession first, then room, then API/session
        await safe_cleanup(agent_session, logger=logger)
        agent_session = None
        await safe_cleanup(room, logger=logger)
        room = None
        try:
            await api_client.room.delete_room(api.DeleteRoomRequest(room=room_name))
        except Exception:
            pass
        await safe_cleanup(api_client, http_session, logger=logger)


class LiveKitSIPCallRunner:
    """Runner for LiveKit SIP calls, used by verification and scenario execution."""

    def __init__(self, settings: VerificationSettings) -> None:
        """Initialize the runner with verification settings.

        Args:
            settings: LiveKit and SIP configuration.
        """
        self._settings = settings

    async def run(
        self,
        phone_number: str,
        identity: str,
        room_prefix: str,
        conversation_fn: Callable[[rtc.Room, AgentSession, str], Awaitable[Any]],
        *,
        call_timeout: int | None = None,
        before_dial: Callable[[str], Awaitable[Any]] | None = None,
        after_conversation: Callable[[str], Awaitable[Any]] | None = None,
    ) -> None:
        """Run a SIP call and execute the conversation callback.

        Args:
            phone_number: E.164 phone number to dial.
            identity: Participant identity for our agent.
            room_prefix: Prefix for room name.
            conversation_fn: Async function to run the conversation.
            call_timeout: Optional SIP ringing timeout.
            before_dial: Optional async hook before SIP dial.
            after_conversation: Optional async hook after conversation.
        """
        async with run_livekit_sip_call(
            phone_number=phone_number,
            identity=identity,
            room_prefix=room_prefix,
            settings=self._settings,
            call_timeout=call_timeout,
            before_dial=before_dial,
            after_conversation=after_conversation,
        ) as (room, session, room_name):
            await conversation_fn(room, session, room_name)
