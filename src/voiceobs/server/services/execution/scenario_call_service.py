"""Scenario call service for real LiveKit SIP calls with egress recording."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from livekit import api, rtc
from livekit.agents import Agent, AgentSession, RoomInputOptions

from voiceobs.server.config.execution import ExecutionSettings
from voiceobs.server.config.verification import VerificationSettings
from voiceobs.server.prompts.scenario_call import SCENARIO_CALL_SYSTEM_PROMPT
from voiceobs.server.services.execution.scenario_call import (
    AfterConversationCallback,
    BeforeDialCallback,
    EgressContext,
    TranscriptCollector,
)
from voiceobs.server.services.livekit_sip import run_livekit_sip_call

if TYPE_CHECKING:
    from voiceobs.server.db.repositories.agent import AgentRepository
    from voiceobs.server.db.repositories.persona import PersonaRepository
    from voiceobs.server.db.repositories.test_execution import TestExecutionRepository
    from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository
    from voiceobs.server.db.repositories.test_suite import TestSuiteRepository
    from voiceobs.server.db.repositories.test_suite_run import TestSuiteRunRepository

logger = logging.getLogger(__name__)

# Default max turns and timeout when scenario does not specify
DEFAULT_MAX_TURNS = 6
DEFAULT_TIMEOUT_SECONDS = 120

# Egress poll interval and max wait
EGRESS_POLL_INTERVAL = 2
EGRESS_MAX_WAIT_SECONDS = 60

# Max time to wait for agent to finish speaking after turn limit (capture full TTS)
AGENT_FINISH_SPEAKING_TIMEOUT_SECONDS = 60


class ScenarioCallService:
    """Service for running scenario calls via LiveKit SIP with egress recording."""

    def __init__(
        self,
        execution_repo: TestExecutionRepository,
        scenario_repo: TestScenarioRepository,
        suite_repo: TestSuiteRepository,
        suite_run_repo: TestSuiteRunRepository,
        agent_repo: AgentRepository,
        persona_repo: PersonaRepository,
        verification_settings: VerificationSettings,
        execution_settings: ExecutionSettings,
    ) -> None:
        """Initialize the scenario call service."""
        self._execution_repo = execution_repo
        self._scenario_repo = scenario_repo
        self._suite_repo = suite_repo
        self._suite_run_repo = suite_run_repo
        self._agent_repo = agent_repo
        self._persona_repo = persona_repo
        self._verification_settings = verification_settings
        self._execution_settings = execution_settings

    def _build_scenario_system_prompt(
        self,
        goal: str,
        persona_traits: list[str],
        caller_behaviors: list[str],
        persona_description: str | None = None,
    ) -> str:
        """Build the system prompt for the persona bot in a scenario call."""
        traits_str = ", ".join(persona_traits) if persona_traits else "natural"
        behaviors_str = ", ".join(caller_behaviors) if caller_behaviors else "natural"
        desc_part = ""
        if persona_description:
            desc_part = f" Persona: {persona_description}."

        return SCENARIO_CALL_SYSTEM_PROMPT.format(
            desc_part=desc_part,
            goal=goal,
            traits_str=traits_str,
            behaviors_str=behaviors_str,
        )

    async def _before_dial_egress(
        self,
        ctx: EgressContext,
        execution_id: UUID,
        room_name: str,
    ) -> None:
        """Start room composite egress and store API client/egress_id in context."""
        if self._execution_settings.audio_storage_provider != "s3":
            raise RuntimeError("Egress requires S3 (VOICEOBS_AUDIO_STORAGE_PROVIDER=s3)")
        if not self._execution_settings.audio_storage_path:
            raise RuntimeError("Egress S3 bucket not configured (VOICEOBS_AUDIO_STORAGE_PATH)")
        if (
            not self._execution_settings.audio_s3_access_key
            or not self._execution_settings.audio_s3_secret
        ):
            raise RuntimeError(
                "Egress S3 credentials required "
                "(VOICEOBS_AUDIO_S3_ACCESS_KEY, VOICEOBS_AUDIO_S3_SECRET)"
            )

        ctx.api_client = api.LiveKitAPI(
            url=self._verification_settings.livekit_url,
            api_key=self._verification_settings.livekit_api_key,
            api_secret=self._verification_settings.livekit_api_secret,
        )

        req = api.RoomCompositeEgressRequest(
            room_name=room_name,
            audio_only=True,
            file_outputs=[
                api.EncodedFileOutput(
                    filepath=f"test-scenario-executions/{execution_id}.ogg",
                    s3=api.S3Upload(
                        region=self._execution_settings.audio_s3_region,
                        bucket=self._execution_settings.audio_storage_path,
                        access_key=self._execution_settings.audio_s3_access_key,
                        secret=self._execution_settings.audio_s3_secret,
                    ),
                ),
            ],
        )
        egress_info = await ctx.api_client.egress.start_room_composite_egress(req)
        ctx.egress_id = egress_info.egress_id
        logger.info("Started egress %s for room %s", ctx.egress_id, room_name)

    async def _after_conversation_wait_egress(
        self,
        ctx: EgressContext,
        execution_id: UUID,
        room_name: str,
    ) -> None:
        """Stop egress, poll for completion, set audio_url on context, close API client."""
        if ctx.api_client is None or ctx.egress_id is None:
            return

        stop_req = api.StopEgressRequest(egress_id=ctx.egress_id)
        await ctx.api_client.egress.stop_egress(stop_req)

        waited = 0
        while waited < EGRESS_MAX_WAIT_SECONDS:
            list_req = api.ListEgressRequest(egress_id=ctx.egress_id)
            list_resp = await ctx.api_client.egress.list_egress(list_req)
            if list_resp.items:
                info = list_resp.items[0]
                if info.status == api.EGRESS_COMPLETE:
                    filepath = f"test-scenario-executions/{execution_id}.ogg"
                    ctx.audio_url = f"s3://{self._execution_settings.audio_storage_path}/{filepath}"
                    logger.info("Egress complete, audio_url=%s", ctx.audio_url)
                    break
                if info.status in (api.EGRESS_FAILED, api.EGRESS_ABORTED):
                    err = getattr(info, "error", "unknown")
                    logger.warning("Egress failed: %s", err)
                    break
            await asyncio.sleep(EGRESS_POLL_INTERVAL)
            waited += EGRESS_POLL_INTERVAL

        await ctx.api_client.aclose()

    async def _run_conversation(
        self,
        room: rtc.Room,
        session: AgentSession,
        system_prompt: str,
        max_turns: int,
        timeout_seconds: int,
    ) -> list[dict[str, Any]]:
        """Run agent conversation, collect transcript, return when done."""
        collector = TranscriptCollector()
        session.on("conversation_item_added", collector)

        agent_state: list[str] = ["unknown"]

        def _on_agent_state(event: Any) -> None:
            new_state = getattr(event, "new_state", "unknown")
            agent_state[0] = str(new_state)

        session.on("agent_state_changed", _on_agent_state)

        await session.start(
            agent=Agent(instructions=system_prompt),
            room=room,
            room_input_options=RoomInputOptions(),
        )

        turn_count = 0
        elapsed = 0
        while turn_count < max_turns and elapsed < timeout_seconds:
            await asyncio.sleep(1)
            elapsed += 1
            turn_count = sum(1 for e in collector.items if e.get("role") == "persona")

        # Wait for agent to finish speaking before stopping egress (capture full TTS)
        if agent_state[0] in ("thinking", "speaking"):
            agent_finished = asyncio.Event()

            def _on_agent_state_finish(event: Any) -> None:
                new_state = getattr(event, "new_state", "unknown")
                agent_state[0] = str(new_state)
                if new_state == "listening":
                    agent_finished.set()

            session.on("agent_state_changed", _on_agent_state_finish)
            try:
                await asyncio.wait_for(
                    agent_finished.wait(),
                    timeout=AGENT_FINISH_SPEAKING_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "Timed out waiting for agent to finish speaking (state=%s)",
                    agent_state[0],
                )

        return collector.items

    async def run_scenario(self, execution_id: UUID) -> bool:
        """Run a scenario call: load context, dial, record, collect transcript.

        On success: updates execution with transcript, audio_url, duration, status=evaluating.
        On failure: updates execution with status=failed and error_message.

        Returns:
            True if call succeeded and execution is ready for evaluation, False otherwise.
        """
        execution = await self._execution_repo.get_by_id(execution_id)
        if execution is None:
            logger.warning("Execution %s not found, skipping", execution_id)
            return False

        org_id = execution.org_id

        suite_run_id = execution.suite_run_id

        # Load scenario
        scenario = await self._scenario_repo.get(execution.scenario_id, org_id)
        if scenario is None:
            await self._mark_failed(execution_id, org_id, "Scenario not found", suite_run_id)
            return False

        # Load suite
        suite = await self._suite_repo.get(scenario.suite_id, org_id)
        if suite is None:
            await self._mark_failed(execution_id, org_id, "Suite not found", suite_run_id)
            return False

        if suite.agent_id is None:
            await self._mark_failed(execution_id, org_id, "Suite has no agent", suite_run_id)
            return False

        # Load agent
        agent = await self._agent_repo.get(suite.agent_id, org_id)
        if agent is None:
            await self._mark_failed(execution_id, org_id, "Agent not found", suite_run_id)
            return False

        if agent.agent_type != "phone":
            await self._mark_failed(
                execution_id,
                org_id,
                f"Agent type '{agent.agent_type}' not supported for calls",
                suite_run_id,
            )
            return False

        phone_number = agent.phone_number
        if not phone_number:
            await self._mark_failed(execution_id, org_id, "Agent has no phone number", suite_run_id)
            return False

        # Load persona
        persona = await self._persona_repo.get(scenario.persona_id, org_id)
        if persona is None:
            await self._mark_failed(execution_id, org_id, "Persona not found", suite_run_id)
            return False

        # Update status to calling
        await self._execution_repo.update(
            execution_id,
            org_id,
            {"status": "calling", "started_at": datetime.utcnow()},
        )

        started_at = time.monotonic()
        egress_ctx = EgressContext()
        max_turns = scenario.max_turns or DEFAULT_MAX_TURNS
        timeout_seconds = scenario.timeout or DEFAULT_TIMEOUT_SECONDS

        system_prompt = self._build_scenario_system_prompt(
            goal=scenario.goal,
            persona_traits=scenario.persona_traits or persona.traits,
            caller_behaviors=scenario.caller_behaviors,
            persona_description=persona.description,
        )

        before_dial = BeforeDialCallback(self, egress_ctx, execution_id)
        after_conversation = AfterConversationCallback(self, egress_ctx, execution_id)

        try:
            async with run_livekit_sip_call(
                phone_number=phone_number,
                identity="execution-bot",
                room_prefix="exec-",
                settings=self._verification_settings,
                before_dial=before_dial,
                after_conversation=after_conversation,
            ) as (_room, session, _room_name):
                transcript = await self._run_conversation(
                    _room, session, system_prompt, max_turns, timeout_seconds
                )

        except Exception as e:
            error_msg = getattr(e, "message", str(e))
            logger.warning("Scenario call failed for execution %s: %s", execution_id, e)
            if egress_ctx.api_client is not None:
                try:
                    await egress_ctx.api_client.aclose()
                except Exception:
                    pass
                egress_ctx.api_client = None
            await self._mark_failed(execution_id, org_id, error_msg, suite_run_id)
            return False

        duration_seconds = time.monotonic() - started_at

        await self._execution_repo.update(
            execution_id,
            org_id,
            {
                "status": "evaluating",
                "transcript": transcript,
                "audio_url": egress_ctx.audio_url,
                "duration_seconds": duration_seconds,
                "completed_at": datetime.utcnow(),
            },
        )

        logger.info(
            "Scenario call completed for execution %s: %d turns, %.1fs",
            execution_id,
            len([e for e in transcript if e.get("role") == "persona"]),
            duration_seconds,
        )
        return True

    async def _mark_failed(
        self,
        execution_id: UUID,
        org_id: UUID,
        error_message: str,
        suite_run_id: UUID,
    ) -> None:
        """Mark execution failed, increment suite run failed count, complete suite if done."""
        await self._execution_repo.update(
            execution_id, org_id, {"status": "failed", "error_message": error_message}
        )
        await self._suite_run_repo.increment_failed(suite_run_id, org_id)
        suite_run = await self._suite_run_repo.get(suite_run_id, org_id)
        if suite_run and self._is_suite_run_complete(suite_run):
            await self._suite_run_repo.update(
                suite_run_id, org_id, {"status": "completed", "completed_at": datetime.utcnow()}
            )

    def _is_suite_run_complete(self, suite_run: Any) -> bool:
        """Check if all executions in suite run have finished."""
        total = suite_run.completed_scenarios + suite_run.failed_scenarios
        return total >= suite_run.total_scenarios
