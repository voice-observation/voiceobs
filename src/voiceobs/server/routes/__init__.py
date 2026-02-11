"""API routes for the voiceobs server."""

from voiceobs.server.routes.agents import router as agents_router
from voiceobs.server.routes.analysis import router as analysis_router
from voiceobs.server.routes.audio import router as audio_router
from voiceobs.server.routes.auth import router as auth_router
from voiceobs.server.routes.conversations import router as conversations_router
from voiceobs.server.routes.failures import router as failures_router
from voiceobs.server.routes.health import router as health_router
from voiceobs.server.routes.metrics import router as metrics_router
from voiceobs.server.routes.organization_invites import (
    router as organization_invites_router,
)
from voiceobs.server.routes.organization_members import (
    router as organization_members_router,
)
from voiceobs.server.routes.organizations import router as organizations_router
from voiceobs.server.routes.personas import router as personas_router
from voiceobs.server.routes.spans import router as spans_router
from voiceobs.server.routes.test_executions import router as test_executions_router
from voiceobs.server.routes.test_scenarios import router as test_scenarios_router
from voiceobs.server.routes.test_suites import router as test_suites_router
from voiceobs.server.routes.traits import router as traits_router
from voiceobs.server.routes.tts import router as tts_router

__all__ = [
    "agents_router",
    "analysis_router",
    "audio_router",
    "auth_router",
    "conversations_router",
    "failures_router",
    "health_router",
    "metrics_router",
    "organization_invites_router",
    "organization_members_router",
    "organizations_router",
    "personas_router",
    "spans_router",
    "test_suites_router",
    "test_scenarios_router",
    "test_executions_router",
    "traits_router",
    "tts_router",
]
