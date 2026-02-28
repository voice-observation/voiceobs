"""Tests for suite run Pydantic models."""

from datetime import datetime
from uuid import uuid4

from voiceobs.server.db.models import TestExecutionRow, TestSuiteRunRow
from voiceobs.server.models.response.suite_run import (
    ExecutionSummaryResponse,
    SuiteRunResponse,
    SuiteRunTriggerResponse,
)
from voiceobs.server.models.response.test import TestExecutionResponse


class TestSuiteRunTriggerResponse:
    """Tests for SuiteRunTriggerResponse."""

    def test_create(self):
        """Test creating a SuiteRunTriggerResponse."""
        run_id = uuid4()
        resp = SuiteRunTriggerResponse(
            suite_run_id=str(run_id),
            status="running",
            total_scenarios=5,
        )
        assert resp.suite_run_id == str(run_id)
        assert resp.status == "running"
        assert resp.total_scenarios == 5


class TestExecutionSummaryResponse:
    """Tests for ExecutionSummaryResponse."""

    def test_create_minimal(self):
        """Test creating with minimal fields."""
        resp = ExecutionSummaryResponse(
            id=str(uuid4()),
            scenario_id=str(uuid4()),
            scenario_name="Order Status Check",
            status="pending",
        )
        assert resp.status == "pending"
        assert resp.audio_url is None
        assert resp.transcript is None
        assert resp.evaluation_result is None
        assert resp.duration_seconds is None
        assert resp.attempt == 1
        assert resp.error_message is None

    def test_create_full(self):
        """Test creating with all fields."""
        resp = ExecutionSummaryResponse(
            id=str(uuid4()),
            scenario_id=str(uuid4()),
            scenario_name="Order Status Check",
            status="completed",
            audio_url="s3://bucket/audio.wav",
            transcript=[{"role": "agent", "text": "Hello"}],
            evaluation_result={"passed": True, "score": 0.9},
            duration_seconds=30.5,
            attempt=1,
            error_message=None,
        )
        assert resp.audio_url == "s3://bucket/audio.wav"
        assert resp.transcript == [{"role": "agent", "text": "Hello"}]
        assert resp.evaluation_result == {"passed": True, "score": 0.9}
        assert resp.duration_seconds == 30.5

    def test_from_execution_row(self):
        """Test creating from TestExecutionRow with scenario_name."""
        exec_row = TestExecutionRow(
            id=uuid4(),
            org_id=uuid4(),
            suite_run_id=uuid4(),
            scenario_id=uuid4(),
            status="completed",
            audio_url="s3://bucket/audio.wav",
            transcript=[{"role": "agent", "text": "Hi"}],
            evaluation_result={"passed": True},
            duration_seconds=25.0,
            attempt=1,
        )
        resp = ExecutionSummaryResponse.from_execution_row(exec_row, scenario_name="Test Scenario")
        assert resp.id == str(exec_row.id)
        assert resp.scenario_id == str(exec_row.scenario_id)
        assert resp.scenario_name == "Test Scenario"
        assert resp.status == "completed"
        assert resp.audio_url == "s3://bucket/audio.wav"
        assert resp.transcript == [{"role": "agent", "text": "Hi"}]
        assert resp.evaluation_result == {"passed": True}
        assert resp.duration_seconds == 25.0
        assert resp.attempt == 1


