"""Tests for the metrics aggregation endpoints."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from voiceobs.server.db.repositories.metrics import MetricsRepository


class TestMetricsSummary:
    """Tests for GET /metrics/summary endpoint."""

    def test_summary_requires_postgres(self, client):
        """Test that summary endpoint requires PostgreSQL."""
        response = client.get("/metrics/summary")

        assert response.status_code == 501
        assert "PostgreSQL" in response.json()["detail"]

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_summary_success(self, mock_get_repo, mock_is_postgres, client):
        """Test successful summary retrieval."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_summary.return_value = {
            "total_conversations": 100,
            "total_turns": 500,
            "total_duration_ms": 125000.0,
            "avg_latency_p50_ms": 150.0,
            "avg_latency_p95_ms": 300.0,
            "avg_latency_p99_ms": 450.0,
            "failure_rate": 2.5,
            "total_failures": 25,
            "silence_mean_ms": 850.0,
            "overlap_count": 10,
        }
        mock_get_repo.return_value = mock_repo

        response = client.get("/metrics/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_conversations"] == 100
        assert data["total_turns"] == 500
        assert data["total_duration_ms"] == 125000.0
        assert data["avg_latency_p50_ms"] == 150.0
        assert data["avg_latency_p95_ms"] == 300.0
        assert data["avg_latency_p99_ms"] == 450.0
        assert data["failure_rate"] == 2.5
        assert data["total_failures"] == 25
        assert data["silence_mean_ms"] == 850.0
        assert data["overlap_count"] == 10

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_summary_with_filters(self, mock_get_repo, mock_is_postgres, client):
        """Test summary with time and conversation filters."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_summary.return_value = {
            "total_conversations": 10,
            "total_turns": 50,
            "total_duration_ms": 12500.0,
            "avg_latency_p50_ms": 150.0,
            "avg_latency_p95_ms": 300.0,
            "avg_latency_p99_ms": 450.0,
            "failure_rate": 0.0,
            "total_failures": 0,
            "silence_mean_ms": None,
            "overlap_count": 0,
        }
        mock_get_repo.return_value = mock_repo

        start_time = datetime.now(UTC) - timedelta(days=1)
        end_time = datetime.now(UTC)
        start_time_str = start_time.replace(tzinfo=None).isoformat() + "Z"
        end_time_str = end_time.replace(tzinfo=None).isoformat() + "Z"
        response = client.get(
            f"/metrics/summary?start_time={start_time_str}&end_time={end_time_str}&conversation_id=conv-1"
        )

        assert response.status_code == 200
        mock_repo.get_summary.assert_called_once()
        call_args = mock_repo.get_summary.call_args
        assert call_args[1]["conversation_id"] == "conv-1"
        assert call_args[1]["start_time"] is not None
        assert call_args[1]["end_time"] is not None

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_summary_repository_none(self, mock_get_repo, mock_is_postgres, client):
        """Test summary when repository is None."""
        mock_is_postgres.return_value = True
        mock_get_repo.return_value = None

        response = client.get("/metrics/summary")

        assert response.status_code == 500
        assert "not available" in response.json()["detail"]


class TestLatencyBreakdown:
    """Tests for GET /metrics/latency endpoint."""

    def test_latency_requires_postgres(self, client):
        """Test that latency endpoint requires PostgreSQL."""
        response = client.get("/metrics/latency")

        assert response.status_code == 501
        assert "PostgreSQL" in response.json()["detail"]

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_latency_by_stage(self, mock_get_repo, mock_is_postgres, client):
        """Test latency breakdown by stage."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_latency_breakdown.return_value = [
            {
                "group": "asr",
                "count": 100,
                "mean_ms": 145.5,
                "p50_ms": 132.0,
                "p95_ms": 210.5,
                "p99_ms": 285.0,
            },
            {
                "group": "llm",
                "count": 100,
                "mean_ms": 850.0,
                "p50_ms": 750.0,
                "p95_ms": 1200.0,
                "p99_ms": 1500.0,
            },
        ]
        mock_get_repo.return_value = mock_repo

        response = client.get("/metrics/latency?group_by=stage")

        assert response.status_code == 200
        data = response.json()
        assert len(data["breakdown"]) == 2
        assert data["breakdown"][0]["group"] == "asr"
        assert data["breakdown"][0]["count"] == 100
        assert data["breakdown"][0]["p50_ms"] == 132.0
        assert data["breakdown"][1]["group"] == "llm"
        assert data["breakdown"][1]["p95_ms"] == 1200.0

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_latency_with_filters(self, mock_get_repo, mock_is_postgres, client):
        """Test latency breakdown with filters."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_latency_breakdown.return_value = []
        mock_get_repo.return_value = mock_repo

        start_time = datetime.now(UTC) - timedelta(days=1)
        start_time_str = start_time.replace(tzinfo=None).isoformat() + "Z"
        response = client.get(
            f"/metrics/latency?group_by=stage&start_time={start_time_str}&conversation_id=conv-1"
        )

        assert response.status_code == 200
        mock_repo.get_latency_breakdown.assert_called_once()
        call_args = mock_repo.get_latency_breakdown.call_args
        assert call_args[1]["group_by"] == "stage"
        assert call_args[1]["conversation_id"] == "conv-1"
        assert call_args[1]["start_time"] is not None


class TestFailureBreakdown:
    """Tests for GET /metrics/failures endpoint."""

    def test_failures_requires_postgres(self, client):
        """Test that failures endpoint requires PostgreSQL."""
        response = client.get("/metrics/failures")

        assert response.status_code == 501
        assert "PostgreSQL" in response.json()["detail"]

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_failures_by_type(self, mock_get_repo, mock_is_postgres, client):
        """Test failure breakdown by type."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_failure_breakdown.return_value = (
            [
                {"group": "high_latency", "count": 10, "percentage": 40.0},
                {"group": "interruption", "count": 15, "percentage": 60.0},
            ],
            25,
        )
        mock_get_repo.return_value = mock_repo

        response = client.get("/metrics/failures?group_by=type")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["breakdown"]) == 2
        assert data["breakdown"][0]["group"] == "high_latency"
        assert data["breakdown"][0]["count"] == 10
        assert data["breakdown"][0]["percentage"] == 40.0
        assert data["breakdown"][1]["group"] == "interruption"
        assert data["breakdown"][1]["percentage"] == 60.0

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_failures_by_severity(self, mock_get_repo, mock_is_postgres, client):
        """Test failure breakdown by severity."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_failure_breakdown.return_value = (
            [
                {"group": "high", "count": 5, "percentage": 50.0},
                {"group": "medium", "count": 5, "percentage": 50.0},
            ],
            10,
        )
        mock_get_repo.return_value = mock_repo

        response = client.get("/metrics/failures?group_by=severity")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["breakdown"]) == 2

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_failures_with_filters(self, mock_get_repo, mock_is_postgres, client):
        """Test failure breakdown with filters."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_failure_breakdown.return_value = ([], 0)
        mock_get_repo.return_value = mock_repo

        end_time = datetime.now(UTC)
        end_time_str = end_time.replace(tzinfo=None).isoformat() + "Z"
        response = client.get(
            f"/metrics/failures?group_by=type&end_time={end_time_str}&conversation_id=conv-1"
        )

        assert response.status_code == 200
        mock_repo.get_failure_breakdown.assert_called_once()
        call_args = mock_repo.get_failure_breakdown.call_args
        assert call_args[1]["group_by"] == "type"
        assert call_args[1]["conversation_id"] == "conv-1"
        assert call_args[1]["end_time"] is not None


