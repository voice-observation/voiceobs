"""Agent management routes."""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from voiceobs.server.db.repositories.agent import AgentRepository
from voiceobs.server.dependencies import (
    get_agent_repository,
    get_agent_verification_service,
    is_using_postgres,
)
from voiceobs.server.models import (
    AgentCreateRequest,
    AgentListItem,
    AgentResponse,
    AgentsListResponse,
    AgentUpdateRequest,
    AgentVerificationRequest,
    ErrorResponse,
)
from voiceobs.server.utils import parse_uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])


def get_agent_repo() -> AgentRepository:
    """Dependency to get agent repository.

    Returns:
        Agent repository.

    Raises:
        HTTPException: If repository is not available.
    """
    if not is_using_postgres():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Agent API requires PostgreSQL database",
        )

    repo = get_agent_repository()
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent repository not available",
        )
    return repo


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create agent",
    description="Create a new agent and initiate connection verification.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        501: {
            "model": ErrorResponse,
            "description": "Agent verification requires PostgreSQL database",
        },
    },
)
async def create_agent(
    request: AgentCreateRequest,
) -> AgentResponse:
    """Create a new agent and start verification in background."""
    repo = get_agent_repo()

    # Build contact_info from request (already validated in Pydantic model)
    contact_info = request.contact_info or {}

    # Create agent with 'saved' status
    try:
        agent = await repo.create(
            name=request.name,
            agent_type=request.agent_type,
            contact_info=contact_info,
            goal=request.goal,
            supported_intents=request.supported_intents,
            metadata=request.metadata,
            created_by=request.created_by,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Start verification in background
    logger.info(f"Starting verification for agent {agent.id} (name: {agent.name})")
    verification_service = get_agent_verification_service()
    if not verification_service:
        logger.error(
            f"Verification service is None - cannot verify agent {agent.id}. "
            "PostgreSQL must be configured."
        )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Agent verification requires PostgreSQL database. "
                "Configure server.database_url in voiceobs.yaml or "
                "set VOICEOBS_DATABASE_URL environment variable."
            ),
        )

    logger.info(
        f"Verification service available, triggering background verification for agent {agent.id}"
    )
    await verification_service.verify_agent_background(agent.id)

    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        agent_type=agent.agent_type,
        contact_info=agent.contact_info,
        phone_number=agent.phone_number,
        web_url=agent.web_url,
        goal=agent.goal,
        supported_intents=agent.supported_intents,
        connection_status=agent.connection_status,
        verification_attempts=agent.verification_attempts,
        last_verification_at=agent.last_verification_at,
        verification_error=agent.verification_error,
        verification_reasoning=agent.verification_reasoning,
        verification_transcript=agent.verification_transcript,
        metadata=agent.metadata,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        created_by=agent.created_by,
        is_active=agent.is_active,
    )


@router.get(
    "",
    response_model=AgentsListResponse,
    summary="List agents",
    description="Get a list of all agents with optional filtering.",
    responses={
        501: {"model": ErrorResponse, "description": "Agent API requires PostgreSQL database"},
    },
)
async def list_agents(
    connection_status: str | None = Query(None, description="Filter by connection status"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int | None = Query(None, ge=1, le=100, description="Maximum number of results"),
    offset: int | None = Query(None, ge=0, description="Number of results to skip"),
) -> AgentsListResponse:
    """List all agents with optional filtering."""
    repo = get_agent_repo()
    agents = await repo.list_all(
        connection_status=connection_status,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )

    return AgentsListResponse(
        count=len(agents),
        agents=[
            AgentListItem(
                id=str(agent.id),
                name=agent.name,
                agent_type=agent.agent_type,
                phone_number=agent.phone_number,
                web_url=agent.web_url,
                goal=agent.goal,
                connection_status=agent.connection_status,
                is_active=agent.is_active,
                created_at=agent.created_at,
            )
            for agent in agents
        ],
    )


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Get agent details",
    description="Get detailed information about a specific agent.",
    responses={
        404: {"model": ErrorResponse, "description": "Agent not found"},
        501: {
            "model": ErrorResponse,
            "description": "Agent verification requires PostgreSQL database",
        },
    },
)
async def get_agent(agent_id: str) -> AgentResponse:
    """Get agent by ID."""
    repo = get_agent_repo()
    agent_uuid = parse_uuid(agent_id, "agent")
    agent = await repo.get(agent_uuid)

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        agent_type=agent.agent_type,
        contact_info=agent.contact_info,
        phone_number=agent.phone_number,
        web_url=agent.web_url,
        goal=agent.goal,
        supported_intents=agent.supported_intents,
        connection_status=agent.connection_status,
        verification_attempts=agent.verification_attempts,
        last_verification_at=agent.last_verification_at,
        verification_error=agent.verification_error,
        verification_reasoning=agent.verification_reasoning,
        verification_transcript=agent.verification_transcript,
        metadata=agent.metadata,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        created_by=agent.created_by,
        is_active=agent.is_active,
    )