class TestSuiteRunResponse:
    """Tests for SuiteRunResponse."""

    def test_create_minimal(self):
        """Test creating with minimal fields."""
        resp = SuiteRunResponse(
            id=str(uuid4()),
            suite_id=str(uuid4()),
            status="pending",
            total_scenarios=5,
            completed_scenarios=0,
            failed_scenarios=0,
            executions=[],
        )
        assert resp.status == "pending"
        assert resp.triggered_by is None
        assert resp.started_at is None
        assert resp.completed_at is None
        assert resp.created_at is None
        assert resp.executions == []

    def test_create_full(self):
        """Test creating with all fields."""
        started = datetime.utcnow()
        completed = datetime.utcnow()
        created = datetime.utcnow()
        resp = SuiteRunResponse(
            id=str(uuid4()),
            suite_id=str(uuid4()),
            status="completed",
            total_scenarios=10,
            completed_scenarios=9,
            failed_scenarios=1,
            triggered_by="user-123",
            started_at=started,
            completed_at=completed,
            created_at=created,
            executions=[
                ExecutionSummaryResponse(
                    id=str(uuid4()),
                    scenario_id=str(uuid4()),
                    scenario_name="Scenario 1",
                    status="completed",
                )
            ],
        )
        assert resp.status == "completed"
        assert resp.triggered_by == "user-123"
        assert resp.started_at == started
        assert resp.completed_at == completed
        assert len(resp.executions) == 1

    def test_from_row(self):
        """Test creating from TestSuiteRunRow with executions."""
        run_row = TestSuiteRunRow(
            id=uuid4(),
            org_id=uuid4(),
            suite_id=uuid4(),
            total_scenarios=2,
            status="running",
            completed_scenarios=1,
            failed_scenarios=0,
            triggered_by="user-456",
            started_at=datetime.utcnow(),
            completed_at=None,
            created_at=datetime.utcnow(),
        )
        exec_summaries = [
            ExecutionSummaryResponse(
                id=str(uuid4()),
                scenario_id=str(uuid4()),
                scenario_name="Scenario A",
                status="completed",
            ),
            ExecutionSummaryResponse(
                id=str(uuid4()),
                scenario_id=str(uuid4()),
                scenario_name="Scenario B",
                status="pending",
            ),
        ]
        resp = SuiteRunResponse.from_row(run_row, executions=exec_summaries)
        assert resp.id == str(run_row.id)
        assert resp.suite_id == str(run_row.suite_id)
        assert resp.status == "running"
        assert resp.total_scenarios == 2
        assert resp.completed_scenarios == 1
        assert resp.failed_scenarios == 0
        assert resp.triggered_by == "user-456"
        assert len(resp.executions) == 2


class TestTestExecutionResponseUpdated:
    """Tests for updated TestExecutionResponse with new fields."""

    def test_create_with_new_fields(self):
        """Test TestExecutionResponse with audio_url, transcript, etc."""
        resp = TestExecutionResponse(
            id=str(uuid4()),
            scenario_id=str(uuid4()),
            conversation_id=None,
            status="completed",
            audio_url="s3://bucket/audio.wav",
            transcript=[{"role": "agent", "text": "Hello"}],
            evaluation_result={"passed": True, "score": 0.9},
            error_message=None,
            duration_seconds=30.5,
            attempt=1,
            suite_run_id=str(uuid4()),
            org_id=str(uuid4()),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            result_json={},
        )
        assert resp.audio_url == "s3://bucket/audio.wav"
        assert resp.transcript == [{"role": "agent", "text": "Hello"}]
        assert resp.evaluation_result == {"passed": True, "score": 0.9}
        assert resp.duration_seconds == 30.5
        assert resp.attempt == 1
        assert resp.suite_run_id is not None
        assert resp.org_id is not None

    def test_from_row(self):
        """Test TestExecutionResponse.from_row with new fields."""
        exec_row = TestExecutionRow(
            id=uuid4(),
            org_id=uuid4(),
            suite_run_id=uuid4(),
            scenario_id=uuid4(),
            status="completed",
            audio_url="s3://bucket/audio.wav",
            transcript=[{"role": "agent", "text": "Hi"}],
            evaluation_result={"passed": True},
            duration_seconds=25.0,
            attempt=1,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        resp = TestExecutionResponse.from_row(exec_row)
        assert resp.id == str(exec_row.id)
        assert resp.scenario_id == str(exec_row.scenario_id)
        assert resp.status == "completed"
        assert resp.audio_url == "s3://bucket/audio.wav"
        assert resp.transcript == [{"role": "agent", "text": "Hi"}]
        assert resp.evaluation_result == {"passed": True}
        assert resp.duration_seconds == 25.0
        assert resp.attempt == 1
        assert resp.suite_run_id == str(exec_row.suite_run_id)
        assert resp.org_id == str(exec_row.org_id)