class TestConversationVolume:
    """Tests for GET /metrics/conversations endpoint."""

    def test_volume_requires_postgres(self, client):
        """Test that volume endpoint requires PostgreSQL."""
        response = client.get("/metrics/conversations")

        assert response.status_code == 501
        assert "PostgreSQL" in response.json()["detail"]

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_volume_by_hour(self, mock_get_repo, mock_is_postgres, client):
        """Test conversation volume grouped by hour."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_conversation_volume.return_value = [
            {"time_bucket": "2024-01-15T10:00:00Z", "count": 5},
            {"time_bucket": "2024-01-15T11:00:00Z", "count": 8},
            {"time_bucket": "2024-01-15T12:00:00Z", "count": 12},
        ]
        mock_get_repo.return_value = mock_repo

        response = client.get("/metrics/conversations?group_by=hour")

        assert response.status_code == 200
        data = response.json()
        assert len(data["volume"]) == 3
        assert data["volume"][0]["time_bucket"] == "2024-01-15T10:00:00Z"
        assert data["volume"][0]["count"] == 5
        assert data["volume"][2]["count"] == 12

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_volume_by_day(self, mock_get_repo, mock_is_postgres, client):
        """Test conversation volume grouped by day."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_conversation_volume.return_value = [
            {"time_bucket": "2024-01-15T00:00:00Z", "count": 50},
            {"time_bucket": "2024-01-16T00:00:00Z", "count": 75},
        ]
        mock_get_repo.return_value = mock_repo

        response = client.get("/metrics/conversations?group_by=day")

        assert response.status_code == 200
        data = response.json()
        assert len(data["volume"]) == 2
        mock_repo.get_conversation_volume.assert_called_once_with(
            group_by="day", start_time=None, end_time=None, conversation_id=None
        )

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_volume_with_filters(self, mock_get_repo, mock_is_postgres, client):
        """Test conversation volume with filters."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_conversation_volume.return_value = []
        mock_get_repo.return_value = mock_repo

        start_time = datetime.now(UTC) - timedelta(days=7)
        end_time = datetime.now(UTC)
        start_time_str = start_time.replace(tzinfo=None).isoformat() + "Z"
        end_time_str = end_time.replace(tzinfo=None).isoformat() + "Z"
        response = client.get(
            f"/metrics/conversations?group_by=week&start_time={start_time_str}&end_time={end_time_str}"
        )

        assert response.status_code == 200
        mock_repo.get_conversation_volume.assert_called_once()
        call_args = mock_repo.get_conversation_volume.call_args
        assert call_args[1]["group_by"] == "week"
        assert call_args[1]["start_time"] is not None
        assert call_args[1]["end_time"] is not None


class TestTrends:
    """Tests for GET /metrics/trends endpoint."""

    def test_trends_requires_postgres(self, client):
        """Test that trends endpoint requires PostgreSQL."""
        response = client.get("/metrics/trends")

        assert response.status_code == 501
        assert "PostgreSQL" in response.json()["detail"]

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_trends_latency(self, mock_get_repo, mock_is_postgres, client):
        """Test trends for latency metric."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_trends.return_value = [
            {
                "timestamp": "2024-01-15T10:00:00Z",
                "value": 150.0,
                "rolling_avg": 145.5,
            },
            {
                "timestamp": "2024-01-15T11:00:00Z",
                "value": 160.0,
                "rolling_avg": 155.0,
            },
        ]
        mock_get_repo.return_value = mock_repo

        response = client.get("/metrics/trends?metric=latency&window=1h")

        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "latency"
        assert data["window"] == "1h"
        assert len(data["data_points"]) == 2
        assert data["data_points"][0]["timestamp"] == "2024-01-15T10:00:00Z"
        assert data["data_points"][0]["value"] == 150.0
        assert data["data_points"][0]["rolling_avg"] == 145.5

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_trends_failures(self, mock_get_repo, mock_is_postgres, client):
        """Test trends for failures metric."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_trends.return_value = [
            {"timestamp": "2024-01-15T10:00:00Z", "value": 5.0, "rolling_avg": 4.5},
            {"timestamp": "2024-01-15T11:00:00Z", "value": 3.0, "rolling_avg": 4.0},
        ]
        mock_get_repo.return_value = mock_repo

        response = client.get("/metrics/trends?metric=failures&window=1d")

        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "failures"
        assert data["window"] == "1d"
        assert len(data["data_points"]) == 2

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_trends_conversations(self, mock_get_repo, mock_is_postgres, client):
        """Test trends for conversations metric."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_trends.return_value = [
            {"timestamp": "2024-01-15T10:00:00Z", "value": 10.0, "rolling_avg": 9.5},
        ]
        mock_get_repo.return_value = mock_repo

        response = client.get("/metrics/trends?metric=conversations&window=1w")

        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "conversations"
        assert data["window"] == "1w"

    @patch("voiceobs.server.routes.metrics.is_using_postgres")
    @patch("voiceobs.server.routes.metrics.get_metrics_repository")
    def test_trends_with_filters(self, mock_get_repo, mock_is_postgres, client):
        """Test trends with filters."""
        mock_is_postgres.return_value = True
        mock_repo = AsyncMock()
        mock_repo.get_trends.return_value = []
        mock_get_repo.return_value = mock_repo

        start_time = datetime.now(UTC) - timedelta(days=1)
        start_time_str = start_time.replace(tzinfo=None).isoformat() + "Z"
        response = client.get(
            f"/metrics/trends?metric=latency&window=1h&start_time={start_time_str}&conversation_id=conv-1"
        )

        assert response.status_code == 200
        mock_repo.get_trends.assert_called_once()
        call_args = mock_repo.get_trends.call_args
        assert call_args[1]["metric"] == "latency"
        assert call_args[1]["window"] == "1h"
        assert call_args[1]["conversation_id"] == "conv-1"
        assert call_args[1]["start_time"] is not None


