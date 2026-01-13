"""Persona management routes."""

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from voiceobs.server.db.repositories.persona import PersonaRepository
from voiceobs.server.dependencies import (
    get_audio_storage,
    get_persona_repository,
    is_using_postgres,
)
from voiceobs.server.models import (
    ErrorResponse,
    PersonaAudioPreviewResponse,
    PersonaCreateRequest,
    PersonaListItem,
    PersonaResponse,
    PersonasListResponse,
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


def get_persona_repo() -> PersonaRepository:
    """Dependency to get persona repository.

    Returns:
        Persona repository.

    Raises:
        HTTPException: If repository is not available.
    """
    if not is_using_postgres():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Persona API requires PostgreSQL database",
        )

    repo = get_persona_repository()
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Persona repository not available",
        )
    return repo


@router.post(
    "",
    response_model=PersonaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create persona",
    description="Create a new persona and generate preview audio.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def create_persona(
    request: PersonaCreateRequest,
) -> PersonaResponse:
    """Create a new persona and optionally generate preview audio."""
    repo = get_persona_repo()

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

    # Generate preview audio using TTS service only if TTS provider and config are provided
    preview_audio_url = None
    if tts_provider and tts_config:
        try:
            tts_service = TTSServiceFactory.create(tts_provider)
            audio_bytes, mime_type, _ = await tts_service.synthesize(
                DEFAULT_PREVIEW_TEXT, tts_config
            )

            # Store audio - we'll use a temporary prefix and update after persona creation
            audio_storage = get_audio_storage()
            preview_audio_url = await audio_storage.store_audio(
                audio_bytes,
                prefix="personas/preview/temp",
                content_type=mime_type,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    # Create persona first to get the persona ID
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
            preview_audio_url=preview_audio_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT if preview_audio_url else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # If we generated preview audio, update the URL with the correct persona ID
    if preview_audio_url and persona:
        # Note: The audio was already stored, but we could move it to the correct location
        # For now, we'll leave it as is since the storage handles the prefix
        pass

    # Get presigned URL if S3, otherwise return URL as-is
    response_preview_audio_url = await get_presigned_url_for_audio(persona.preview_audio_url)

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
        preview_audio_url=response_preview_audio_url,
        preview_audio_text=persona.preview_audio_text,
        metadata=persona.metadata,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
        created_by=persona.created_by,
        is_active=persona.is_active,
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
    repo = get_persona_repo()
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
                is_active=persona.is_active,
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
    repo = get_persona_repo()
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
        metadata=persona.metadata,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
        created_by=persona.created_by,
        is_active=persona.is_active,
    )