@router.put(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Update agent",
    description="Update an existing agent.",
    responses={
        404: {"model": ErrorResponse, "description": "Agent not found"},
        501: {
            "model": ErrorResponse,
            "description": "Agent verification requires PostgreSQL database",
        },
    },
)
async def update_agent(
    agent_id: str,
    request: AgentUpdateRequest,
) -> AgentResponse:
    """Update an agent. Re-verifies if phone number or web_url changed."""
    repo = get_agent_repo()
    agent_uuid = parse_uuid(agent_id, "agent")

    # Get existing agent
    existing = await repo.get(agent_uuid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    # Build contact_info update if provided
    contact_info_update = None
    if request.contact_info is not None:
        # Merge with existing contact_info
        contact_info_update = {**existing.contact_info, **request.contact_info}
    elif request.phone_number is not None or request.web_url is not None:
        # Update from convenience fields
        contact_info_update = existing.contact_info.copy()
        if request.phone_number is not None:
            contact_info_update["phone_number"] = request.phone_number
        if request.web_url is not None:
            contact_info_update["web_url"] = request.web_url

    # Get only explicitly set fields (excludes None defaults)
    update_kwargs = request.model_dump(exclude_unset=True)

    # Remove convenience fields that aren't direct repo params
    update_kwargs.pop("phone_number", None)
    update_kwargs.pop("web_url", None)
    update_kwargs.pop("contact_info", None)

    # Add required ID and computed contact_info
    update_kwargs["agent_id"] = agent_uuid
    if contact_info_update is not None:
        update_kwargs["contact_info"] = contact_info_update

    # Update agent
    try:
        agent = await repo.update(**update_kwargs)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    # Re-verify if contact_info changed
    verification_service = get_agent_verification_service()
    contact_info_changed = contact_info_update and contact_info_update != existing.contact_info
    logger.info(
        f"Update agent {agent_id}: verification_service={verification_service is not None}, "
        f"contact_info_changed={contact_info_changed}"
    )
    if contact_info_changed:
        if not verification_service:
            logger.error(
                f"Verification service is None - cannot re-verify agent {agent_id}. "
                "PostgreSQL must be configured."
            )
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=(
                    "Agent verification requires PostgreSQL database. "
                    "Configure server.database_url in voiceobs.yaml or "
                    "set VOICEOBS_DATABASE_URL environment variable."
                ),
            )

        logger.info(
            f"Contact info changed, triggering background verification for agent {agent_id}"
        )
        await verification_service.verify_agent_background(agent_uuid)
    else:
        logger.debug(f"Contact info unchanged, skipping verification for agent {agent_id}")

    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        agent_type=agent.agent_type,
        contact_info=agent.contact_info,
        phone_number=agent.phone_number,
        web_url=agent.web_url,
        goal=agent.goal,
        supported_intents=agent.supported_intents,
        connection_status=agent.connection_status,
        verification_attempts=agent.verification_attempts,
        last_verification_at=agent.last_verification_at,
        verification_error=agent.verification_error,
        verification_reasoning=agent.verification_reasoning,
        verification_transcript=agent.verification_transcript,
        metadata=agent.metadata,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        created_by=agent.created_by,
        is_active=agent.is_active,
    )


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete agent",
    description="Permanently delete an agent.",
    responses={
        404: {"model": ErrorResponse, "description": "Agent not found"},
        501: {
            "model": ErrorResponse,
            "description": "Agent verification requires PostgreSQL database",
        },
    },
)
async def delete_agent(agent_id: str) -> None:
    """Delete an agent."""
    repo = get_agent_repo()
    agent_uuid = parse_uuid(agent_id, "agent")
    deleted = await repo.delete(agent_uuid)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )


