# Test Scenario Execution - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable users to execute test scenarios against voice AI agents via a two-queue SQS pipeline with parallel workers, capturing audio and transcript per execution.

**Architecture:** FastAPI API creates TestSuiteRun + TestExecution rows and enqueues SQS messages. Call workers poll the Execution Queue, dial agents via LiveKit/SIP, record audio + real-time transcript via Deepgram, then enqueue to Evaluation Queue. Eval workers run LLM-based evaluation. Frontend polls a suite-run endpoint for status.

**Tech Stack:** FastAPI, PostgreSQL/asyncpg, AWS SQS (boto3), LiveKit/SIP, Deepgram STT, S3 audio storage, existing LLM service.

**Design Doc:** `docs/plans/2026-02-25-test-scenario-execution-design.md`

---

## Task 1: TestSuiteRun Model & Migration

**Files:**
- Create: `src/voiceobs/server/db/models/test_suite_run.py`
- Modify: `src/voiceobs/server/db/models/__init__.py`
- Create: `src/voiceobs/server/db/alembic/versions/20260226_000000_027_add_test_suite_runs_table.py`
- Test: `tests/server/db/test_test_suite_run_model.py`

**Step 1: Write the test**

```python
# tests/server/db/test_test_suite_run_model.py
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
```

**Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/server/db/test_test_suite_run_model.py -v`
Expected: FAIL with ImportError (TestSuiteRunRow doesn't exist)

**Step 3: Write the model**

```python
# src/voiceobs/server/db/models/test_suite_run.py
"""Test suite run model for database operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class TestSuiteRunRow:
    """Represents a test suite run row in the database."""

    id: UUID
    org_id: UUID
    suite_id: UUID
    total_scenarios: int
    status: str = "pending"  # pending, running, completed, failed, cancelled
    completed_scenarios: int = 0
    failed_scenarios: int = 0
    triggered_by: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
```

Update `src/voiceobs/server/db/models/__init__.py` — add:
```python
from voiceobs.server.db.models.test_suite_run import TestSuiteRunRow
```
And add `"TestSuiteRunRow"` to `__all__`.

**Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/server/db/test_test_suite_run_model.py -v`
Expected: PASS

**Step 5: Write the migration**

```python
# src/voiceobs/server/db/alembic/versions/20260226_000000_027_add_test_suite_runs_table.py
"""Add test_suite_runs table and update test_executions.

Revision ID: 027
Revises: 026
Create Date: 2026-02-26 00:00:00.000000

This migration:
1. Creates test_suite_runs table
2. Adds new columns to test_executions (suite_run_id, org_id, attempt,
   max_attempts, audio_url, transcript, evaluation_result, error_message,
   duration_seconds)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "027"
