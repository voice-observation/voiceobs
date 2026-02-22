"""Agent verification service for orchestrating agent verification."""

import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from voiceobs.server.config.verification import get_verification_settings
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
    5. Scheduling retries with exponential backoff on failure
    """

    def __init__(self, agent_repository: AgentRepository) -> None:
        """Initialize the agent verification service.

        Args:
            agent_repository: Repository for agent database operations
        """
        self._agent_repo = agent_repository
        self._settings = get_verification_settings()
        self._retry_tasks: dict[UUID, asyncio.Task] = {}

    async def verify_agent(self, agent_id: UUID, org_id: UUID, force: bool = False) -> None:
        """Verify an agent's connection asynchronously.

        This method updates the agent's connection status based on verification results.
        It should be called in a background task.

        Args:
            agent_id: UUID of the agent to verify
            org_id: UUID of the organization the agent belongs to
            force: If True, re-verify even if already verified
        """
        try:
            # Refresh settings for each verification attempt
            self._settings = get_verification_settings()

            # Get agent from repository
            agent = await self._agent_repo.get(agent_id, org_id)
            if not agent:
                logger.error(f"Agent {agent_id} not found for verification")
                return

            # Skip if already verified and not forcing
            if not force and agent.connection_status == "verified":
                logger.info(f"Agent {agent_id} already verified, skipping")
                return

            current_attempt = (agent.verification_attempts or 0) + 1

            # Update status to "connecting"
            await self._agent_repo.update(
                agent_id,
                org_id,
                connection_status="connecting",
                verification_attempts=current_attempt,
                last_verification_at=datetime.now(timezone.utc),
                verification_error=None,
            )

            # Get appropriate verifier for agent type
            try:
                verifier = AgentVerifierFactory.create(agent.agent_type)
            except ValueError:
                error_msg = f"Unsupported agent type: {agent.agent_type}"
                logger.error(f"{error_msg} for agent {agent_id}")
                await self._agent_repo.update(
                    agent_id,
                    org_id,
                    connection_status="failed",
                    verification_error=error_msg,
                )
                return

            # Run verification
            try:
                is_verified, error_message, transcript = await verifier.verify(agent.contact_info)

                if is_verified:
                    # Update to verified status
                    await self._agent_repo.update(
                        agent_id,
                        org_id,
                        connection_status="verified",
                        verification_error=None,
                        verification_reasoning="Agent answered and responded successfully",
                        verification_transcript=transcript,
                    )
                    logger.info(f"Agent {agent_id} verified successfully")
                else:
                    # Handle failure with retry logic
                    await self._handle_verification_failure(
                        agent_id=agent_id,
                        org_id=org_id,
                        current_attempt=current_attempt,
                        error_message=error_message or "Verification failed",
                        transcript=transcript,
                    )

            except Exception as e:
                # Handle verification errors with retry logic
                error_msg = f"Verification error: {str(e)}"
                logger.error(f"Error verifying agent {agent_id}: {e}", exc_info=True)
                await self._handle_verification_failure(
                    agent_id=agent_id,
                    org_id=org_id,
                    current_attempt=current_attempt,
                    error_message=error_msg,
                )

        except Exception as e:
            logger.error(
                f"Unexpected error in verify_agent for agent {agent_id}: {e}",
                exc_info=True,
            )

    async def _handle_verification_failure(
        self,
        agent_id: UUID,
        org_id: UUID,
        current_attempt: int,
        error_message: str,
        transcript: list[dict[str, str]] | None = None,
    ) -> None:
        """Handle verification failure with retry logic.

        If the current attempt is less than max retries, schedule a retry.
        Otherwise, mark the agent as failed.

        Args:
            agent_id: UUID of the agent
            org_id: UUID of the organization the agent belongs to
            current_attempt: Current attempt number (1-based)
            error_message: Error message from the failed verification
            transcript: Conversation transcript from the verification attempt
        """
        max_retries = self._settings.verification_max_retries

        if current_attempt < max_retries:
            # Schedule retry
            await self._agent_repo.update(
                agent_id,
                org_id,
                connection_status="pending_retry",
                verification_error=error_message,
                verification_transcript=transcript,
            )
            logger.info(
                f"Agent {agent_id} verification failed (attempt {current_attempt}/{max_retries}), "
                "scheduling retry"
            )
            self._schedule_retry(agent_id, org_id, current_attempt)
        else:
            # Max retries exceeded
            await self._agent_repo.update(
                agent_id,
                org_id,
                connection_status="failed",
                verification_error=error_message,
                verification_transcript=transcript,
            )
            logger.warning(
                f"Agent {agent_id} verification failed after {current_attempt} attempts: "
                f"{error_message}"
            )

    def _schedule_retry(self, agent_id: UUID, org_id: UUID, current_attempt: int) -> None:
        """Schedule a retry verification after a delay.

        The delay is calculated using exponential backoff.

        Args:
            agent_id: UUID of the agent to retry
            org_id: UUID of the organization the agent belongs to
            current_attempt: Current attempt number (used for backoff calculation)
        """
        delay = self._settings.get_retry_delay(current_attempt)
        logger.info(f"Scheduling retry for agent {agent_id} in {delay} seconds")

        async def retry_after_delay() -> None:
            await asyncio.sleep(delay)
            await self.verify_agent(agent_id, org_id)
            # Clean up task reference after completion
            self._retry_tasks.pop(agent_id, None)

        task = asyncio.create_task(retry_after_delay())
        self._retry_tasks[agent_id] = task

    async def verify_agent_background(
        self, agent_id: UUID, org_id: UUID, force: bool = False
    ) -> None:
        """Start agent verification in a background task.

        This is a convenience method that creates a background task for verification.
        Use this when you want to fire-and-forget verification.

        Args:
            agent_id: UUID of the agent to verify
            org_id: UUID of the organization the agent belongs to
            force: If True, re-verify even if already verified
        """
        logger.info(
            f"Creating background task for agent verification: agent_id={agent_id}, force={force}"
        )
        task = asyncio.create_task(self.verify_agent(agent_id, org_id, force=force))
        logger.debug(f"Background verification task created: {task}")

    def cancel_retry(self, agent_id: UUID) -> bool:
        """Cancel a pending retry for an agent.

        Args:
            agent_id: UUID of the agent

        Returns:
            True if a retry was cancelled, False if no retry was pending
        """
        task = self._retry_tasks.pop(agent_id, None)
        if task:
            task.cancel()
            logger.info(f"Cancelled pending retry for agent {agent_id}")
            return True
        return False
