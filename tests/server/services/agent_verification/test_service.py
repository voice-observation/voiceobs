"""Tests for agent verification service."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from voiceobs.server.db.models import AgentRow
from voiceobs.server.services.agent_verification.service import AgentVerificationService


@pytest.fixture
def mock_agent_repo():
    """Create a mock agent repository."""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.update_status = AsyncMock()
    return repo


@pytest.fixture
def mock_settings():
    """Create mock verification settings."""
    settings = MagicMock()
    settings.verification_max_retries = 3
    settings.get_retry_delay.return_value = 30
    return settings


class TestRetryLogic:
    """Tests for retry logic in verification service."""

    @pytest.mark.asyncio
    async def test_schedules_retry_on_failure(self, mock_agent_repo, mock_settings):
        """Test that failed verification schedules a retry when attempts < max."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="saved",
            verification_attempts=0,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(False, "Call not answered", None))
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

        # Should update to pending_retry (not failed) since attempts < max
        calls = mock_agent_repo.update_status.call_args_list
        # Find the final status update (after failure)
        final_call = calls[-1]
        assert final_call.kwargs.get("connection_status") == "pending_retry"

    @pytest.mark.asyncio
    async def test_marks_failed_after_max_retries(self, mock_agent_repo, mock_settings):
        """Test that verification marks as failed after max retries exceeded."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="pending_retry",
            verification_attempts=3,  # Already at max
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(False, "Call not answered", None))
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

        # Should update to failed (max retries exceeded)
        calls = mock_agent_repo.update_status.call_args_list
        final_call = calls[-1]
        assert final_call.kwargs.get("connection_status") == "failed"

    @pytest.mark.asyncio
    async def test_marks_verified_on_success(self, mock_agent_repo, mock_settings):
        """Test that successful verification marks agent as verified."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="saved",
            verification_attempts=0,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(True, None, None))
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

        # Should update to verified
        calls = mock_agent_repo.update_status.call_args_list
        final_call = calls[-1]
        assert final_call.kwargs.get("connection_status") == "verified"

    @pytest.mark.asyncio
    async def test_success_sets_verification_reasoning(self, mock_agent_repo, mock_settings):
        """Test that successful verification sets verification_reasoning."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="saved",
            verification_attempts=0,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(True, None, None))
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

        # Should set verification_reasoning
        calls = mock_agent_repo.update_status.call_args_list
        final_call = calls[-1]
        expected_reasoning = "Agent answered and responded successfully"
        assert final_call.kwargs.get("verification_reasoning") == expected_reasoning

    @pytest.mark.asyncio
    async def test_retry_delay_calculated_correctly(self, mock_agent_repo, mock_settings):
        """Test that retry delay is calculated using exponential backoff."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="saved",
            verification_attempts=1,  # Second attempt
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(False, "Call not answered", None))
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

        # get_retry_delay should be called with the current attempt number (after increment)
        # verification_attempts was 1 before, becomes 2 during verification
        mock_settings.get_retry_delay.assert_called_with(2)

    @pytest.mark.asyncio
    async def test_schedule_retry_creates_background_task(self, mock_agent_repo, mock_settings):
        """Test that _schedule_retry creates an asyncio task."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="saved",
            verification_attempts=0,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(False, "Call not answered", None))
                mock_factory.create.return_value = mock_verifier

                with patch("asyncio.create_task") as mock_create_task:
                    service = AgentVerificationService(mock_agent_repo)
                    await service.verify_agent(agent_id)

                    # Should have created a background task for retry
                    mock_create_task.assert_called()

    @pytest.mark.asyncio
    async def test_retry_task_stored_in_service(self, mock_agent_repo, mock_settings):
        """Test that retry task is stored in _retry_tasks dict."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="saved",
            verification_attempts=0,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(False, "Call not answered", None))
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

                # Should have stored task in _retry_tasks
                assert agent_id in service._retry_tasks

    @pytest.mark.asyncio
    async def test_handles_exception_during_verification(self, mock_agent_repo, mock_settings):
        """Test that exceptions during verification trigger retry logic."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="saved",
            verification_attempts=0,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(side_effect=Exception("Connection error"))
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

        # Should still schedule retry on exception (attempts < max)
        calls = mock_agent_repo.update_status.call_args_list
        final_call = calls[-1]
        assert final_call.kwargs.get("connection_status") == "pending_retry"

    @pytest.mark.asyncio
    async def test_agent_not_found_does_not_crash(self, mock_agent_repo, mock_settings):
        """Test that verification handles agent not found gracefully."""
        agent_id = uuid4()
        mock_agent_repo.get.return_value = None

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            service = AgentVerificationService(mock_agent_repo)
            # Should not raise
            await service.verify_agent(agent_id)

        # No status updates should be called
        mock_agent_repo.update_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_already_verified_agent(self, mock_agent_repo, mock_settings):
        """Test that already verified agents are skipped."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="verified",
            verification_attempts=1,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            service = AgentVerificationService(mock_agent_repo)
            await service.verify_agent(agent_id)

        # No status updates should be called
        mock_agent_repo.update_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_force_reverifies_verified_agent(self, mock_agent_repo, mock_settings):
        """Test that force=True re-verifies already verified agents."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="verified",
            verification_attempts=1,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(True, None, None))
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id, force=True)

        # Should have made status updates
        assert mock_agent_repo.update_status.call_count >= 1

    @pytest.mark.asyncio
    async def test_unsupported_agent_type_fails_immediately(self, mock_agent_repo, mock_settings):
        """Test that unsupported agent types fail without retry."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="unknown",
            contact_info={},
            connection_status="saved",
            verification_attempts=0,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_factory.create.side_effect = ValueError("Unsupported agent type")

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

        # Should fail immediately, not pending_retry
        calls = mock_agent_repo.update_status.call_args_list
        final_call = calls[-1]
        assert final_call.kwargs.get("connection_status") == "failed"


