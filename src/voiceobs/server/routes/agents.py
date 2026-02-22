"""Agent management routes (org-scoped)."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from voiceobs.server.auth.context import AuthContext, require_org_membership
from voiceobs.server.dependencies import (
    get_agent_repository,
    get_agent_verification_service,
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

router = APIRouter(prefix="/api/v1/orgs/{org_id}/agents", tags=["Agents"])


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create agent",
    description="Create a new agent within an organization and initiate connection verification.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        403: {"model": ErrorResponse, "description": "Not a member of this organization"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        501: {
            "model": ErrorResponse,
            "description": "Agent verification requires PostgreSQL database",
        },
    },
)
async def create_agent(
    org_id: UUID,
    request: AgentCreateRequest,
    auth: AuthContext = Depends(require_org_membership),
) -> AgentResponse:
    """Create a new agent within an organization and start verification in background."""
    repo = get_agent_repository()

    # Build contact_info from request (already validated in Pydantic model)
    contact_info = request.contact_info or {}

    # Create agent with 'saved' status
    try:
        agent = await repo.create(
            org_id=org_id,
            name=request.name,
            agent_type=request.agent_type,
            contact_info=contact_info,
            goal=request.goal,
            supported_intents=request.supported_intents,
            context=request.context,
            metadata=request.metadata,
            created_by=request.created_by,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Start verification in background
    logger.info(f"Starting verification for agent {agent.id} (name: {agent.name}) in org {org_id}")
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
    await verification_service.verify_agent_background(agent.id, agent.org_id)

    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        agent_type=agent.agent_type,
        contact_info=agent.contact_info,
        phone_number=agent.phone_number,
        web_url=agent.web_url,
        goal=agent.goal,
        supported_intents=agent.supported_intents,
        context=agent.context,
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
    description="Get a list of all agents within an organization with optional filtering.",
    responses={
        403: {"model": ErrorResponse, "description": "Not a member of this organization"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        501: {"model": ErrorResponse, "description": "Agent API requires PostgreSQL database"},
    },
)
async def list_agents(
    org_id: UUID,
    auth: AuthContext = Depends(require_org_membership),
    connection_status: str | None = Query(None, description="Filter by connection status"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int | None = Query(None, ge=1, le=100, description="Maximum number of results"),
    offset: int | None = Query(None, ge=0, description="Number of results to skip"),
) -> AgentsListResponse:
    """List all agents within an organization with optional filtering."""
    repo = get_agent_repository()
    agents = await repo.list_all(
        org_id=org_id,
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
    description="Get detailed information about a specific agent within an organization.",
    responses={
        403: {"model": ErrorResponse, "description": "Not a member of this organization"},
        404: {"model": ErrorResponse, "description": "Agent not found or organization not found"},
        501: {
            "model": ErrorResponse,
            "description": "Agent verification requires PostgreSQL database",
        },
    },
)
async def get_agent(
    org_id: UUID,
    agent_id: str,
    auth: AuthContext = Depends(require_org_membership),
) -> AgentResponse:
    """Get agent by ID within an organization."""
    repo = get_agent_repository()
    agent_uuid = parse_uuid(agent_id, "agent")
    agent = await repo.get(agent_uuid, org_id)

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in organization",
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
        context=agent.context,
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
    description="Update an existing agent within an organization.",
    responses={
        403: {"model": ErrorResponse, "description": "Not a member of this organization"},
        404: {"model": ErrorResponse, "description": "Agent not found or organization not found"},
        501: {
            "model": ErrorResponse,
            "description": "Agent verification requires PostgreSQL database",
        },
    },
)
async def update_agent(
    org_id: UUID,
    agent_id: str,
    request: AgentUpdateRequest,
    auth: AuthContext = Depends(require_org_membership),
) -> AgentResponse:
    """Update an agent. Re-verifies if phone number or web_url changed."""
    repo = get_agent_repository()
    agent_uuid = parse_uuid(agent_id, "agent")

    # Get existing agent
    existing = await repo.get(agent_uuid, org_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in organization",
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

    # Remove agent_id from kwargs (passed as positional)
    update_kwargs.pop("agent_id", None)
    if contact_info_update is not None:
        update_kwargs["contact_info"] = contact_info_update

    # Update agent
    try:
        agent = await repo.update(agent_uuid, org_id, **update_kwargs)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in organization",
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
        await verification_service.verify_agent_background(agent_uuid, org_id)
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
        context=agent.context,
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
    description="Permanently delete an agent within an organization.",
    responses={
        403: {"model": ErrorResponse, "description": "Not a member of this organization"},
        404: {"model": ErrorResponse, "description": "Agent not found or organization not found"},
        501: {
            "model": ErrorResponse,
            "description": "Agent verification requires PostgreSQL database",
        },
    },
)
async def delete_agent(
    org_id: UUID,
    agent_id: str,
    auth: AuthContext = Depends(require_org_membership),
) -> None:
    """Delete an agent."""
    repo = get_agent_repository()
    agent_uuid = parse_uuid(agent_id, "agent")
    deleted = await repo.delete(agent_uuid, org_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in organization",
        )


@router.get(
    "/{agent_id}/verification-status",
    summary="Get verification status",
    description="Get detailed verification status for an agent within an organization.",
    responses={
        403: {"model": ErrorResponse, "description": "Not a member of this organization"},
        404: {"model": ErrorResponse, "description": "Agent not found or organization not found"},
        501: {"model": ErrorResponse, "description": "Requires PostgreSQL database"},
    },
)
async def get_verification_status(
    org_id: UUID,
    agent_id: str,
    auth: AuthContext = Depends(require_org_membership),
):
    """Get verification status for an agent."""
    repo = get_agent_repository()
    agent_uuid = parse_uuid(agent_id, "agent")
    agent = await repo.get(agent_uuid, org_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in organization",
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
    description="Manually trigger agent connection verification within an organization.",
    responses={
        403: {"model": ErrorResponse, "description": "Not a member of this organization"},
        404: {"model": ErrorResponse, "description": "Agent not found or organization not found"},
        501: {
            "model": ErrorResponse,
            "description": "Agent verification requires PostgreSQL database",
        },
    },
)
async def verify_agent(
    org_id: UUID,
    agent_id: str,
    request: AgentVerificationRequest = AgentVerificationRequest(),
    auth: AuthContext = Depends(require_org_membership),
) -> AgentResponse:
    """Manually trigger agent verification."""
    repo = get_agent_repository()
    agent_uuid = parse_uuid(agent_id, "agent")
    agent = await repo.get(agent_uuid, org_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in organization",
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
            context=agent.context,
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
    await verification_service.verify_agent_background(agent_uuid, org_id, force=request.force)

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
        context=agent.context,
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
