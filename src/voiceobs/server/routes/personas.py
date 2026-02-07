"""Persona management routes."""

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from voiceobs.server.dependencies import (
    get_audio_storage,
    get_persona_repository,
    is_using_postgres,
)
from voiceobs.server.models import (
    ErrorResponse,
    PersonaAudioPreviewResponse,
    PersonaListItem,
    PersonaResponse,
    PersonasListResponse,
    PreviewAudioStatusResponse,
)
from voiceobs.server.models.request import (
    PersonaActiveRequest,
    PersonaCreateRequest,
    PersonaUpdateRequest,
)
from voiceobs.server.services.tts_factory import TTSServiceFactory
from voiceobs.server.utils import parse_uuid
from voiceobs.server.utils.persona_llm import generate_persona_attributes_with_llm
from voiceobs.server.utils.storage import get_presigned_url_for_audio

router = APIRouter(prefix="/api/v1/personas", tags=["Personas"])

# Path to TTS provider models file
MODELS_PATH = Path(__file__).parent.parent / "seed" / "tts_provider_models.json"

# Default preview text for generating preview audio (30-60 seconds when spoken)
DEFAULT_PREVIEW_TEXT = (
    "Hello! I'm here to help you today. My name is Alex, and I'll be assisting you "
    "with your inquiry. I understand that getting the right support is important, "
    "so please take a moment to listen to my voice and speaking style. I aim to be "
    "clear, professional, and easy to understand. Whether you have questions about "
    "products, services, or need technical assistance, I'm here to provide the "
    "information you need. I'll do my best to ensure our conversation is productive "
    "and helpful. If at any point you need me to slow down, repeat information, or "
    "clarify something, please don't hesitate to let me know. I'm committed to "
    "making this a positive experience for you. Now, how may I assist you today?"
)


async def _generate_preview_audio_background(
    persona_id: str,
    tts_provider: str,
    tts_config: dict,
    preview_text: str,
) -> None:
    """Background task to generate preview audio for a persona."""
    from voiceobs.server.dependencies import get_persona_repository

    repo = get_persona_repository()

    persona_uuid = parse_uuid(persona_id, "persona")

    try:
        tts_service = TTSServiceFactory.create(tts_provider)
        audio_bytes, mime_type, _ = await tts_service.synthesize(preview_text, tts_config)

        audio_storage = get_audio_storage()
        preview_audio_url = await audio_storage.store_audio(
            audio_bytes,
            prefix=f"personas/preview/{persona_id}",
            content_type=mime_type,
        )

        await repo.update(
            persona_id=persona_uuid,
            preview_audio_url=preview_audio_url,
            preview_audio_text=preview_text,
            preview_audio_status="ready",
            preview_audio_error=None,
        )
    except Exception as e:
        await repo.update(
            persona_id=persona_uuid,
            preview_audio_status="failed",
            preview_audio_error=str(e),
        )


