"""TTS provider routes."""

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from voiceobs.server.auth.context import AuthContext, get_auth_context
from voiceobs.server.dependencies import is_using_postgres
from voiceobs.server.models import ErrorResponse

router = APIRouter(prefix="/api/v1/tts", tags=["TTS"])

# Path to TTS provider models file
MODELS_PATH = Path(__file__).parent.parent / "seed" / "tts_provider_models.json"


@router.get(
    "/models",
    summary="Get available TTS models",
    description="Get a list of available TTS provider models.",
    responses={
        501: {"model": ErrorResponse, "description": "TTS API requires PostgreSQL database"},
    },
)
async def get_tts_models(
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, dict[str, dict[str, Any]]]:
    """Get available TTS provider models.

    Returns the models from tts_provider_models.json file.
    This data is global and not organization-specific.
    """
    if not is_using_postgres():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="TTS API requires PostgreSQL database",
        )

    try:
        with open(MODELS_PATH, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("models", {})
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TTS models file not found",
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse TTS models file: {str(e)}",
        )
