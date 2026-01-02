"""Tests for database model dataclasses."""

from datetime import datetime
from uuid import uuid4

from voiceobs.server.db.models import (
    ConversationRow,
    FailureRow,
    SpanRow,
    TestExecutionRow,
    TestScenarioRow,
    TestSuiteRow,
    TurnRow,
)


class TestConversationRow:
    """Tests for ConversationRow model."""

    def test_conversation_row_creation(self):
        """Test creating a ConversationRow with all fields."""
        conv_id = uuid4()
        created_at = datetime.now()
        updated_at = datetime.now()

        row = ConversationRow(
            id=conv_id,
            conversation_id="conv-123",
            created_at=created_at,
            updated_at=updated_at,
            audio_path="/path/to/audio.wav",
            audio_metadata={"duration": 120.5, "format": "wav"},
        )

        assert row.id == conv_id
        assert row.conversation_id == "conv-123"
        assert row.created_at == created_at
        assert row.updated_at == updated_at
        assert row.audio_path == "/path/to/audio.wav"
        assert row.audio_metadata == {"duration": 120.5, "format": "wav"}

    def test_conversation_row_defaults(self):
        """Test ConversationRow with default values."""
        conv_id = uuid4()

        row = ConversationRow(
            id=conv_id,
            conversation_id="conv-123",
        )

        assert row.id == conv_id
        assert row.conversation_id == "conv-123"
        assert row.created_at is None
        assert row.updated_at is None
        assert row.audio_path is None
        assert row.audio_metadata == {}

    def test_conversation_row_audio_fields_optional(self):
        """Test that audio_path and audio_metadata are optional."""
        conv_id = uuid4()

        row = ConversationRow(
            id=conv_id,
            conversation_id="conv-123",
            audio_path=None,
            audio_metadata={},
        )

        assert row.audio_path is None
        assert row.audio_metadata == {}


class TestTestSuiteRow:
    """Tests for TestSuiteRow model."""

    def test_test_suite_row_creation(self):
        """Test creating a TestSuiteRow with all fields."""
        suite_id = uuid4()
        created_at = datetime.now()

        row = TestSuiteRow(
            id=suite_id,
            name="Test Suite 1",
            description="A test suite",
            status="running",
            created_at=created_at,
        )

        assert row.id == suite_id
        assert row.name == "Test Suite 1"
        assert row.description == "A test suite"
        assert row.status == "running"
        assert row.created_at == created_at

    def test_test_suite_row_defaults(self):
        """Test TestSuiteRow with default values."""
        suite_id = uuid4()

        row = TestSuiteRow(
            id=suite_id,
            name="Test Suite 1",
        )

        assert row.id == suite_id
        assert row.name == "Test Suite 1"
        assert row.description is None
        assert row.status == "pending"
        assert row.created_at is None


class TestTestScenarioRow:
    """Tests for TestScenarioRow model."""

    def test_test_scenario_row_creation(self):
        """Test creating a TestScenarioRow with all fields."""
        scenario_id = uuid4()
        suite_id = uuid4()
        persona = {"name": "Alice", "age": 30}

        row = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Scenario 1",
            goal="Test goal",
            persona_json=persona,
            max_turns=10,
            timeout=300,
        )

        assert row.id == scenario_id
        assert row.suite_id == suite_id
        assert row.name == "Scenario 1"
        assert row.goal == "Test goal"
        assert row.persona_json == persona
        assert row.max_turns == 10
        assert row.timeout == 300

    def test_test_scenario_row_defaults(self):
        """Test TestScenarioRow with default values."""
        scenario_id = uuid4()
        suite_id = uuid4()

        row = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Scenario 1",
            goal="Test goal",
        )

        assert row.id == scenario_id
        assert row.suite_id == suite_id
        assert row.name == "Scenario 1"
        assert row.goal == "Test goal"
        assert row.persona_json == {}
        assert row.max_turns is None
        assert row.timeout is None


class TestTestExecutionRow:
    """Tests for TestExecutionRow model."""

    def test_test_execution_row_creation(self):
        """Test creating a TestExecutionRow with all fields."""
        execution_id = uuid4()
        scenario_id = uuid4()
        conversation_id = uuid4()
        started_at = datetime.now()
        completed_at = datetime.now()
        result = {"success": True, "score": 0.95}

        row = TestExecutionRow(
            id=execution_id,
            scenario_id=scenario_id,
            conversation_id=conversation_id,
            status="completed",
            started_at=started_at,
            completed_at=completed_at,
            result_json=result,
        )

        assert row.id == execution_id
        assert row.scenario_id == scenario_id
        assert row.conversation_id == conversation_id
        assert row.status == "completed"
        assert row.started_at == started_at
        assert row.completed_at == completed_at
        assert row.result_json == result

    def test_test_execution_row_defaults(self):
        """Test TestExecutionRow with default values."""
        execution_id = uuid4()
        scenario_id = uuid4()

        row = TestExecutionRow(
            id=execution_id,
            scenario_id=scenario_id,
        )

        assert row.id == execution_id
        assert row.scenario_id == scenario_id
        assert row.conversation_id is None
        assert row.status == "pending"
        assert row.started_at is None
        assert row.completed_at is None
        assert row.result_json == {}


class TestModelCompatibility:
    """Tests to ensure models are compatible with existing code."""

    def test_existing_models_still_work(self):
        """Test that existing models (SpanRow, TurnRow, FailureRow) still work."""
        span_id = uuid4()
        conv_id = uuid4()

        span = SpanRow(
            id=span_id,
            name="test_span",
            start_time=None,
            end_time=None,
            duration_ms=None,
            attributes={},
            trace_id=None,
            span_id=None,
            parent_span_id=None,
            conversation_id=conv_id,
        )

        assert span.id == span_id
        assert span.conversation_id == conv_id

        turn = TurnRow(
            id=uuid4(),
            turn_id="turn-1",
            conversation_id=conv_id,
            span_id=span_id,
            actor="user",
            turn_index=0,
            duration_ms=1000.0,
            transcript="Hello",
        )

        assert turn.conversation_id == conv_id
        assert turn.span_id == span_id

        failure = FailureRow(
            id=uuid4(),
            failure_type="error",
            severity="high",
            message="Test failure",
            conversation_id=conv_id,
            turn_id=None,
            turn_index=None,
            signal_name=None,
            signal_value=None,
            threshold=None,
        )

        assert failure.conversation_id == conv_id