down_revision: str = "026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create test_suite_runs table and update test_executions."""
    # Create test_suite_runs table
    op.create_table(
        "test_suite_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("suite_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("total_scenarios", sa.Integer(), nullable=False),
        sa.Column(
            "completed_scenarios", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "failed_scenarios", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("triggered_by", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["org_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["suite_id"], ["test_suites.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_test_suite_runs_org_id", "test_suite_runs", ["org_id"])
    op.create_index("idx_test_suite_runs_suite_id", "test_suite_runs", ["suite_id"])
    op.create_index("idx_test_suite_runs_status", "test_suite_runs", ["status"])
    op.create_index(
        "idx_test_suite_runs_created_at", "test_suite_runs", ["created_at"]
    )

    # Delete existing test_executions (clean slate for schema change)
    op.execute("DELETE FROM test_executions")

    # Add new columns to test_executions
    op.add_column(
        "test_executions",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "test_executions",
        sa.Column("suite_run_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "test_executions",
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "test_executions",
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "test_executions",
        sa.Column("audio_url", sa.String(512), nullable=True),
    )
    op.add_column(
        "test_executions",
        sa.Column(
            "transcript",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "test_executions",
        sa.Column(
            "evaluation_result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "test_executions",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "test_executions",
        sa.Column("duration_seconds", sa.Float(), nullable=True),
    )
    op.add_column(
        "test_executions",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
    )

    # Make org_id NOT NULL (after clean slate)
    op.alter_column("test_executions", "org_id", nullable=False)
    op.alter_column("test_executions", "suite_run_id", nullable=False)

    # Widen status column to accommodate longer statuses like "evaluating"
    op.alter_column(
        "test_executions", "status", type_=sa.String(30), existing_type=sa.String(20)
    )

    # Add FK constraints
    op.create_foreign_key(
        "fk_test_executions_org_id",
        "test_executions",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_test_executions_suite_run_id",
        "test_executions",
        "test_suite_runs",
        ["suite_run_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add indexes
    op.create_index("idx_test_executions_org_id", "test_executions", ["org_id"])
    op.create_index(
        "idx_test_executions_suite_run_id", "test_executions", ["suite_run_id"]
    )


def downgrade() -> None:
    """Remove test_suite_runs table and revert test_executions changes."""
    # Remove new indexes and constraints from test_executions
    op.drop_index("idx_test_executions_suite_run_id", table_name="test_executions")
    op.drop_index("idx_test_executions_org_id", table_name="test_executions")
    op.drop_constraint("fk_test_executions_suite_run_id", "test_executions", type_="foreignkey")
    op.drop_constraint("fk_test_executions_org_id", "test_executions", type_="foreignkey")

    # Revert status column width
    op.alter_column(
        "test_executions", "status", type_=sa.String(20), existing_type=sa.String(30)
    )

    # Remove new columns from test_executions
    op.drop_column("test_executions", "created_at")
    op.drop_column("test_executions", "duration_seconds")
    op.drop_column("test_executions", "error_message")
    op.drop_column("test_executions", "evaluation_result")
    op.drop_column("test_executions", "transcript")
    op.drop_column("test_executions", "audio_url")
    op.drop_column("test_executions", "max_attempts")
    op.drop_column("test_executions", "attempt")
    op.drop_column("test_executions", "suite_run_id")
    op.drop_column("test_executions", "org_id")

    # Drop test_suite_runs table
    op.drop_index("idx_test_suite_runs_created_at", table_name="test_suite_runs")
    op.drop_index("idx_test_suite_runs_status", table_name="test_suite_runs")
    op.drop_index("idx_test_suite_runs_suite_id", table_name="test_suite_runs")
    op.drop_index("idx_test_suite_runs_org_id", table_name="test_suite_runs")
    op.drop_table("test_suite_runs")
```

**Step 6: Commit**

```bash
git add -f src/voiceobs/server/db/models/test_suite_run.py \
  src/voiceobs/server/db/models/__init__.py \
  src/voiceobs/server/db/alembic/versions/20260226_000000_027_add_test_suite_runs_table.py \
  tests/server/db/test_test_suite_run_model.py
git commit -m "feat: add TestSuiteRun model and migration for execution tracking"
```

---

## Task 2: Update TestExecutionRow Model

**Files:**
- Modify: `src/voiceobs/server/db/models/test_execution.py`
- Test: `tests/server/db/test_test_execution_model.py`

**Step 1: Write the test**

```python
# tests/server/db/test_test_execution_model.py
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
```

**Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/server/db/test_test_execution_model.py -v`
Expected: FAIL (org_id and suite_run_id not in TestExecutionRow)

**Step 3: Update the model**

Replace `src/voiceobs/server/db/models/test_execution.py` with:

```python
"""Test execution model for database operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class TestExecutionRow:
    """Represents a test execution row in the database."""

    id: UUID
    org_id: UUID
    suite_run_id: UUID
    scenario_id: UUID
    conversation_id: UUID | None = None
    status: str = "pending"  # pending, queued, calling, evaluating, completed, failed
    attempt: int = 1
    max_attempts: int = 3
    audio_url: str | None = None
    transcript: list[dict[str, Any]] | None = None
    evaluation_result: dict[str, Any] | None = None
    error_message: str | None = None
    duration_seconds: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result_json: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
```

**Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/server/db/test_test_execution_model.py -v`
Expected: PASS

**Step 5: Fix existing tests that use old TestExecutionRow signature**

The existing test file `tests/server/routes/test_test_executions.py` creates `TestExecutionRow` without `org_id` and `suite_run_id`. Update all instances to include these required fields. Search for all uses:

Run: `uv run python -m pytest tests/ -v` and fix any failures from the model change.

Every `TestExecutionRow(...)` creation in tests must now include `org_id=uuid4()` and `suite_run_id=uuid4()`.

**Step 6: Commit**

```bash
git add src/voiceobs/server/db/models/test_execution.py \
  tests/server/db/test_test_execution_model.py \
  tests/server/routes/test_test_executions.py
git commit -m "feat: update TestExecutionRow with suite_run_id, audio, transcript, evaluation fields"
```

---

## Task 3: TestSuiteRun Repository

**Files:**
- Create: `src/voiceobs/server/db/repositories/test_suite_run.py`
- Modify: `src/voiceobs/server/db/repositories/__init__.py`
- Test: `tests/server/db/test_test_suite_run_repository.py`

**Step 1: Write the test**

```python
# tests/server/db/test_test_suite_run_repository.py
"""Tests for TestSuiteRunRepository."""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from voiceobs.server.db.models import TestSuiteRunRow
from voiceobs.server.db.repositories.test_suite_run import TestSuiteRunRepository


class TestTestSuiteRunRepository:
    """Tests for TestSuiteRunRepository."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = AsyncMock()
        self.repo = TestSuiteRunRepository(self.mock_db)

    @pytest.mark.asyncio
    async def test_create(self):
        """Test creating a suite run."""
        org_id = uuid4()
        suite_id = uuid4()
        run_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": run_id,
            "org_id": org_id,
            "suite_id": suite_id,
            "status": "pending",
            "total_scenarios": 5,
            "completed_scenarios": 0,
            "failed_scenarios": 0,
            "triggered_by": "user-123",
            "started_at": None,
            "completed_at": None,
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.create(
            org_id=org_id,
            suite_id=suite_id,
            total_scenarios=5,
            triggered_by="user-123",
        )

        assert isinstance(result, TestSuiteRunRow)
        assert result.id == run_id
        assert result.status == "pending"
        assert result.total_scenarios == 5
        self.mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get(self):
        """Test fetching a suite run by ID."""
        run_id = uuid4()
        org_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": run_id,
            "org_id": org_id,
            "suite_id": uuid4(),
            "status": "running",
            "total_scenarios": 10,
            "completed_scenarios": 3,
            "failed_scenarios": 1,
            "triggered_by": "user-123",
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.get(run_id, org_id)
        assert result is not None
        assert result.id == run_id
        assert result.status == "running"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test fetching a non-existent suite run."""
        self.mock_db.fetchrow.return_value = None
        result = await self.repo.get(uuid4(), uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_update(self):
        """Test updating suite run fields."""
        run_id = uuid4()
        org_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": run_id,
            "org_id": org_id,
            "suite_id": uuid4(),
            "status": "running",
            "total_scenarios": 10,
            "completed_scenarios": 5,
            "failed_scenarios": 0,
            "triggered_by": "user-123",
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.update(
            run_id, org_id, {"status": "running", "completed_scenarios": 5}
        )
        assert result is not None
        assert result.status == "running"

    @pytest.mark.asyncio
    async def test_increment_completed(self):
        """Test incrementing completed_scenarios counter."""
        run_id = uuid4()
        org_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": run_id,
            "org_id": org_id,
            "suite_id": uuid4(),
            "status": "running",
            "total_scenarios": 10,
            "completed_scenarios": 6,
            "failed_scenarios": 0,
            "triggered_by": None,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.increment_completed(run_id, org_id)
        assert result is not None
        self.mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_failed(self):
        """Test incrementing failed_scenarios counter."""
        run_id = uuid4()
        org_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": run_id,
            "org_id": org_id,
            "suite_id": uuid4(),
            "status": "running",
            "total_scenarios": 10,
            "completed_scenarios": 5,
            "failed_scenarios": 2,
            "triggered_by": None,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.increment_failed(run_id, org_id)
        assert result is not None
        self.mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_by_suite(self):
        """Test listing suite runs for a suite."""
        org_id = uuid4()
        suite_id = uuid4()

        self.mock_db.fetch.return_value = [
            {
                "id": uuid4(),
                "org_id": org_id,
                "suite_id": suite_id,
                "status": "completed",
                "total_scenarios": 5,
                "completed_scenarios": 5,
                "failed_scenarios": 0,
                "triggered_by": "user-123",
                "started_at": datetime.utcnow(),
                "completed_at": datetime.utcnow(),
                "created_at": datetime.utcnow(),
            }
        ]

        result = await self.repo.list_by_suite(org_id, suite_id)
        assert len(result) == 1
        assert result[0].status == "completed"
```

**Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/server/db/test_test_suite_run_repository.py -v`
Expected: FAIL (module not found)

**Step 3: Write the repository**

```python
# src/voiceobs/server/db/repositories/test_suite_run.py
"""Test suite run repository for database operations."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import TestSuiteRunRow

logger = logging.getLogger(__name__)

_COLUMNS = "id, org_id, suite_id, status, total_scenarios, completed_scenarios, failed_scenarios, triggered_by, started_at, completed_at, created_at"


def _row_to_model(row: dict[str, Any]) -> TestSuiteRunRow:
    """Convert a database row to a TestSuiteRunRow."""
    return TestSuiteRunRow(
        id=row["id"],
        org_id=row["org_id"],
        suite_id=row["suite_id"],
        status=row["status"],
        total_scenarios=row["total_scenarios"],
        completed_scenarios=row["completed_scenarios"],
        failed_scenarios=row["failed_scenarios"],
        triggered_by=row["triggered_by"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        created_at=row["created_at"],
    )


class TestSuiteRunRepository:
    """Repository for test suite run operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the test suite run repository."""
        self._db = db

    async def create(
        self,
        org_id: UUID,
        suite_id: UUID,
        total_scenarios: int,
        triggered_by: str | None = None,
    ) -> TestSuiteRunRow:
        """Create a new test suite run."""
        run_id = uuid4()

        await self._db.execute(
            f"""
            INSERT INTO test_suite_runs (id, org_id, suite_id, total_scenarios, triggered_by)
            VALUES ($1, $2, $3, $4, $5)
            """,
            run_id,
            org_id,
            suite_id,
            total_scenarios,
            triggered_by,
        )

        row = await self._db.fetchrow(
            f"SELECT {_COLUMNS} FROM test_suite_runs WHERE id = $1",
            run_id,
        )

        if row is None:
            raise RuntimeError("Failed to create test suite run")

        return _row_to_model(row)

    async def get(self, run_id: UUID, org_id: UUID) -> TestSuiteRunRow | None:
        """Get a test suite run by ID and org_id."""
        row = await self._db.fetchrow(
            f"SELECT {_COLUMNS} FROM test_suite_runs WHERE id = $1 AND org_id = $2",
            run_id,
            org_id,
        )
        return _row_to_model(row) if row else None

    async def update(
        self, run_id: UUID, org_id: UUID, updates: dict[str, Any]
    ) -> TestSuiteRunRow | None:
        """Update a test suite run."""
        allowed = {
            "status", "completed_scenarios", "failed_scenarios",
            "started_at", "completed_at",
        }
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return await self.get(run_id, org_id)

        set_clauses = []
        params: list[Any] = []
        for i, (key, value) in enumerate(filtered.items(), start=1):
            set_clauses.append(f"{key} = ${i}")
            params.append(value)

        params.append(run_id)
        params.append(org_id)

        await self._db.execute(
            f"UPDATE test_suite_runs SET {', '.join(set_clauses)} WHERE id = ${len(params) - 1} AND org_id = ${len(params)}",
            *params,
        )

        return await self.get(run_id, org_id)

    async def increment_completed(
        self, run_id: UUID, org_id: UUID
    ) -> TestSuiteRunRow | None:
        """Atomically increment completed_scenarios."""
        await self._db.execute(
            "UPDATE test_suite_runs SET completed_scenarios = completed_scenarios + 1 WHERE id = $1 AND org_id = $2",
            run_id,
            org_id,
        )
        return await self.get(run_id, org_id)

    async def increment_failed(
        self, run_id: UUID, org_id: UUID
    ) -> TestSuiteRunRow | None:
        """Atomically increment failed_scenarios."""
        await self._db.execute(
            "UPDATE test_suite_runs SET failed_scenarios = failed_scenarios + 1 WHERE id = $1 AND org_id = $2",
            run_id,
            org_id,
        )
        return await self.get(run_id, org_id)

    async def list_by_suite(
        self, org_id: UUID, suite_id: UUID
    ) -> list[TestSuiteRunRow]:
        """List all suite runs for a suite."""
        rows = await self._db.fetch(
            f"SELECT {_COLUMNS} FROM test_suite_runs WHERE org_id = $1 AND suite_id = $2 ORDER BY created_at DESC",
            org_id,
            suite_id,
        )
        return [_row_to_model(row) for row in rows]
```

Update `src/voiceobs/server/db/repositories/__init__.py` — add:
```python
from voiceobs.server.db.repositories.test_suite_run import TestSuiteRunRepository
```
And add `"TestSuiteRunRepository"` to `__all__`.

**Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/server/db/test_test_suite_run_repository.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add -f src/voiceobs/server/db/repositories/test_suite_run.py \
  src/voiceobs/server/db/repositories/__init__.py \
  tests/server/db/test_test_suite_run_repository.py
git commit -m "feat: add TestSuiteRunRepository with CRUD and atomic counter operations"
```

---

## Task 4: Update TestExecution Repository

**Files:**
- Modify: `src/voiceobs/server/db/repositories/test_execution.py`
- Modify: `tests/server/routes/test_test_executions.py`
- Create: `tests/server/db/test_test_execution_repository.py`

**Step 1: Write the test**

```python
# tests/server/db/test_test_execution_repository.py
"""Tests for updated TestExecutionRepository."""

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
```

**Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/server/db/test_test_execution_repository.py -v`
Expected: FAIL (new method signatures don't exist)

**Step 3: Rewrite the repository**

Replace `src/voiceobs/server/db/repositories/test_execution.py` entirely with the updated version that:
- `create()` accepts `org_id`, `suite_run_id`, `scenario_id`, `status`
- `get(execution_id, org_id)` with org scoping
- `update(execution_id, org_id, updates_dict)` for status/transcript/audio_url/etc.
- `list_by_suite_run(org_id, suite_run_id)` returns all executions for a run
- Keep existing `get_summary()` for backward compatibility
- All SELECT queries fetch the new columns

Follow the exact same pattern as `TestSuiteRunRepository` from Task 3.

**Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/server/db/test_test_execution_repository.py -v`
Expected: PASS

**Step 5: Fix all broken tests**

Run: `uv run python -m pytest tests/ -v` and fix any tests still using old repository signature.

**Step 6: Commit**

```bash
git add src/voiceobs/server/db/repositories/test_execution.py \
  tests/server/db/test_test_execution_repository.py \
  tests/server/routes/test_test_executions.py
git commit -m "feat: update TestExecutionRepository with org-scoped CRUD and new fields"
```

---

## Task 5: SQS Client Service

**Files:**
- Create: `src/voiceobs/server/services/sqs_client.py`
- Test: `tests/server/services/test_sqs_client.py`

**Step 1: Write the test**

```python
# tests/server/services/test_sqs_client.py
"""Tests for SQS client service."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from voiceobs.server.services.sqs_client import SQSClient


class TestSQSClient:
    """Tests for SQS client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_sqs = MagicMock()
        self.client = SQSClient(
            execution_queue_url="https://sqs.us-east-1.amazonaws.com/123/exec-queue",
            evaluation_queue_url="https://sqs.us-east-1.amazonaws.com/123/eval-queue",
            sqs_client=self.mock_sqs,
        )

    def test_enqueue_execution(self):
        """Test enqueueing an execution message."""
        execution_id = uuid4()
        self.mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        result = self.client.enqueue_execution(execution_id)

        self.mock_sqs.send_message.assert_called_once()
        call_kwargs = self.mock_sqs.send_message.call_args[1]
        assert call_kwargs["QueueUrl"] == self.client._execution_queue_url
        body = json.loads(call_kwargs["MessageBody"])
        assert body["execution_id"] == str(execution_id)
        assert result == "msg-123"

    def test_enqueue_evaluation(self):
        """Test enqueueing an evaluation message."""
        execution_id = uuid4()
        self.mock_sqs.send_message.return_value = {"MessageId": "msg-456"}

        result = self.client.enqueue_evaluation(execution_id)

        self.mock_sqs.send_message.assert_called_once()
        call_kwargs = self.mock_sqs.send_message.call_args[1]
        assert call_kwargs["QueueUrl"] == self.client._evaluation_queue_url
        body = json.loads(call_kwargs["MessageBody"])
        assert body["execution_id"] == str(execution_id)
        assert result == "msg-456"

    def test_enqueue_execution_batch(self):
        """Test batch enqueueing execution messages."""
        execution_ids = [uuid4() for _ in range(3)]
        self.mock_sqs.send_message_batch.return_value = {
            "Successful": [{"Id": str(i)} for i in range(3)],
            "Failed": [],
        }

        failed = self.client.enqueue_execution_batch(execution_ids)

        self.mock_sqs.send_message_batch.assert_called_once()
        assert failed == []

    @patch("voiceobs.server.services.sqs_client.boto3")
    def test_from_env(self, mock_boto3):
        """Test creating client from environment."""
        mock_boto3.client.return_value = MagicMock()

        with patch.dict(
            "os.environ",
            {
                "VOICEOBS_SQS_EXECUTION_QUEUE_URL": "https://sqs/exec",
                "VOICEOBS_SQS_EVALUATION_QUEUE_URL": "https://sqs/eval",
                "AWS_REGION": "us-east-1",
            },
        ):
            client = SQSClient.from_env()
            assert client._execution_queue_url == "https://sqs/exec"
            assert client._evaluation_queue_url == "https://sqs/eval"
```

**Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/server/services/test_sqs_client.py -v`
Expected: FAIL (module not found)

**Step 3: Write the SQS client**

```python
# src/voiceobs/server/services/sqs_client.py
"""SQS client for test execution queues."""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from uuid import UUID

import boto3

logger = logging.getLogger(__name__)


class SQSClient:
    """Client for sending messages to SQS execution and evaluation queues."""

    def __init__(
        self,
        execution_queue_url: str,
        evaluation_queue_url: str,
        sqs_client: Any | None = None,
    ) -> None:
        """Initialize SQS client."""
        self._execution_queue_url = execution_queue_url
        self._evaluation_queue_url = evaluation_queue_url
        self._sqs = sqs_client or boto3.client("sqs")

    @classmethod
    def from_env(cls) -> SQSClient:
        """Create SQS client from environment variables."""
        execution_url = os.environ["VOICEOBS_SQS_EXECUTION_QUEUE_URL"]
        evaluation_url = os.environ["VOICEOBS_SQS_EVALUATION_QUEUE_URL"]
        region = os.environ.get("AWS_REGION", "us-east-1")
        sqs = boto3.client("sqs", region_name=region)
        return cls(execution_url, evaluation_url, sqs)

    def enqueue_execution(self, execution_id: UUID) -> str:
        """Enqueue a single execution message. Returns message ID."""
        response = self._sqs.send_message(
            QueueUrl=self._execution_queue_url,
            MessageBody=json.dumps({"execution_id": str(execution_id)}),
        )
        logger.info(f"Enqueued execution {execution_id}")
        return response["MessageId"]

    def enqueue_evaluation(self, execution_id: UUID) -> str:
        """Enqueue a single evaluation message. Returns message ID."""
        response = self._sqs.send_message(
            QueueUrl=self._evaluation_queue_url,
            MessageBody=json.dumps({"execution_id": str(execution_id)}),
        )
        logger.info(f"Enqueued evaluation {execution_id}")
        return response["MessageId"]

    def enqueue_execution_batch(self, execution_ids: list[UUID]) -> list[UUID]:
        """Enqueue batch of execution messages. Returns list of failed IDs."""
        entries = [
            {
                "Id": str(i),
                "MessageBody": json.dumps({"execution_id": str(eid)}),
            }
            for i, eid in enumerate(execution_ids)
        ]

        # SQS batch max is 10
        failed_ids: list[UUID] = []
        for chunk_start in range(0, len(entries), 10):
            chunk = entries[chunk_start : chunk_start + 10]
            response = self._sqs.send_message_batch(
                QueueUrl=self._execution_queue_url,
                Entries=chunk,
            )
            for fail in response.get("Failed", []):
                idx = int(fail["Id"])
                failed_ids.append(execution_ids[chunk_start + idx])

        return failed_ids
```

**Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/server/services/test_sqs_client.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add -f src/voiceobs/server/services/sqs_client.py \
  tests/server/services/test_sqs_client.py
git commit -m "feat: add SQS client for execution and evaluation queues"
```

---

## Task 6: Pydantic Request/Response Models for Suite Runs

**Files:**
- Create: `src/voiceobs/server/models/request/suite_run.py`
- Create: `src/voiceobs/server/models/response/suite_run.py`
- Modify: `src/voiceobs/server/models/request/__init__.py`
- Modify: `src/voiceobs/server/models/response/__init__.py`
- Modify: `src/voiceobs/server/models/__init__.py`
- Modify: `src/voiceobs/server/models/response/test.py` (update TestExecutionResponse)
- Test: `tests/server/test_suite_run_models.py`

Create these Pydantic models:

**Request models** (`request/suite_run.py`):
- No new request models needed (run endpoints take suite_id/scenario_id from URL path)

**Response models** (`response/suite_run.py`):
- `SuiteRunResponse` — id, suite_id, status, total_scenarios, completed_scenarios, failed_scenarios, triggered_by, started_at, completed_at, created_at, executions (list of `ExecutionSummaryResponse`)
- `SuiteRunTriggerResponse` — suite_run_id, status, total_scenarios (returned from POST /run)
- `ExecutionSummaryResponse` — id, scenario_id, scenario_name, status, audio_url, transcript, evaluation_result, duration_seconds, attempt, error_message

**Updated** `TestExecutionResponse` in `response/test.py`:
- Add: audio_url, transcript, evaluation_result, error_message, duration_seconds, attempt, suite_run_id, org_id

Write tests for model creation and `from_row()` classmethods. Follow the existing `TestScenarioResponse.from_row()` pattern.

**Step 1: Write tests, Step 2: fail, Step 3: implement, Step 4: pass, Step 5: commit.**

```bash
git commit -m "feat: add Pydantic request/response models for suite runs and updated executions"
```

---

## Task 7: Suite Run Routes (Trigger + Poll + Cancel)

**Files:**
- Create: `src/voiceobs/server/routes/suite_runs.py`
- Modify: `src/voiceobs/server/routes/__init__.py`
- Modify: `src/voiceobs/server/app.py`
- Modify: `src/voiceobs/server/dependencies.py` (add suite run repo + SQS client)
- Modify: `src/voiceobs/server/routes/test_dependencies.py` (add helpers)
- Test: `tests/server/routes/test_suite_runs.py`

**Endpoints to implement:**

```python
router = APIRouter(prefix="/api/v1/orgs/{org_id}", tags=["Suite Runs"])

# Trigger: run entire suite
@router.post("/test-suites/{suite_id}/run")
async def run_suite(org_id, suite_id, auth, suite_run_repo, scenario_repo, execution_repo, sqs_client):
    # 1. Validate suite exists and has ready scenarios
    # 2. Create TestSuiteRun row
    # 3. Create TestExecution rows for each scenario (status=pending)
    # 4. Enqueue all execution_ids to SQS execution queue via batch
    # 5. Update execution statuses to "queued"
    # 6. Return SuiteRunTriggerResponse (202)

# Trigger: run single scenario
@router.post("/test-scenarios/{scenario_id}/run")
async def run_scenario(org_id, scenario_id, auth, suite_run_repo, scenario_repo, execution_repo, sqs_client):
    # 1. Validate scenario exists
    # 2. Create TestSuiteRun (total_scenarios=1)
    # 3. Create TestExecution
    # 4. Enqueue to SQS
    # 5. Return SuiteRunTriggerResponse (202)

# Poll status
@router.get("/suite-runs/{suite_run_id}")
async def get_suite_run(org_id, suite_run_id, auth, suite_run_repo, execution_repo):
    # 1. Fetch suite run
    # 2. Fetch all executions for this run
    # 3. Return SuiteRunResponse with embedded executions

# Cancel
@router.post("/suite-runs/{suite_run_id}/cancel")
async def cancel_suite_run(org_id, suite_run_id, auth, suite_run_repo, execution_repo):
    # 1. Update suite run status to "cancelled"
    # 2. Update all pending/queued executions to "cancelled"
    # 3. Return updated SuiteRunResponse

# Get individual execution detail
@router.get("/executions/{execution_id}")
async def get_execution(org_id, execution_id, auth, execution_repo):
    # Return full execution with audio_url, transcript, evaluation_result

# Audio pre-signed URL
@router.get("/executions/{execution_id}/audio")
async def get_execution_audio(org_id, execution_id, auth, execution_repo, audio_storage):
    # Fetch execution, generate presigned URL from audio_url, return redirect or URL
```

**Dependencies to add** in `dependencies.py`:
- `_test_suite_run_repo` global + `get_test_suite_run_repository()`
- `_sqs_client` global + `get_sqs_client()` (lazy, returns None if env vars not set)

**Step 1: Write tests (mock repos + SQS), Step 2: fail, Step 3: implement, Step 4: pass, Step 5: commit.**

```bash
git commit -m "feat: add suite run routes for trigger, poll, cancel, and execution detail"
```

---

## Task 8: Evaluation Schemas

**Files:**
- Create: `src/voiceobs/server/services/evaluation/schemas.py`
- Test: `tests/server/services/test_evaluation_schemas.py`

**Step 1: Write the test**

```python
# tests/server/services/test_evaluation_schemas.py
"""Tests for evaluation schemas."""

from voiceobs.server.services.evaluation.schemas import (
    CriterionResult,
    EvaluationResult,
)


class TestEvaluationSchemas:
    """Tests for evaluation Pydantic schemas."""

    def test_criterion_result(self):
        """Test CriterionResult creation."""
        criterion = CriterionResult(
            name="greeting",
            passed=True,
            score=0.95,
            evidence="Agent said 'Hello, welcome to our service'",
        )
        assert criterion.name == "greeting"
        assert criterion.passed is True

    def test_evaluation_result(self):
        """Test EvaluationResult creation."""
        result = EvaluationResult(
            passed=True,
            score=0.88,
            goal_achieved=True,
            intent_handled=True,
            criteria=[
                CriterionResult(
                    name="greeting", passed=True, score=0.9, evidence="Good greeting"
                ),
            ],
            reasoning="The agent handled the request well.",
        )
        assert result.passed is True
        assert result.score == 0.88
        assert len(result.criteria) == 1

    def test_evaluation_result_to_dict(self):
        """Test serialization to dict for storing in JSONB."""
        result = EvaluationResult(
            passed=False,
            score=0.3,
            goal_achieved=False,
            intent_handled=True,
            criteria=[],
            reasoning="Agent failed to fulfill the order.",
        )
        d = result.model_dump()
        assert d["passed"] is False
        assert d["score"] == 0.3
```

**Step 2: fail, Step 3: implement, Step 4: pass**

```python
# src/voiceobs/server/services/evaluation/__init__.py
# (empty)

# src/voiceobs/server/services/evaluation/schemas.py
"""Evaluation result schemas."""

from pydantic import BaseModel, Field


class CriterionResult(BaseModel):
    """Result for a single evaluation criterion."""

    name: str = Field(..., description="Criterion name (e.g., 'greeting', 'tone')")
    passed: bool = Field(..., description="Whether this criterion passed")
    score: float = Field(..., ge=0.0, le=1.0, description="Score for this criterion")
    evidence: str = Field(..., description="Transcript quote supporting judgment")


class EvaluationResult(BaseModel):
    """Full evaluation result from LLM."""

    passed: bool = Field(..., description="Overall pass/fail")
    score: float = Field(..., ge=0.0, le=1.0, description="Overall score")
    goal_achieved: bool = Field(..., description="Did agent fulfill scenario goal?")
    intent_handled: bool = Field(..., description="Did agent handle the intent?")
    criteria: list[CriterionResult] = Field(..., description="Per-criterion breakdown")
    reasoning: str = Field(..., description="LLM explanation of evaluation")
```

**Step 5: Commit**

```bash
git commit -m "feat: add evaluation schemas (EvaluationResult, CriterionResult)"
```

---

## Task 9: Evaluation Service

**Files:**
- Create: `src/voiceobs/server/services/evaluation/service.py`
- Test: `tests/server/services/test_evaluation_service.py`

The evaluation service:
1. Takes an execution_id
2. Fetches the execution (with transcript), scenario (with goal/intent/caller_behaviors), agent, and suite (for evaluation_strictness)
3. Builds a prompt: "Evaluate this conversation..." with the full transcript and success criteria
4. Calls `LLMService.generate_structured(prompt, EvaluationResult)`
5. Returns the `EvaluationResult`

Follow the existing `ScenarioGenerationService` pattern for dependency injection (repos + llm_service in constructor).

**Step 1: Write tests (mock LLM + repos), Step 2: fail, Step 3: implement, Step 4: pass, Step 5: commit.**

```bash
git commit -m "feat: add EvaluationService for LLM-based test result evaluation"
```

---

## Task 10: Execution Orchestration Service

**Files:**
- Create: `src/voiceobs/server/services/execution/service.py`
- Create: `src/voiceobs/server/services/execution/__init__.py`
- Test: `tests/server/services/test_execution_service.py`

This is the core orchestration service that:
1. Creates suite runs and executions (used by routes)
2. Provides `trigger_suite_run(org_id, suite_id, triggered_by)` and `trigger_scenario_run(org_id, scenario_id, triggered_by)`
3. Each creates the DB records and calls `sqs_client.enqueue_execution_batch()`

Dependencies: `TestSuiteRunRepository`, `TestExecutionRepository`, `TestScenarioRepository`, `TestSuiteRepository`, `SQSClient`

**Step 1: Write tests, Step 2: fail, Step 3: implement, Step 4: pass, Step 5: commit.**

```bash
git commit -m "feat: add ExecutionOrchestrationService for triggering suite/scenario runs"
```

---

## Task 11: Call Execution Worker (Stub)

**Files:**
- Create: `src/voiceobs/server/workers/__init__.py`
- Create: `src/voiceobs/server/workers/call_worker.py`
- Test: `tests/server/workers/test_call_worker.py`

This is the **worker that polls SQS Execution Queue** and runs calls. For this task, implement the worker skeleton:

1. `CallWorker` class with `concurrency` parameter (asyncio.Semaphore)
2. `poll_loop()` — long-polls SQS, dispatches to `process_message()`
3. `process_message(message)` — parses execution_id, calls `execute_scenario()`
4. `execute_scenario(execution_id)` — **stub** that updates status to calling → completed (actual LiveKit integration in a later task)
5. Handles SQS message deletion on success, visibility timeout extension during processing

Test with mocked SQS client and repos.

**Step 1: Write tests, Step 2: fail, Step 3: implement, Step 4: pass, Step 5: commit.**

```bash
git commit -m "feat: add CallWorker skeleton for SQS execution queue polling"
```

---

## Task 12: Evaluation Worker

**Files:**
- Create: `src/voiceobs/server/workers/eval_worker.py`
- Test: `tests/server/workers/test_eval_worker.py`

Similar to CallWorker but polls the Evaluation Queue:

1. `EvalWorker` class with `concurrency` parameter
2. `poll_loop()` — polls SQS Evaluation Queue
3. `process_message(message)` — parses execution_id, calls `evaluate_execution()`
4. `evaluate_execution(execution_id)` — calls `EvaluationService.evaluate()`, saves result to DB, increments suite run counters, checks if suite run is complete

Test with mocked SQS, repos, and evaluation service.

**Step 1: Write tests, Step 2: fail, Step 3: implement, Step 4: pass, Step 5: commit.**

```bash
git commit -m "feat: add EvalWorker for SQS evaluation queue polling"
```

---

## Task 13: Worker CLI Entry Point

**Files:**
- Create: `src/voiceobs/server/workers/cli.py`
- Modify: `pyproject.toml` (add worker entry point)
- Test: `tests/server/workers/test_worker_cli.py`

Create a CLI command to start the worker process:

```python
# src/voiceobs/server/workers/cli.py
"""Worker CLI entry point."""

import asyncio
import logging
import os

from voiceobs.server.workers.call_worker import CallWorker
from voiceobs.server.workers.eval_worker import EvalWorker


def start_worker():
    """Start the worker process with both call and eval workers."""
    call_concurrency = int(os.environ.get("VOICEOBS_WORKER_CALL_CONCURRENCY", "10"))
    eval_concurrency = int(os.environ.get("VOICEOBS_WORKER_EVAL_CONCURRENCY", "20"))

    call_worker = CallWorker(concurrency=call_concurrency)
    eval_worker = EvalWorker(concurrency=eval_concurrency)

    asyncio.run(_run_workers(call_worker, eval_worker))


async def _run_workers(call_worker, eval_worker):
    """Run both workers concurrently."""
    await asyncio.gather(
        call_worker.poll_loop(),
        eval_worker.poll_loop(),
    )
```

Add to `pyproject.toml` under `[project.scripts]`:
```toml
voiceobs-worker = "voiceobs.server.workers.cli:start_worker"
```

**Step 1: Write tests, Step 2: fail, Step 3: implement, Step 4: pass, Step 5: commit.**

```bash
git commit -m "feat: add worker CLI entry point for starting call and eval workers"
```

---

## Task 14: Wire Up Dependencies and Registration

**Files:**
- Modify: `src/voiceobs/server/dependencies.py`
- Modify: `src/voiceobs/server/routes/__init__.py`
- Modify: `src/voiceobs/server/app.py`
- Modify: `src/voiceobs/server/routes/test_dependencies.py`

Wire everything together:

1. Add to `dependencies.py`:
   - `_test_suite_run_repo` global + init in `init_database()` + getter + reset
   - `_sqs_client` global + `get_sqs_client()` (lazy from env, returns None if not configured)
   - `get_execution_orchestration_service()` (lazy)
   - `get_evaluation_service()` (lazy)

2. Add to `routes/__init__.py`:
   - Import and export `suite_runs_router`

3. Add to `app.py`:
   - `app.include_router(suite_runs_router)`

4. Add to `test_dependencies.py`:
   - `get_test_suite_run_repo()` dependency function
   - `parse_suite_run_id()` helper

**Step 1: Write tests, Step 2: fail, Step 3: implement, Step 4: pass, Step 5: commit.**

```bash
git commit -m "feat: wire up suite run repos, SQS client, and routes in dependency injection"
```

---

## Task 15: Run Full Test Suite + Lint + Coverage

**Step 1: Run linter**

```bash
uv run ruff check src/voiceobs/ --fix
uv run ruff check tests/ --fix
```

**Step 2: Run all tests**

```bash
uv run python -m pytest tests/ -v
```

Fix any failures.

**Step 3: Check coverage**

```bash
uv run python -m pytest tests/ --cov=src/voiceobs --cov-report=term-missing --cov-branch
```

Ensure new code has >95% line and branch coverage. Add tests for any uncovered paths.

**Step 4: Commit any fixes**

```bash
git commit -m "fix: resolve lint issues and ensure test coverage >95%"
```

---

## Summary of Tasks

| # | Task | New Files | Modified Files |
|---|------|-----------|---------------|
| 1 | TestSuiteRun model + migration | 3 | 1 |
| 2 | Update TestExecutionRow model | 1 | 1 |
| 3 | TestSuiteRun repository | 2 | 1 |
| 4 | Update TestExecution repository | 1 | 1 |
| 5 | SQS client service | 2 | 0 |
| 6 | Pydantic request/response models | 3 | 3 |
| 7 | Suite run routes | 2 | 4 |
| 8 | Evaluation schemas | 2 | 0 |
| 9 | Evaluation service | 2 | 0 |
| 10 | Execution orchestration service | 2 | 0 |
| 11 | Call worker (stub) | 3 | 0 |
| 12 | Evaluation worker | 2 | 0 |
| 13 | Worker CLI entry point | 2 | 1 |
| 14 | Wire up dependencies | 0 | 4 |
| 15 | Full test + lint + coverage | 0 | varies |

**Future tasks** (not in this plan — to be designed separately):
- Task N+1: LiveKit/SIP call execution (replace stub in CallWorker)
- Task N+2: Deepgram real-time STT integration
- Task N+3: Audio recording + S3 upload during calls
- Task N+4: Circuit breaker for suite runs
- Task N+5: Auto-scaling configuration (CloudWatch + ECS/K8s)
