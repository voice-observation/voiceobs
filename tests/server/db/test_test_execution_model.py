"""Tests for updated TestExecutionRow model."""

from datetime import datetime
from uuid import uuid4

from voiceobs.server.db.models import TestExecutionRow


class TestTestExecutionModel:
    """Tests for updated TestExecutionRow dataclass."""

    def test_create_with_new_defaults(self):
        """Test creating with new default fields."""
        execution = TestExecutionRow(
            id=uuid4(),
            org_id=uuid4(),
            suite_run_id=uuid4(),
            scenario_id=uuid4(),
        )
        assert execution.status == "pending"
        assert execution.attempt == 1
        assert execution.max_attempts == 3
        assert execution.audio_url is None
        assert execution.transcript is None
        assert execution.evaluation_result is None
        assert execution.error_message is None
        assert execution.duration_seconds is None
        assert execution.conversation_id is None
        assert execution.result_json == {}

    def test_from_row(self):
        """Test creating a TestExecutionRow from a database row dict."""
        from datetime import datetime

        exec_id = uuid4()
        org_id = uuid4()
        suite_run_id = uuid4()
        scenario_id = uuid4()
        now = datetime.utcnow()
        transcript = [{"role": "agent", "text": "Hello"}]
        eval_result = {"passed": True, "score": 0.9}
        row = {
            "id": exec_id,
            "org_id": org_id,
            "suite_run_id": suite_run_id,
            "scenario_id": scenario_id,
            "conversation_id": None,
            "status": "completed",
            "attempt": 2,
            "max_attempts": 3,
            "audio_url": "s3://bucket/audio.wav",
            "transcript": transcript,
            "evaluation_result": eval_result,
            "error_message": None,
            "duration_seconds": 45.2,
            "started_at": now,
            "completed_at": now,
            "result_json": {},
            "created_at": now,
        }

        execution = TestExecutionRow.from_row(row)

        assert execution.id == exec_id
        assert execution.org_id == org_id
        assert execution.suite_run_id == suite_run_id
        assert execution.status == "completed"
        assert execution.attempt == 2
        assert execution.transcript == transcript
        assert execution.evaluation_result == eval_result
        assert execution.duration_seconds == 45.2

    def test_from_row_with_defaults(self):
        """Test from_row uses defaults for optional fields."""
        exec_id = uuid4()
        org_id = uuid4()
        suite_run_id = uuid4()
        scenario_id = uuid4()
        row = {
            "id": exec_id,
            "org_id": org_id,
            "suite_run_id": suite_run_id,
            "scenario_id": scenario_id,
            "status": "pending",
        }

        execution = TestExecutionRow.from_row(row)

        assert execution.attempt == 1
        assert execution.max_attempts == 3
        assert execution.result_json == {}
        assert execution.conversation_id is None
        assert execution.audio_url is None

    def test_create_with_all_fields(self):
        """Test creating with all fields populated."""
        now = datetime.utcnow()
        transcript = [
            {"role": "persona", "text": "Hi, I need help", "timestamp_ms": 0},
            {"role": "agent", "text": "Sure, how can I help?", "timestamp_ms": 1500},
        ]
        eval_result = {"passed": True, "score": 0.92, "reasoning": "Good"}

        execution = TestExecutionRow(
            id=uuid4(),
            org_id=uuid4(),
            suite_run_id=uuid4(),
            scenario_id=uuid4(),
            status="completed",
            attempt=2,
            max_attempts=3,
            audio_url="s3://bucket/audio/test.wav",
            transcript=transcript,
            evaluation_result=eval_result,
            error_message=None,
            duration_seconds=45.2,
            started_at=now,
            completed_at=now,
            created_at=now,
        )
        assert execution.status == "completed"
        assert execution.attempt == 2
        assert execution.transcript == transcript
        assert execution.evaluation_result == eval_result
        assert execution.duration_seconds == 45.2