@router.put(
    "/{persona_id}",
    response_model=PersonaResponse,
    summary="Update persona",
    description="Update an existing persona. Regenerates preview audio if TTS settings changed.",
    responses={
        404: {"model": ErrorResponse, "description": "Persona not found"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def update_persona(
    persona_id: str,
    request: PersonaUpdateRequest,
) -> PersonaResponse:
    """Update a persona. Regenerates preview audio if TTS settings change."""
    repo = get_persona_repo()
    persona_uuid = parse_uuid(persona_id, "persona")

    # Get existing persona
    existing = await repo.get(persona_uuid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    # Check if TTS settings changed - regenerate preview audio if so
    preview_audio_url = existing.preview_audio_url
    preview_audio_text = existing.preview_audio_text

    tts_changed = (
        request.tts_provider is not None and request.tts_provider != existing.tts_provider
    ) or (request.tts_config is not None and request.tts_config != existing.tts_config)

    if tts_changed:
        # Regenerate preview audio
        tts_provider = request.tts_provider or existing.tts_provider
        tts_config = request.tts_config or existing.tts_config

        try:
            tts_service = TTSServiceFactory.create(tts_provider)
            audio_bytes, mime_type, _ = await tts_service.synthesize(
                DEFAULT_PREVIEW_TEXT, tts_config
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        # Store new audio using persona ID in the prefix
        audio_storage = get_audio_storage()
        preview_audio_url = await audio_storage.store_audio(
            audio_bytes,
            prefix=f"personas/preview/{persona_id}",
            content_type=mime_type,
        )
        preview_audio_text = DEFAULT_PREVIEW_TEXT

    # Update persona
    try:
        persona = await repo.update(
            persona_id=persona_uuid,
            name=request.name,
            description=request.description,
            aggression=request.aggression,
            patience=request.patience,
            verbosity=request.verbosity,
            traits=request.traits,
            tts_provider=request.tts_provider,
            tts_config=request.tts_config,
            preview_audio_url=preview_audio_url if tts_changed else None,
            preview_audio_text=preview_audio_text if tts_changed else None,
            metadata=request.metadata,
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
        metadata=persona.metadata,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
        created_by=persona.created_by,
        is_active=persona.is_active,
    )


@router.delete(
    "/{persona_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete persona",
    description="Delete a persona (soft delete by default).",
    responses={
        404: {"model": ErrorResponse, "description": "Persona not found"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def delete_persona(
    persona_id: str,
    soft: bool = Query(True, description="Soft delete (default) or hard delete"),
) -> None:
    """Delete a persona."""
    repo = get_persona_repo()
    persona_uuid = parse_uuid(persona_id, "persona")
    deleted = await repo.delete(persona_uuid, soft=soft)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
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
    repo = get_persona_repo()
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


@router.post(
    "/{persona_id}/preview-audio",
    response_model=PersonaAudioPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate persona preview audio",
    description="Generate and store preview audio for a persona using its TTS configuration.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request or TTS generation failed"},
        404: {"model": ErrorResponse, "description": "Persona not found"},
        501: {"model": ErrorResponse, "description": "Persona API requires PostgreSQL database"},
    },
)
async def generate_persona_preview_audio(persona_id: str) -> PersonaAudioPreviewResponse:
    """Generate preview audio for a persona and update the persona record.

    This endpoint:
    1. Retrieves the persona from the database
    2. Uses the persona's TTS provider and configuration to synthesize audio
    3. Uses the persona's preview_audio_text (or DEFAULT_PREVIEW_TEXT if not set)
    4. Stores the generated audio
    5. Updates the persona with the new preview_audio_url
    6. Returns the preview audio information
    """
    repo = get_persona_repo()
    persona_uuid = parse_uuid(persona_id, "persona")

    # Get persona from database
    persona = await repo.get(persona_uuid)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{persona_id}' not found",
        )

    # Determine preview text to use
    preview_text = persona.preview_audio_text or DEFAULT_PREVIEW_TEXT

    # Generate preview audio using TTS service
    try:
        tts_service = TTSServiceFactory.create(persona.tts_provider)
        audio_bytes, mime_type, _ = await tts_service.synthesize(
            preview_text, persona.tts_config or {}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate preview audio: {str(e)}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS service error: {str(e)}",
        ) from e

    # Store audio using persona ID in the prefix
    audio_storage = get_audio_storage()
    try:
        preview_audio_url = await audio_storage.store_audio(
            audio_bytes,
            prefix=f"personas/preview/{persona.id}",
            content_type=mime_type,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store preview audio: {str(e)}",
        ) from e

    # Update persona with preview audio URL and text
    try:
        updated_persona = await repo.update(
            persona_id=persona_uuid,
            preview_audio_url=preview_audio_url,
            preview_audio_text=preview_text,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update persona: {str(e)}",
        ) from e

    if updated_persona is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update persona with preview audio URL",
        )

    # Get presigned URL if S3, otherwise return URL as-is
    audio_url = await get_presigned_url_for_audio(preview_audio_url)

    # Return preview audio information
    return PersonaAudioPreviewResponse(
        audio_url=audio_url,
        text=preview_text,
        format=mime_type,
    )


class PersonaActiveRequest(BaseModel):
    """Request model for updating persona active status."""

    is_active: bool = Field(..., description="Whether the persona should be active")


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
    repo = get_persona_repo()
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
        metadata=persona.metadata,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
        created_by=persona.created_by,
        is_active=persona.is_active,
    )
