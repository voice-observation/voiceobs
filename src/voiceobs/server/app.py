"""FastAPI application for voiceobs server."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from voiceobs._version import __version__
from voiceobs.server.routes import (
    analysis_router,
    conversations_router,
    failures_router,
    health_router,
    spans_router,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="voiceobs",
        description="Voice AI observability server",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS for UI integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health_router)
    app.include_router(spans_router)
    app.include_router(analysis_router)
    app.include_router(conversations_router)
    app.include_router(failures_router)

    return app
