"""API routes for the voiceobs server."""

from voiceobs.server.routes.analysis import router as analysis_router
from voiceobs.server.routes.audio import router as audio_router
from voiceobs.server.routes.conversations import router as conversations_router
from voiceobs.server.routes.failures import router as failures_router
from voiceobs.server.routes.health import router as health_router
from voiceobs.server.routes.metrics import router as metrics_router
from voiceobs.server.routes.spans import router as spans_router
from voiceobs.server.routes.test_executions import router as test_executions_router
from voiceobs.server.routes.test_scenarios import router as test_scenarios_router
from voiceobs.server.routes.test_suites import router as test_suites_router

__all__ = [
    "analysis_router",
    "audio_router",
    "conversations_router",
    "failures_router",
    "health_router",
    "metrics_router",
    "spans_router",
    "test_suites_router",
    "test_scenarios_router",
    "test_executions_router",
]
