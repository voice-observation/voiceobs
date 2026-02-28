"""Async callback for run_livekit_sip_call before_dial hook."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from voiceobs.server.services.execution.scenario_call.egress_context import (
    EgressContext,
)

if TYPE_CHECKING:
    from voiceobs.server.services.execution.scenario_call_service import (
        ScenarioCallService,
    )


class BeforeDialCallback:
    """Async callback for run_livekit_sip_call before_dial hook."""

    def __init__(
        self,
        service: ScenarioCallService,
        ctx: EgressContext,
        execution_id: UUID,
    ) -> None:
        self._service = service
        self._ctx = ctx
        self._execution_id = execution_id

    async def __call__(self, room_name: str) -> None:
        await self._service._before_dial_egress(self._ctx, self._execution_id, room_name)
