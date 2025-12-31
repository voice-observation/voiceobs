"""Tests for the FailureRepository class."""

from uuid import UUID, uuid4

import pytest

from voiceobs.server.db.models import FailureRow
from voiceobs.server.db.repositories import FailureRepository

from .conftest import MockRecord


class TestFailureRepository:
    """Tests for the FailureRepository class."""

    @pytest.mark.asyncio
    async def test_add_failure(self, mock_db):
        """Test adding a failure."""
        repo = FailureRepository(mock_db)

        failure_id = await repo.add(
            failure_type="interruption",
            severity="medium",
            message="Agent interrupted user",
        )

        assert isinstance(failure_id, UUID)
        mock_db.execute.assert_called_once()
        assert "INSERT INTO failures" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_add_failure_with_all_fields(self, mock_db):
        """Test adding a failure with all fields."""
        repo = FailureRepository(mock_db)
        conv_id = uuid4()
        turn_id = uuid4()

        failure_id = await repo.add(
            failure_type="excessive_silence",
            severity="high",
            message="Silence exceeded threshold",
            conversation_id=conv_id,
            turn_id=turn_id,
            turn_index=3,
            signal_name="voice.silence.after_user_ms",
            signal_value=5000.0,
            threshold=3000.0,
        )

        assert isinstance(failure_id, UUID)
        call_args = mock_db.execute.call_args[0]
        assert call_args[2] == "excessive_silence"
        assert call_args[3] == "high"
        assert call_args[5] == conv_id
        assert call_args[6] == turn_id
        assert call_args[9] == 5000.0
        assert call_args[10] == 3000.0

    @pytest.mark.asyncio
    async def test_get_failure(self, mock_db):
        """Test getting a failure by UUID."""
        repo = FailureRepository(mock_db)
        failure_id = uuid4()
        mock_db.fetchrow.return_value = MockRecord({
            "id": failure_id,
            "failure_type": "interruption",
            "severity": "medium",
            "message": "Test message",
            "conversation_id": None,
            "turn_id": None,
            "turn_index": None,
            "signal_name": None,
            "signal_value": None,
            "threshold": None,
            "created_at": None,
        })

        result = await repo.get(failure_id)

        assert result is not None
        assert isinstance(result, FailureRow)
        assert result.failure_type == "interruption"

    @pytest.mark.asyncio
    async def test_get_failure_not_found(self, mock_db):
        """Test getting a non-existent failure."""
        repo = FailureRepository(mock_db)
        mock_db.fetchrow.return_value = None

        result = await repo.get(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_failures_no_filter(self, mock_db):
        """Test getting all failures without filters."""
        repo = FailureRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({
                "id": uuid4(),
                "failure_type": "interruption",
                "severity": "low",
                "message": "Test 1",
                "conversation_id": None,
                "turn_id": None,
                "turn_index": None,
                "signal_name": None,
                "signal_value": None,
                "threshold": None,
                "created_at": None,
            }),
        ]

        result = await repo.get_all()

        assert len(result) == 1
        # No WHERE clause when no filters
        assert "WHERE" not in mock_db.fetch.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_all_failures_with_severity_filter(self, mock_db):
        """Test getting failures filtered by severity."""
        repo = FailureRepository(mock_db)
        mock_db.fetch.return_value = []

        await repo.get_all(severity="high")

        call_args = mock_db.fetch.call_args[0]
        assert "WHERE" in call_args[0]
        assert "severity = $1" in call_args[0]
        assert call_args[1] == "high"

    @pytest.mark.asyncio
    async def test_get_all_failures_with_type_filter(self, mock_db):
        """Test getting failures filtered by type."""
        repo = FailureRepository(mock_db)
        mock_db.fetch.return_value = []

        await repo.get_all(failure_type="interruption")

        call_args = mock_db.fetch.call_args[0]
        assert "WHERE" in call_args[0]
        assert "failure_type = $1" in call_args[0]
        assert call_args[1] == "interruption"

    @pytest.mark.asyncio
    async def test_get_all_failures_with_both_filters(self, mock_db):
        """Test getting failures filtered by both severity and type."""
        repo = FailureRepository(mock_db)
        mock_db.fetch.return_value = []

        await repo.get_all(severity="medium", failure_type="slow_response")

        call_args = mock_db.fetch.call_args[0]
        assert "WHERE" in call_args[0]
        assert "severity = $1" in call_args[0]
        assert "failure_type = $2" in call_args[0]
        assert call_args[1] == "medium"
        assert call_args[2] == "slow_response"

    @pytest.mark.asyncio
    async def test_get_by_conversation(self, mock_db):
        """Test getting failures by conversation."""
        repo = FailureRepository(mock_db)
        conv_id = uuid4()
        mock_db.fetch.return_value = [
            MockRecord({
                "id": uuid4(),
                "failure_type": "interruption",
                "severity": "low",
                "message": "Test",
                "conversation_id": conv_id,
                "turn_id": None,
                "turn_index": 1,
                "signal_name": None,
                "signal_value": None,
                "threshold": None,
                "created_at": None,
            }),
        ]

        result = await repo.get_by_conversation(conv_id)

        assert len(result) == 1
        assert result[0].conversation_id == conv_id

    @pytest.mark.asyncio
    async def test_get_counts_by_severity(self, mock_db):
        """Test getting failure counts by severity."""
        repo = FailureRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({"severity": "low", "count": 5}),
            MockRecord({"severity": "medium", "count": 3}),
            MockRecord({"severity": "high", "count": 1}),
        ]

        result = await repo.get_counts_by_severity()

        assert result == {"low": 5, "medium": 3, "high": 1}

    @pytest.mark.asyncio
    async def test_get_counts_by_type(self, mock_db):
        """Test getting failure counts by type."""
        repo = FailureRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({"failure_type": "interruption", "count": 4}),
            MockRecord({"failure_type": "excessive_silence", "count": 2}),
        ]

        result = await repo.get_counts_by_type()

        assert result == {"interruption": 4, "excessive_silence": 2}

    @pytest.mark.asyncio
    async def test_clear_failures(self, mock_db):
        """Test clearing all failures."""
        repo = FailureRepository(mock_db)
        mock_db.fetchval.return_value = 12

        count = await repo.clear()

        assert count == 12
        mock_db.execute.assert_called_once_with("DELETE FROM failures")

    @pytest.mark.asyncio
    async def test_count_failures(self, mock_db):
        """Test counting failures."""
        repo = FailureRepository(mock_db)
        mock_db.fetchval.return_value = 20

        count = await repo.count()

        assert count == 20
