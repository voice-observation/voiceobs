"""Persona management routes."""

from fastapi import APIRouter, HTTPException, Query, status

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

router = APIRouter(prefix="/api/v1/personas", tags=["Personas"])

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
    """Create a new persona and generate preview audio."""
    repo = get_persona_repo()

    # Generate preview audio using TTS service
    try:
        tts_service = TTSServiceFactory.create(request.tts_provider)
        audio_bytes, mime_type, _ = await tts_service.synthesize(
            DEFAULT_PREVIEW_TEXT, request.tts_config
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Store audio
    audio_storage = get_audio_storage()
    # Generate a unique filename prefix using persona name
    preview_audio_url = await audio_storage.save(
        audio_bytes,
        conversation_id=f"persona-{request.name}",
        audio_type="preview",
    )

    # Create persona with preview audio URL
    try:
        persona = await repo.create(
            name=request.name,
            aggression=request.aggression,
            patience=request.patience,
            verbosity=request.verbosity,
            tts_provider=request.tts_provider,
            tts_config=request.tts_config,
            description=request.description,
            traits=request.traits,
            metadata=request.metadata,
            created_by=request.created_by,
            preview_audio_url=preview_audio_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
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
    is_active: bool | None = Query(True, description="Filter by active status"),
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
    ) or (
        request.tts_config is not None and request.tts_config != existing.tts_config
    )

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

        # Store new audio
        audio_storage = get_audio_storage()
        preview_audio_url = await audio_storage.save(
            audio_bytes,
            conversation_id=f"persona-{persona_id}",
            audio_type="preview",
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

    # Return stored preview audio URL
    return PersonaAudioPreviewResponse(
        audio_url=persona.preview_audio_url,
        text=persona.preview_audio_text or DEFAULT_PREVIEW_TEXT,
        format="audio/mpeg",
    )
