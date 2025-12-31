"""Health check routes."""

from datetime import datetime

from fastapi import APIRouter

from voiceobs._version import __version__
from voiceobs.server.models import HealthResponse

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the server is running and healthy.",
)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=__version__,
        timestamp=datetime.utcnow(),
    )