@router.post(
    "",
    response_model=PersonaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create persona",
    description="Create a new persona. Preview audio is generated lazily when requested.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def create_persona(
    request: PersonaCreateRequest,
) -> PersonaResponse:
    """Create a new persona without generating preview audio.

    Preview audio is generated lazily when the user requests it via
    POST /personas/{persona_id}/preview-audio.
    """
    repo = get_persona_repository()

    # Generate persona attributes with LLM if they are missing
    needs_llm_generation = (
        request.aggression is None
        or request.patience is None
        or request.verbosity is None
        or request.tts_provider is None
        or request.tts_config is None
    )

    if needs_llm_generation:
        try:
            (
                llm_aggression,
                llm_patience,
                llm_verbosity,
                llm_tts_provider,
                llm_tts_config,
            ) = await generate_persona_attributes_with_llm(
                request.name, request.description, MODELS_PATH
            )
            # Use LLM-generated values, falling back to provided values if they exist
            aggression = request.aggression if request.aggression is not None else llm_aggression
            patience = request.patience if request.patience is not None else llm_patience
            verbosity = request.verbosity if request.verbosity is not None else llm_verbosity
            tts_provider = (
                request.tts_provider if request.tts_provider is not None else llm_tts_provider
            )
            tts_config = request.tts_config if request.tts_config is not None else llm_tts_config
        except ValueError:
            # If LLM generation fails, use defaults
            aggression = request.aggression if request.aggression is not None else 0.5
            patience = request.patience if request.patience is not None else 0.5
            verbosity = request.verbosity if request.verbosity is not None else 0.5
            tts_provider = request.tts_provider
            tts_config = request.tts_config or {}
    else:
        # Use provided values
        aggression = request.aggression
        patience = request.patience
        verbosity = request.verbosity
        tts_provider = request.tts_provider
        tts_config = request.tts_config or {}

    # Create persona without preview audio (lazy generation)
    try:
        persona = await repo.create(
            name=request.name,
            aggression=aggression,
            patience=patience,
            verbosity=verbosity,
            tts_provider=tts_provider,
            tts_config=tts_config,
            description=request.description,
            traits=request.traits,
            metadata=request.metadata,
            created_by=request.created_by,
            preview_audio_url=None,
            preview_audio_text=None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return PersonaResponse(
        id=str(persona.id),
        name=persona.name,
        description=persona.description,
        aggression=persona.aggression,
        patience=persona.patience,
        verbosity=persona.verbosity,
        traits=persona.traits,
        tts_provider=persona.tts_provider,
        tts_config=persona.tts_config,
        preview_audio_url=persona.preview_audio_url,
        preview_audio_text=persona.preview_audio_text,
        preview_audio_status=persona.preview_audio_status,
        preview_audio_error=persona.preview_audio_error,
        metadata=persona.metadata,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
        created_by=persona.created_by,
        is_active=persona.is_active,
        is_default=persona.is_default,
    )


@router.get(
    "",
    response_model=PersonasListResponse,
    summary="List personas",
    description="Get a list of personas with optional filtering.",
    responses={
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def list_personas(
    is_active: bool | None = Query(None, description="Filter by active status (None for all)"),
    limit: int | None = Query(None, ge=1, le=100, description="Maximum number of results"),
    offset: int | None = Query(None, ge=0, description="Number of results to skip"),
) -> PersonasListResponse:
    """List all personas with optional filtering."""
    repo = get_persona_repository()
    personas = await repo.list_all(is_active=is_active, limit=limit, offset=offset)

    return PersonasListResponse(
        count=len(personas),
        personas=[
            PersonaListItem(
                id=str(persona.id),
                name=persona.name,
                description=persona.description,
                aggression=persona.aggression,
                patience=persona.patience,
                verbosity=persona.verbosity,
                traits=persona.traits,
                preview_audio_url=persona.preview_audio_url,
                preview_audio_text=persona.preview_audio_text,
                preview_audio_status=persona.preview_audio_status,
                is_active=persona.is_active,
                is_default=persona.is_default,
            )
            for persona in personas
        ],
    )


@router.get(
    "/tts-models",
    summary="Get available TTS models",
    description="Get a list of available TTS provider models for persona creation.",
    responses={
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def get_tts_models() -> dict[str, dict[str, dict[str, Any]]]:
    """Get available TTS provider models.

    Returns the models from tts_provider_models.json file.
    """
    if not is_using_postgres():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Persona API requires PostgreSQL database",
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


@router.get(
    "/{persona_id}",
    response_model=PersonaResponse,
    summary="Get persona details",
    description="Get detailed information about a specific persona.",
    responses={
        404: {"model": ErrorResponse, "description": "Persona not found"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def get_persona(persona_id: str) -> PersonaResponse:
    """Get persona by ID."""
    repo = get_persona_repository()
    persona_uuid = parse_uuid(persona_id, "persona")
    persona = await repo.get(persona_uuid)

    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    return PersonaResponse(
        id=str(persona.id),
        name=persona.name,
        description=persona.description,
        aggression=persona.aggression,
        patience=persona.patience,
        verbosity=persona.verbosity,
        traits=persona.traits,
        tts_provider=persona.tts_provider,
        tts_config=persona.tts_config,
        preview_audio_url=persona.preview_audio_url,
        preview_audio_text=persona.preview_audio_text,
        preview_audio_status=persona.preview_audio_status,
        preview_audio_error=persona.preview_audio_error,
        metadata=persona.metadata,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
        created_by=persona.created_by,
        is_active=persona.is_active,
        is_default=persona.is_default,
    )


@router.put(
    "/{persona_id}",
    response_model=PersonaResponse,
    summary="Update persona",
    description="Update an existing persona. Clears preview audio on any update.",
    responses={
        404: {"model": ErrorResponse, "description": "Persona not found"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def update_persona(
    persona_id: str,
    request: PersonaUpdateRequest,
) -> PersonaResponse:
    """Update a persona. Clears preview audio on any update."""
    repo = get_persona_repository()
    persona_uuid = parse_uuid(persona_id, "persona")

    # Get existing persona
    existing = await repo.get(persona_uuid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    # Delete existing preview audio file if it exists (best-effort)
    if existing.preview_audio_url:
        try:
            audio_storage = get_audio_storage()
            await audio_storage.delete_by_url(existing.preview_audio_url)
        except Exception:
            # Best-effort cleanup - continue even if deletion fails
            pass

    # Get only explicitly set fields (excludes None defaults)
    update_kwargs = request.model_dump(exclude_unset=True)

    # Add required ID
    update_kwargs["persona_id"] = persona_uuid

    # Always clear preview audio fields on any update
    update_kwargs["preview_audio_url"] = None
    update_kwargs["preview_audio_text"] = None
    update_kwargs["preview_audio_status"] = None
    update_kwargs["preview_audio_error"] = None

    # Update persona
    try:
        persona = await repo.update(**update_kwargs)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    return PersonaResponse(
        id=str(persona.id),
        name=persona.name,
        description=persona.description,
        aggression=persona.aggression,
        patience=persona.patience,
        verbosity=persona.verbosity,
        traits=persona.traits,
        tts_provider=persona.tts_provider,
        tts_config=persona.tts_config,
        preview_audio_url=persona.preview_audio_url,
        preview_audio_text=persona.preview_audio_text,
        preview_audio_status=persona.preview_audio_status,
        preview_audio_error=persona.preview_audio_error,
        metadata=persona.metadata,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
        created_by=persona.created_by,
        is_active=persona.is_active,
        is_default=persona.is_default,
    )


@router.delete(
    "/{persona_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete persona",
    description=(
        "Permanently delete a persona. "
        "Cannot delete the default persona or the last remaining persona."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Cannot delete default or last persona"},
        404: {"model": ErrorResponse, "description": "Persona not found"},
        409: {"model": ErrorResponse, "description": "Persona is in use by test scenarios"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def delete_persona(persona_id: str) -> None:
    """Delete a persona.

    Validation rules:
    - Cannot delete the default persona
    - Cannot delete the last remaining persona
    - Cannot delete a persona that is used by test scenarios
    """
    from asyncpg.exceptions import ForeignKeyViolationError

    repo = get_persona_repository()
    persona_uuid = parse_uuid(persona_id, "persona")

    # Get the persona to check if it's the default
    persona = await repo.get(persona_uuid)
    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    # Check if this is the default persona
    if persona.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the default persona. Set another persona as default first.",
        )

    # Check if this is the last persona
    persona_count = await repo.count()
    if persona_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the last remaining persona. At least one persona must exist.",
        )

    # Delete preview audio file if it exists (best-effort)
    if persona.preview_audio_url:
        try:
            audio_storage = get_audio_storage()
            await audio_storage.delete_by_url(persona.preview_audio_url)
        except Exception:
            # Best-effort cleanup - continue even if deletion fails
            pass

    try:
        deleted = await repo.delete(persona_uuid)
    except ForeignKeyViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete persona. It is used by one or more test scenarios.",
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )


@router.post(
    "/{persona_id}/set-default",
    response_model=PersonaResponse,
    summary="Set persona as default",
    description="Set a persona as the default fallback persona. Unsets any previous default.",
    responses={
        404: {"model": ErrorResponse, "description": "Persona not found"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def set_persona_default(persona_id: str) -> PersonaResponse:
    """Set a persona as the default.

    This atomically unsets any existing default persona and sets the specified
    persona as the new default.
    """
    repo = get_persona_repository()
    persona_uuid = parse_uuid(persona_id, "persona")

    # Check if persona exists
    existing = await repo.get(persona_uuid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    # Set as default
    persona = await repo.set_default(persona_uuid)

    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set persona as default",
        )

    return PersonaResponse(
        id=str(persona.id),
        name=persona.name,
        description=persona.description,
        aggression=persona.aggression,
        patience=persona.patience,
        verbosity=persona.verbosity,
        traits=persona.traits,
        tts_provider=persona.tts_provider,
        tts_config=persona.tts_config,
        preview_audio_url=persona.preview_audio_url,
        preview_audio_text=persona.preview_audio_text,
        preview_audio_status=persona.preview_audio_status,
        preview_audio_error=persona.preview_audio_error,
        metadata=persona.metadata,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
        created_by=persona.created_by,
        is_active=persona.is_active,
        is_default=persona.is_default,
    )


@router.get(
    "/{persona_id}/preview-audio",
    response_model=PersonaAudioPreviewResponse,
    summary="Get persona preview audio",
    description="Get pregenerated preview audio URL for a persona.",
    responses={
        404: {"model": ErrorResponse, "description": "Persona or preview audio not found"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def get_persona_preview_audio(persona_id: str) -> PersonaAudioPreviewResponse:
    """Get pregenerated preview audio for a persona."""
    repo = get_persona_repository()
    persona_uuid = parse_uuid(persona_id, "persona")

    # Get persona from database
    persona = await repo.get(persona_uuid)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    if not persona.preview_audio_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview audio not available for this persona",
        )

    # Get presigned URL if S3, otherwise return URL as-is
    audio_url = await get_presigned_url_for_audio(persona.preview_audio_url)

    # Return stored preview audio URL
    return PersonaAudioPreviewResponse(
        audio_url=audio_url,
        text=persona.preview_audio_text or DEFAULT_PREVIEW_TEXT,
        format="audio/mpeg",
    )


@router.get(
    "/{persona_id}/preview-audio/status",
    response_model=PreviewAudioStatusResponse,
    summary="Get preview audio generation status",
    description="Check the status of preview audio generation for a persona.",
    responses={
        404: {"model": ErrorResponse, "description": "Persona not found"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def get_preview_audio_status(persona_id: str) -> PreviewAudioStatusResponse:
    """Get preview audio generation status for a persona."""
    repo = get_persona_repository()
    persona_uuid = parse_uuid(persona_id, "persona")

    persona = await repo.get(persona_uuid)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    audio_url = None
    if persona.preview_audio_status == "ready" and persona.preview_audio_url:
        audio_url = await get_presigned_url_for_audio(persona.preview_audio_url)

    return PreviewAudioStatusResponse(
        status=persona.preview_audio_status,
        audio_url=audio_url,
        error_message=persona.preview_audio_error,
    )


@router.post(
    "/{persona_id}/preview-audio",
    response_model=PreviewAudioStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate persona preview audio",
    description="Start async preview audio generation for a persona.",
    responses={
        202: {"model": PreviewAudioStatusResponse, "description": "Generation started"},
        404: {"model": ErrorResponse, "description": "Persona not found"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def generate_persona_preview_audio(
    persona_id: str,
    background_tasks: BackgroundTasks,
) -> PreviewAudioStatusResponse:
    """Start async preview audio generation for a persona."""
    repo = get_persona_repository()
    persona_uuid = parse_uuid(persona_id, "persona")

    persona = await repo.get(persona_uuid)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    if persona.preview_audio_status == "generating":
        return PreviewAudioStatusResponse(
            status="generating",
            audio_url=None,
            error_message=None,
        )

    await repo.update(
        persona_id=persona_uuid,
        preview_audio_status="generating",
        preview_audio_error=None,
    )

    preview_text = persona.preview_audio_text or DEFAULT_PREVIEW_TEXT

    background_tasks.add_task(
        _generate_preview_audio_background,
        persona_id,
        persona.tts_provider,
        persona.tts_config or {},
        preview_text,
    )

    return PreviewAudioStatusResponse(
        status="generating",
        audio_url=None,
        error_message=None,
    )


@router.patch(
    "/{persona_id}/active",
    response_model=PersonaResponse,
    summary="Enable or disable persona",
    description="Enable or disable a persona by setting its active status.",
    responses={
        404: {"model": ErrorResponse, "description": "Persona not found"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def set_persona_active(
    persona_id: str,
    request: PersonaActiveRequest,
) -> PersonaResponse:
    """Enable or disable a persona."""
    repo = get_persona_repository()
    persona_uuid = parse_uuid(persona_id, "persona")

    # Get existing persona to verify it exists
    existing = await repo.get(persona_uuid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    # Update is_active status
    try:
        persona = await repo.update(
            persona_id=persona_uuid,
            is_active=request.is_active,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    return PersonaResponse(
        id=str(persona.id),
        name=persona.name,
        description=persona.description,
        aggression=persona.aggression,
        patience=persona.patience,
        verbosity=persona.verbosity,
        traits=persona.traits,
        tts_provider=persona.tts_provider,
        tts_config=persona.tts_config,
        preview_audio_url=persona.preview_audio_url,
        preview_audio_text=persona.preview_audio_text,
        preview_audio_status=persona.preview_audio_status,
        preview_audio_error=persona.preview_audio_error,
        metadata=persona.metadata,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
        created_by=persona.created_by,
        is_active=persona.is_active,
        is_default=persona.is_default,
    )
