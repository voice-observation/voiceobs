"""FastAPI application for voiceobs server."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from voiceobs._version import __version__
from voiceobs.server.dependencies import init_database, shutdown_database
from voiceobs.server.routes import (
    analysis_router,
    audio_router,
    conversations_router,
    failures_router,
    health_router,
    metrics_router,
    spans_router,
    test_executions_router,
    test_scenarios_router,
    test_suites_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler.

    Manages database connection on startup and shutdown.
    """
    # Startup: initialize database connection
    await init_database()
    yield
    # Shutdown: close database connection
    await shutdown_database()


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
        lifespan=lifespan,
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
    app.include_router(metrics_router)
    app.include_router(audio_router)
    app.include_router(test_suites_router)
    app.include_router(test_scenarios_router)
    app.include_router(test_executions_router)

    return app