@router.get(
    "/{agent_id}/verification-status",
    summary="Get verification status",
    description="Get detailed verification status for an agent.",
    responses={
        404: {"model": ErrorResponse, "description": "Agent not found"},
        501: {"model": ErrorResponse, "description": "Requires PostgreSQL database"},
    },
)
async def get_verification_status(agent_id: str):
    """Get verification status for an agent."""
    repo = get_agent_repo()
    agent_uuid = parse_uuid(agent_id, "agent")
    agent = await repo.get(agent_uuid)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    return {
        "agent_id": str(agent.id),
        "status": agent.connection_status,
        "attempts": agent.verification_attempts,
        "reasoning": agent.verification_reasoning,
        "transcript": agent.verification_transcript,
        "last_verification_at": agent.last_verification_at,
        "error": agent.verification_error,
    }


@router.post(
    "/{agent_id}/verify",
    response_model=AgentResponse,
    summary="Verify agent connection",
    description="Manually trigger agent connection verification.",
    responses={
        404: {"model": ErrorResponse, "description": "Agent not found"},
        501: {
            "model": ErrorResponse,
            "description": "Agent verification requires PostgreSQL database",
        },
    },
)
async def verify_agent(
    agent_id: str,
    request: AgentVerificationRequest = AgentVerificationRequest(),
) -> AgentResponse:
    """Manually trigger agent verification."""
    repo = get_agent_repo()
    agent_uuid = parse_uuid(agent_id, "agent")
    agent = await repo.get(agent_uuid)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    if not request.force and agent.connection_status == "verified":
        # Already verified, return current status
        return AgentResponse(
            id=str(agent.id),
            name=agent.name,
            agent_type=agent.agent_type,
            contact_info=agent.contact_info,
            phone_number=agent.phone_number,
            web_url=agent.web_url,
            goal=agent.goal,
            supported_intents=agent.supported_intents,
            connection_status=agent.connection_status,
            verification_attempts=agent.verification_attempts,
            last_verification_at=agent.last_verification_at,
            verification_error=agent.verification_error,
            verification_reasoning=agent.verification_reasoning,
            verification_transcript=agent.verification_transcript,
            metadata=agent.metadata,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            created_by=agent.created_by,
            is_active=agent.is_active,
        )

    # Start verification in background
    logger.info(f"Manual verification requested for agent {agent_id} (force={request.force})")
    verification_service = get_agent_verification_service()
    if not verification_service:
        logger.error(
            f"Verification service is None - cannot verify agent {agent_id}. "
            "PostgreSQL must be configured."
        )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Agent verification requires PostgreSQL database. "
                "Configure server.database_url in voiceobs.yaml or "
                "set VOICEOBS_DATABASE_URL environment variable."
            ),
        )

    logger.info(
        f"Verification service available, triggering background verification for agent {agent_id}"
    )
    await verification_service.verify_agent_background(agent_uuid, force=request.force)

    # Return current status (will be updated asynchronously)
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        agent_type=agent.agent_type,
        contact_info=agent.contact_info,
        phone_number=agent.phone_number,
        web_url=agent.web_url,
        goal=agent.goal,
        supported_intents=agent.supported_intents,
        connection_status=agent.connection_status,
        verification_attempts=agent.verification_attempts,
        last_verification_at=agent.last_verification_at,
        verification_error=agent.verification_error,
        verification_reasoning=agent.verification_reasoning,
        verification_transcript=agent.verification_transcript,
        metadata=agent.metadata,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        created_by=agent.created_by,
        is_active=agent.is_active,
    )
