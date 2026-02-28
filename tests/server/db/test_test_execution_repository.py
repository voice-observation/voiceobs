"""Tests for updated TestExecutionRepository."""

import json
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from voiceobs.server.db.models import TestExecutionRow
from voiceobs.server.db.repositories.test_execution import TestExecutionRepository


class TestTestExecutionRepository:
    """Tests for updated TestExecutionRepository."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = AsyncMock()
        self.repo = TestExecutionRepository(self.mock_db)

    @pytest.mark.asyncio
    async def test_create_with_new_fields(self):
        """Test creating execution with org_id and suite_run_id."""
        org_id = uuid4()
        suite_run_id = uuid4()
        scenario_id = uuid4()
        exec_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": exec_id,
            "org_id": org_id,
            "suite_run_id": suite_run_id,
            "scenario_id": scenario_id,
            "conversation_id": None,
            "status": "pending",
            "attempt": 1,
            "max_attempts": 3,
            "audio_url": None,
            "transcript": None,
            "evaluation_result": None,
            "error_message": None,
            "duration_seconds": None,
            "started_at": None,
            "completed_at": None,
            "result_json": {},
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.create(
            org_id=org_id,
            suite_run_id=suite_run_id,
            scenario_id=scenario_id,
        )

        assert isinstance(result, TestExecutionRow)
        assert result.org_id == org_id
        assert result.suite_run_id == suite_run_id
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_get_with_org_scope(self):
        """Test fetching execution with org_id filter."""
        exec_id = uuid4()
        org_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": exec_id,
            "org_id": org_id,
            "suite_run_id": uuid4(),
            "scenario_id": uuid4(),
            "conversation_id": None,
            "status": "calling",
            "attempt": 1,
            "max_attempts": 3,
            "audio_url": None,
            "transcript": None,
            "evaluation_result": None,
            "error_message": None,
            "duration_seconds": None,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "result_json": {},
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.get(exec_id, org_id)
        assert result is not None
        assert result.org_id == org_id

    @pytest.mark.asyncio
    async def test_update_status(self):
        """Test updating execution status."""
        exec_id = uuid4()
        org_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": exec_id,
            "org_id": org_id,
            "suite_run_id": uuid4(),
            "scenario_id": uuid4(),
            "conversation_id": None,
            "status": "calling",
            "attempt": 1,
            "max_attempts": 3,
            "audio_url": None,
            "transcript": None,
            "evaluation_result": None,
            "error_message": None,
            "duration_seconds": None,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "result_json": {},
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.update(exec_id, org_id, {"status": "calling"})
        assert result is not None
        self.mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_with_transcript_serializes_jsonb(self):
        """Test that transcript (list) is JSON-serialized for JSONB column."""
        exec_id = uuid4()
        org_id = uuid4()
        transcript = [
            {"role": "persona", "text": "Hello", "timestamp_ms": 0},
            {"role": "agent", "text": "Hi!", "timestamp_ms": 500},
        ]

        self.mock_db.fetchrow.return_value = {
            "id": exec_id,
            "org_id": org_id,
            "suite_run_id": uuid4(),
            "scenario_id": uuid4(),
            "conversation_id": None,
            "status": "evaluating",
            "attempt": 1,
            "max_attempts": 3,
            "audio_url": None,
            "transcript": transcript,
            "evaluation_result": None,
            "error_message": None,
            "duration_seconds": None,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "result_json": {},
            "created_at": datetime.utcnow(),
        }

        await self.repo.update(exec_id, org_id, {"transcript": transcript})
        call_args = self.mock_db.execute.call_args
        params = call_args[0][1:] if len(call_args[0]) > 1 else []
        assert json.dumps(transcript) in params

    @pytest.mark.asyncio
    async def test_list_by_suite_run(self):
        """Test listing executions for a suite run."""
        org_id = uuid4()
        suite_run_id = uuid4()

        self.mock_db.fetch.return_value = [
            {
                "id": uuid4(),
                "org_id": org_id,
                "suite_run_id": suite_run_id,
                "scenario_id": uuid4(),
                "conversation_id": None,
                "status": "completed",
                "attempt": 1,
                "max_attempts": 3,
                "audio_url": "s3://bucket/audio.wav",
                "transcript": [{"role": "agent", "text": "Hello"}],
                "evaluation_result": {"passed": True, "score": 0.9},
                "error_message": None,
                "duration_seconds": 30.5,
                "started_at": datetime.utcnow(),
                "completed_at": datetime.utcnow(),
                "result_json": {},
                "created_at": datetime.utcnow(),
            }
        ]

        result = await self.repo.list_by_suite_run(org_id, suite_run_id)
        assert len(result) == 1
        assert result[0].status == "completed"
        assert result[0].audio_url == "s3://bucket/audio.wav"

    @pytest.mark.asyncio
    async def test_list_by_scenario(self):
        """Test listing executions for a scenario."""
        org_id = uuid4()
        scenario_id = uuid4()

        self.mock_db.fetch.return_value = [
            {
                "id": uuid4(),
                "org_id": org_id,
                "suite_run_id": uuid4(),
                "scenario_id": scenario_id,
                "conversation_id": None,
                "status": "completed",
                "attempt": 1,
                "max_attempts": 3,
                "audio_url": "s3://bucket/audio.wav",
                "transcript": [{"role": "agent", "text": "Hi"}],
                "evaluation_result": {"passed": True},
                "error_message": None,
                "duration_seconds": 25.0,
                "started_at": datetime.utcnow(),
                "completed_at": datetime.utcnow(),
                "result_json": {},
                "created_at": datetime.utcnow(),
            }
        ]

        result = await self.repo.list_by_scenario(org_id, scenario_id, limit=20)
        assert len(result) == 1
        assert result[0].scenario_id == scenario_id
        assert result[0].status == "completed"
        self.mock_db.fetch.assert_called_once()
        call_args = self.mock_db.fetch.call_args[0]
        assert "ORDER BY created_at DESC LIMIT" in call_args[0]
        assert call_args[3] == 20
