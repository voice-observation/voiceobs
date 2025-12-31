"""API routes for the voiceobs server."""

from voiceobs.server.routes.analysis import router as analysis_router
from voiceobs.server.routes.conversations import router as conversations_router
from voiceobs.server.routes.failures import router as failures_router
from voiceobs.server.routes.health import router as health_router
from voiceobs.server.routes.spans import router as spans_router

__all__ = [
    "analysis_router",
    "conversations_router",
    "failures_router",
    "health_router",
    "spans_router",
]
