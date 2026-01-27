"""FastAPI application for voiceobs server."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from voiceobs._version import __version__
from voiceobs.server.config.logging_config import configure_logging
from voiceobs.server.dependencies import init_database, shutdown_database
from voiceobs.server.routes import (
    agents_router,
    analysis_router,
    audio_router,
    conversations_router,
    failures_router,
    health_router,
    metrics_router,
    personas_router,
    spans_router,
    test_executions_router,
    test_scenarios_router,
    test_suites_router,
)

logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv

    # Try to find .env file in project root
    # app.py is at: src/voiceobs/server/app.py
    # Going up: server -> voiceobs -> src -> project_root
    project_root = Path(__file__).parent.parent.parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)  # Don't override existing env vars
except ImportError:
    # python-dotenv not installed, skip loading .env file
    pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler.

    Manages database connection and agent worker on startup and shutdown.
    """
    # Startup: initialize database connection
    await init_database()
    yield
    await shutdown_database()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    # Configure logging first so all module logs are visible
    configure_logging()

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
    app.include_router(personas_router)
    app.include_router(agents_router)

    return app
