"""Tests for TestSuiteRunRow model."""

from uuid import uuid4

from voiceobs.server.db.models import TestSuiteRunRow


class TestTestSuiteRunModel:
    """Tests for TestSuiteRunRow dataclass."""

    def test_create_with_defaults(self):
        """Test creating a TestSuiteRunRow with default values."""
        run = TestSuiteRunRow(
            id=uuid4(),
            org_id=uuid4(),
            suite_id=uuid4(),
            total_scenarios=5,
        )
        assert run.status == "pending"
        assert run.completed_scenarios == 0
        assert run.failed_scenarios == 0
        assert run.triggered_by is None
        assert run.started_at is None
        assert run.completed_at is None
        assert run.created_at is None

    def test_from_row(self):
        """Test creating a TestSuiteRunRow from a database row dict."""
        from datetime import datetime

        run_id = uuid4()
        org_id = uuid4()
        suite_id = uuid4()
        now = datetime.utcnow()
        row = {
            "id": run_id,
            "org_id": org_id,
            "suite_id": suite_id,
            "status": "running",
            "total_scenarios": 10,
            "completed_scenarios": 3,
            "failed_scenarios": 1,
            "triggered_by": "user-123",
            "started_at": now,
            "completed_at": None,
            "created_at": now,
        }

        run = TestSuiteRunRow.from_row(row)

        assert run.id == run_id
        assert run.org_id == org_id
        assert run.suite_id == suite_id
        assert run.status == "running"
        assert run.total_scenarios == 10
        assert run.completed_scenarios == 3
        assert run.failed_scenarios == 1
        assert run.triggered_by == "user-123"
        assert run.started_at == now
        assert run.created_at == now

    def test_create_with_all_fields(self):
        """Test creating a TestSuiteRunRow with all fields."""
        from datetime import datetime

        run = TestSuiteRunRow(
            id=uuid4(),
            org_id=uuid4(),
            suite_id=uuid4(),
            status="running",
            total_scenarios=10,
            completed_scenarios=3,
            failed_scenarios=1,
            triggered_by="user-123",
            started_at=datetime.utcnow(),
            completed_at=None,
            created_at=datetime.utcnow(),
        )
        assert run.status == "running"
        assert run.total_scenarios == 10
        assert run.completed_scenarios == 3
        assert run.failed_scenarios == 1
        assert run.triggered_by == "user-123"
