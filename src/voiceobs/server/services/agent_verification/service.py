"""Agent verification service for orchestrating agent verification."""

import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from voiceobs.server.db.repositories.agent import AgentRepository
from voiceobs.server.services.agent_verification.factory import AgentVerifierFactory

logger = logging.getLogger(__name__)


class AgentVerificationService:
    """Service for verifying agent connections.

    This service orchestrates the verification process by:
    1. Getting the agent from the repository
    2. Selecting the appropriate verifier based on agent type
    3. Running the verification
    4. Updating the agent status in the database
    """

    def __init__(self, agent_repository: AgentRepository) -> None:
        """Initialize the agent verification service.

        Args:
            agent_repository: Repository for agent database operations
        """
        self._agent_repo = agent_repository

    async def verify_agent(self, agent_id: UUID, force: bool = False) -> None:
        """Verify an agent's connection asynchronously.

        This method updates the agent's connection status based on verification results.
        It should be called in a background task.

        Args:
            agent_id: UUID of the agent to verify
            force: If True, re-verify even if already verified
        """
        try:
            # Get agent from repository
            agent = await self._agent_repo.get(agent_id)
            if not agent:
                logger.error(f"Agent {agent_id} not found for verification")
                return

            # Skip if already verified and not forcing
            if not force and agent.connection_status == "verified":
                logger.info(f"Agent {agent_id} already verified, skipping")
                return

            # Update status to "connecting"
            await self._agent_repo.update_status(
                agent_id=agent_id,
                connection_status="connecting",
                verification_attempts=agent.verification_attempts + 1,
                last_verification_at=datetime.now(timezone.utc),
                verification_error=None,
            )

            # Get appropriate verifier for agent type
            try:
                verifier = AgentVerifierFactory.create(agent.agent_type)
            except ValueError as e:
                error_msg = f"Unsupported agent type: {agent.agent_type}"
                logger.error(f"{error_msg} for agent {agent_id}")
                await self._agent_repo.update_status(
                    agent_id=agent_id,
                    connection_status="failed",
                    verification_error=error_msg,
                )
                return

            # Run verification
            try:
                is_verified, error_message = await verifier.verify(agent.contact_info)

                if is_verified:
                    # Update to verified status
                    await self._agent_repo.update_status(
                        agent_id=agent_id,
                        connection_status="verified",
                        verification_error=None,
                    )
                    logger.info(f"Agent {agent_id} verified successfully")
                else:
                    # Update to failed status with error message
                    await self._agent_repo.update_status(
                        agent_id=agent_id,
                        connection_status="failed",
                        verification_error=error_message or "Verification failed",
                    )
                    logger.warning(f"Agent {agent_id} verification failed: {error_message}")

            except Exception as e:
                # Handle verification errors
                error_msg = f"Verification error: {str(e)}"
                logger.error(f"Error verifying agent {agent_id}: {e}", exc_info=True)
                await self._agent_repo.update_status(
                    agent_id=agent_id,
                    connection_status="failed",
                    verification_error=error_msg,
                )

        except Exception as e:
            logger.error(f"Unexpected error in verify_agent for agent {agent_id}: {e}", exc_info=True)

    async def verify_agent_background(self, agent_id: UUID, force: bool = False) -> None:
        """Start agent verification in a background task.

        This is a convenience method that creates a background task for verification.
        Use this when you want to fire-and-forget verification.

        Args:
            agent_id: UUID of the agent to verify
            force: If True, re-verify even if already verified
        """
        asyncio.create_task(self.verify_agent(agent_id, force=force))