class TestMetricsRepository:
    """Tests for MetricsRepository class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        from unittest.mock import AsyncMock

        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_summary_empty(self, mock_db):
        """Test get_summary with no data."""

        mock_db.fetchrow = AsyncMock(return_value=None)
        repo = MetricsRepository(mock_db)

        result = await repo.get_summary()

        assert result["total_conversations"] == 0
        assert result["total_turns"] == 0
        assert result["total_failures"] == 0
        assert result["overlap_count"] == 0

    @pytest.mark.asyncio
    async def test_get_summary_with_data(self, mock_db):
        """Test get_summary with data."""
        from tests.server.db.conftest import MockRecord

        mock_row = MockRecord(
            {
                "total_conversations": 100,
                "total_turns": 500,
                "total_duration_ms": 125000.0,
                "p50_latency": 150.0,
                "p95_latency": 300.0,
                "p99_latency": 450.0,
                "total_failures": 25,
                "silence_mean_ms": 850.0,
                "overlap_count": 10,
            }
        )
        mock_db.fetchrow = AsyncMock(return_value=mock_row)
        repo = MetricsRepository(mock_db)

        result = await repo.get_summary()

        assert result["total_conversations"] == 100
        assert result["total_turns"] == 500
        assert result["failure_rate"] == 25.0  # 25/100 * 100

    @pytest.mark.asyncio
    async def test_get_latency_breakdown(self, mock_db):
        """Test get_latency_breakdown."""
        from tests.server.db.conftest import MockRecord

        mock_rows = [
            MockRecord(
                {
                    "group_name": "asr",
                    "count": 100,
                    "mean_ms": 145.5,
                    "p50_ms": 132.0,
                    "p95_ms": 210.5,
                    "p99_ms": 285.0,
                }
            ),
        ]
        mock_db.fetch = AsyncMock(return_value=mock_rows)
        repo = MetricsRepository(mock_db)

        result = await repo.get_latency_breakdown(group_by="stage")

        assert len(result) == 1
        assert result[0]["group"] == "asr"
        assert result[0]["count"] == 100
        assert result[0]["p50_ms"] == 132.0

    @pytest.mark.asyncio
    async def test_get_failure_breakdown(self, mock_db):
        """Test get_failure_breakdown."""
        from tests.server.db.conftest import MockRecord

        mock_rows = [
            MockRecord({"group_name": "high_latency", "count": 10}),
            MockRecord({"group_name": "interruption", "count": 15}),
        ]
        mock_total_row = MockRecord({"total": 25})
        mock_db.fetch = AsyncMock(return_value=mock_rows)
        mock_db.fetchrow = AsyncMock(return_value=mock_total_row)
        repo = MetricsRepository(mock_db)

        breakdown, total = await repo.get_failure_breakdown(group_by="type")

        assert total == 25
        assert len(breakdown) == 2
        assert breakdown[0]["group"] == "high_latency"
        assert breakdown[0]["count"] == 10
        assert breakdown[0]["percentage"] == 40.0  # 10/25 * 100

    @pytest.mark.asyncio
    async def test_get_conversation_volume(self, mock_db):
        """Test get_conversation_volume."""
        from tests.server.db.conftest import MockRecord

        mock_rows = [
            MockRecord({"time_bucket": "2024-01-15T10:00:00Z", "count": 5}),
            MockRecord({"time_bucket": "2024-01-15T11:00:00Z", "count": 8}),
        ]
        mock_db.fetch = AsyncMock(return_value=mock_rows)
        repo = MetricsRepository(mock_db)

        result = await repo.get_conversation_volume(group_by="hour")

        assert len(result) == 2
        assert result[0]["time_bucket"] == "2024-01-15T10:00:00Z"
        assert result[0]["count"] == 5

    @pytest.mark.asyncio
    async def test_get_trends(self, mock_db):
        """Test get_trends."""
        from tests.server.db.conftest import MockRecord

        mock_rows = [
            MockRecord(
                {
                    "timestamp": "2024-01-15T10:00:00Z",
                    "value": 150.0,
                    "rolling_avg": 145.5,
                }
            ),
        ]
        mock_db.fetch = AsyncMock(return_value=mock_rows)
        repo = MetricsRepository(mock_db)

        result = await repo.get_trends(metric="latency", window="1h")

        assert len(result) == 1
        assert result[0]["timestamp"] == "2024-01-15T10:00:00Z"
        assert result[0]["value"] == 150.0
        assert result[0]["rolling_avg"] == 145.5