class TestCancelRetry:
    """Tests for cancel_retry method."""

    @pytest.mark.asyncio
    async def test_cancel_retry_returns_true_when_task_exists(self, mock_agent_repo, mock_settings):
        """Test that cancel_retry returns True when a retry task exists."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="saved",
            verification_attempts=0,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(False, "Call not answered", None))
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

                # Task should be stored
                assert agent_id in service._retry_tasks

                # Cancel should return True
                result = service.cancel_retry(agent_id)
                assert result is True

                # Task should be removed
                assert agent_id not in service._retry_tasks

    @pytest.mark.asyncio
    async def test_cancel_retry_returns_false_when_no_task(self, mock_agent_repo, mock_settings):
        """Test that cancel_retry returns False when no retry task exists."""
        agent_id = uuid4()

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            service = AgentVerificationService(mock_agent_repo)
            result = service.cancel_retry(agent_id)
            assert result is False


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_handles_unexpected_exception_in_verify_agent(
        self, mock_agent_repo, mock_settings
    ):
        """Test that unexpected exceptions in verify_agent are handled gracefully."""
        agent_id = uuid4()
        # Make get() raise an unexpected exception after being called
        mock_agent_repo.get.side_effect = RuntimeError("Database connection lost")

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            service = AgentVerificationService(mock_agent_repo)
            # Should not raise
            await service.verify_agent(agent_id)

        # No status updates should be called since we crashed early
        mock_agent_repo.update_status.assert_not_called()


class TestTranscriptStorage:
    """Tests for transcript storage in verification service."""

    @pytest.mark.asyncio
    async def test_success_stores_transcript(self, mock_agent_repo, mock_settings):
        """Test that successful verification stores the transcript."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="saved",
            verification_attempts=0,
        )
        mock_agent_repo.get.return_value = mock_agent

        expected_transcript = [
            {"role": "assistant", "content": "This is a verification call."},
            {"role": "user", "content": "Hello, I am here."},
        ]

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(True, None, expected_transcript))
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

        # Should store transcript in update_status call
        calls = mock_agent_repo.update_status.call_args_list
        final_call = calls[-1]
        assert final_call.kwargs.get("verification_transcript") == expected_transcript

    @pytest.mark.asyncio
    async def test_failure_stores_transcript(self, mock_agent_repo, mock_settings):
        """Test that failed verification stores the transcript."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="saved",
            verification_attempts=0,
        )
        mock_agent_repo.get.return_value = mock_agent

        expected_transcript = [
            {"role": "assistant", "content": "This is a verification call."},
        ]

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(
                    return_value=(False, "Agent did not respond", expected_transcript)
                )
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

        # Should store transcript even on failure
        calls = mock_agent_repo.update_status.call_args_list
        final_call = calls[-1]
        assert final_call.kwargs.get("verification_transcript") == expected_transcript

    @pytest.mark.asyncio
    async def test_stores_none_transcript_when_not_available(self, mock_agent_repo, mock_settings):
        """Test that None transcript is stored when not available."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="saved",
            verification_attempts=0,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(True, None, None))
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

        # Should store None transcript
        calls = mock_agent_repo.update_status.call_args_list
        final_call = calls[-1]
        assert final_call.kwargs.get("verification_transcript") is None

    @pytest.mark.asyncio
    async def test_max_retries_failure_stores_transcript(self, mock_agent_repo, mock_settings):
        """Test that transcript is stored when max retries exceeded."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="pending_retry",
            verification_attempts=3,  # Already at max
        )
        mock_agent_repo.get.return_value = mock_agent

        expected_transcript = [
            {"role": "assistant", "content": "Verification message."},
        ]

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(
                    return_value=(False, "Call not answered", expected_transcript)
                )
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent(agent_id)

        # Should store transcript in final failed status
        calls = mock_agent_repo.update_status.call_args_list
        final_call = calls[-1]
        assert final_call.kwargs.get("connection_status") == "failed"
        assert final_call.kwargs.get("verification_transcript") == expected_transcript


class TestVerifyAgentBackground:
    """Tests for verify_agent_background method."""

    @pytest.mark.asyncio
    async def test_verify_agent_background_creates_task(self, mock_agent_repo, mock_settings):
        """Test that verify_agent_background creates a background task."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="saved",
            verification_attempts=0,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(True, None, None))
                mock_factory.create.return_value = mock_verifier

                with patch("asyncio.create_task") as mock_create_task:
                    service = AgentVerificationService(mock_agent_repo)
                    await service.verify_agent_background(agent_id)
                    mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_agent_background_with_force(self, mock_agent_repo, mock_settings):
        """Test that verify_agent_background passes force flag correctly."""
        agent_id = uuid4()
        mock_agent = AgentRow(
            id=agent_id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            connection_status="verified",
            verification_attempts=1,
        )
        mock_agent_repo.get.return_value = mock_agent

        with patch(
            "voiceobs.server.services.agent_verification.service.get_verification_settings",
            return_value=mock_settings,
        ):
            with patch(
                "voiceobs.server.services.agent_verification.service.AgentVerifierFactory"
            ) as mock_factory:
                mock_verifier = MagicMock()
                mock_verifier.verify = AsyncMock(return_value=(True, None, None))
                mock_factory.create.return_value = mock_verifier

                service = AgentVerificationService(mock_agent_repo)
                await service.verify_agent_background(agent_id, force=True)

                # Give the background task a moment to run
                await asyncio.sleep(0.01)

                # Should have made status updates since force=True
                assert mock_agent_repo.update_status.call_count >= 1
