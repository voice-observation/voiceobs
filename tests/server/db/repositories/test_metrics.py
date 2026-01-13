"""Tests for the MetricsRepository class."""

from datetime import datetime, timezone

import pytest

from voiceobs.server.db.repositories.metrics import MetricsRepository

from .conftest import MockRecord


class TestMetricsRepository:
    """Tests for the MetricsRepository class."""

    @pytest.mark.asyncio
    async def test_get_summary_no_filters(self, mock_db):
        """Test get_summary with no filters."""
        repo = MetricsRepository(mock_db)
        mock_db.fetchrow.return_value = MockRecord(
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

        result = await repo.get_summary()

        assert result["total_conversations"] == 100
        assert result["total_turns"] == 500
        assert result["total_duration_ms"] == 125000.0
        assert result["avg_latency_p50_ms"] == 150.0
        assert result["avg_latency_p95_ms"] == 300.0
        assert result["avg_latency_p99_ms"] == 450.0
        assert result["failure_rate"] == 25.0  # 25/100 * 100
        assert result["total_failures"] == 25
        assert result["silence_mean_ms"] == 850.0
        assert result["overlap_count"] == 10

    @pytest.mark.asyncio
    async def test_get_summary_with_filters(self, mock_db):
        """Test get_summary with time and conversation filters."""
        repo = MetricsRepository(mock_db)
        start_time = datetime.now(timezone.utc)
        end_time = datetime.now(timezone.utc)
        mock_db.fetchrow.return_value = MockRecord(
            {
                "total_conversations": 10,
                "total_turns": 50,
                "total_duration_ms": 12500.0,
                "p50_latency": 150.0,
                "p95_latency": 300.0,
                "p99_latency": 450.0,
                "total_failures": 0,
                "silence_mean_ms": None,
                "overlap_count": 0,
            }
        )

        result = await repo.get_summary(
            start_time=start_time, end_time=end_time, conversation_id="conv-1"
        )

        assert result["total_conversations"] == 10
        assert result["failure_rate"] == 0.0
        # Verify filters were applied
        assert start_time in mock_db.fetchrow.call_args[0][1:]
        assert end_time in mock_db.fetchrow.call_args[0][1:]
        assert "conv-1" in mock_db.fetchrow.call_args[0][1:]

    @pytest.mark.asyncio
    async def test_get_summary_none_result(self, mock_db):
        """Test get_summary when fetchrow returns None."""
        repo = MetricsRepository(mock_db)
        mock_db.fetchrow.return_value = None

        result = await repo.get_summary()

        assert result["total_conversations"] == 0
        assert result["total_turns"] == 0
        assert result["total_duration_ms"] is None
        assert result["avg_latency_p50_ms"] is None
        assert result["failure_rate"] is None
        assert result["total_failures"] == 0

    @pytest.mark.asyncio
    async def test_get_summary_null_values(self, mock_db):
        """Test get_summary handles null values correctly."""
        repo = MetricsRepository(mock_db)
        mock_db.fetchrow.return_value = MockRecord(
            {
                "total_conversations": 0,
                "total_turns": None,
                "total_duration_ms": None,
                "p50_latency": None,
                "p95_latency": None,
                "p99_latency": None,
                "total_failures": 0,
                "silence_mean_ms": None,
                "overlap_count": None,
            }
        )

        result = await repo.get_summary()

        assert result["total_conversations"] == 0
        assert result["total_turns"] == 0
        assert result["total_duration_ms"] is None
        assert result["avg_latency_p50_ms"] is None
        assert result["failure_rate"] is None
        assert result["overlap_count"] == 0

    @pytest.mark.asyncio
    async def test_get_summary_zero_conversations(self, mock_db):
        """Test get_summary with zero conversations."""
        repo = MetricsRepository(mock_db)
        mock_db.fetchrow.return_value = MockRecord(
            {
                "total_conversations": 0,
                "total_turns": 0,
                "total_duration_ms": 0.0,
                "p50_latency": None,
                "p95_latency": None,
                "p99_latency": None,
                "total_failures": 0,
                "silence_mean_ms": None,
                "overlap_count": 0,
            }
        )

        result = await repo.get_summary()

        assert result["total_conversations"] == 0
        assert result["failure_rate"] is None  # Division by zero

    @pytest.mark.asyncio
    async def test_get_latency_breakdown_by_stage(self, mock_db):
        """Test get_latency_breakdown grouped by stage."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "group_name": "asr",
                    "count": 100,
                    "mean_ms": 150.5,
                    "p50_ms": 140.0,
                    "p95_ms": 200.0,
                    "p99_ms": 250.0,
                }
            )
        ]

        result = await repo.get_latency_breakdown(group_by="stage")

        assert len(result) == 1
        assert result[0]["group"] == "asr"
        assert result[0]["count"] == 100
        assert result[0]["mean_ms"] == 150.5
        assert result[0]["p50_ms"] == 140.0
        query = mock_db.fetch.call_args[0][0]
        assert "voice.stage.type" in query

    @pytest.mark.asyncio
    async def test_get_latency_breakdown_by_custom_attribute(self, mock_db):
        """Test get_latency_breakdown grouped by custom attribute."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = []

        result = await repo.get_latency_breakdown(group_by="custom.attr")

        assert len(result) == 0
        query = mock_db.fetch.call_args[0][0]
        assert "custom.attr" in query

    @pytest.mark.asyncio
    async def test_get_latency_breakdown_with_filters(self, mock_db):
        """Test get_latency_breakdown with filters."""
        repo = MetricsRepository(mock_db)
        start_time = datetime.now(timezone.utc)
        mock_db.fetch.return_value = []

        result = await repo.get_latency_breakdown(start_time=start_time, conversation_id="conv-1")

        assert len(result) == 0
        assert start_time in mock_db.fetch.call_args[0][1:]
        assert "conv-1" in mock_db.fetch.call_args[0][1:]

    @pytest.mark.asyncio
    async def test_get_latency_breakdown_null_values(self, mock_db):
        """Test get_latency_breakdown handles null values."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "group_name": "asr",
                    "count": 10,
                    "mean_ms": None,
                    "p50_ms": None,
                    "p95_ms": None,
                    "p99_ms": None,
                }
            )
        ]

        result = await repo.get_latency_breakdown()

        assert result[0]["mean_ms"] is None
        assert result[0]["p50_ms"] is None

    @pytest.mark.asyncio
    async def test_get_failure_breakdown_by_type(self, mock_db):
        """Test get_failure_breakdown grouped by type."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({"group_name": "timeout", "count": 10}),
            MockRecord({"group_name": "error", "count": 5}),
        ]
        mock_db.fetchrow.return_value = MockRecord({"total": 15})

        breakdown, total = await repo.get_failure_breakdown(group_by="type")

        assert len(breakdown) == 2
        assert breakdown[0]["group"] == "timeout"
        assert breakdown[0]["count"] == 10
        assert breakdown[0]["percentage"] == pytest.approx(66.67, abs=0.01)
        assert total == 15

    @pytest.mark.asyncio
    async def test_get_failure_breakdown_by_severity(self, mock_db):
        """Test get_failure_breakdown grouped by severity."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({"group_name": "high", "count": 8}),
        ]
        mock_db.fetchrow.return_value = MockRecord({"total": 8})

        breakdown, total = await repo.get_failure_breakdown(group_by="severity")

        assert len(breakdown) == 1
        assert breakdown[0]["group"] == "high"
        assert breakdown[0]["percentage"] == 100.0
        query = mock_db.fetch.call_args[0][0]
        assert "f.severity" in query

    @pytest.mark.asyncio
    async def test_get_failure_breakdown_with_filters(self, mock_db):
        """Test get_failure_breakdown with filters."""
        repo = MetricsRepository(mock_db)
        start_time = datetime.now(timezone.utc)
        mock_db.fetch.return_value = []
        mock_db.fetchrow.return_value = MockRecord({"total": 0})

        breakdown, total = await repo.get_failure_breakdown(
            start_time=start_time, conversation_id="conv-1"
        )

        assert len(breakdown) == 0
        assert total == 0
        assert start_time in mock_db.fetch.call_args[0][1:]

    @pytest.mark.asyncio
    async def test_get_failure_breakdown_zero_total(self, mock_db):
        """Test get_failure_breakdown when total is zero."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({"group_name": "timeout", "count": 0}),
        ]
        mock_db.fetchrow.return_value = MockRecord({"total": 0})

        breakdown, total = await repo.get_failure_breakdown()

        assert len(breakdown) == 1
        # When total is 0, percentage should be None (division by zero)
        assert breakdown[0]["percentage"] is None
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_failure_breakdown_none_total(self, mock_db):
        """Test get_failure_breakdown when total is None."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchrow.return_value = None

        breakdown, total = await repo.get_failure_breakdown()

        assert len(breakdown) == 0
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_conversation_volume_by_hour(self, mock_db):
        """Test get_conversation_volume grouped by hour."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({"time_bucket": "2024-01-01T10:00:00Z", "count": 5}),
            MockRecord({"time_bucket": "2024-01-01T11:00:00Z", "count": 3}),
        ]

        result = await repo.get_conversation_volume(group_by="hour")

        assert len(result) == 2
        assert result[0]["time_bucket"] == "2024-01-01T10:00:00Z"
        assert result[0]["count"] == 5
        query = mock_db.fetch.call_args[0][0]
        assert "date_trunc('hour'" in query

    @pytest.mark.asyncio
    async def test_get_conversation_volume_by_day(self, mock_db):
        """Test get_conversation_volume grouped by day."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({"time_bucket": "2024-01-01T00:00:00Z", "count": 20}),
        ]

        result = await repo.get_conversation_volume(group_by="day")

        assert len(result) == 1
        query = mock_db.fetch.call_args[0][0]
        assert "date_trunc('day'" in query

    @pytest.mark.asyncio
    async def test_get_conversation_volume_by_week(self, mock_db):
        """Test get_conversation_volume grouped by week."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = []

        result = await repo.get_conversation_volume(group_by="week")

        assert len(result) == 0
        query = mock_db.fetch.call_args[0][0]
        assert "date_trunc('week'" in query

    @pytest.mark.asyncio
    async def test_get_conversation_volume_with_filters(self, mock_db):
        """Test get_conversation_volume with filters."""
        repo = MetricsRepository(mock_db)
        start_time = datetime.now(timezone.utc)
        mock_db.fetch.return_value = []

        result = await repo.get_conversation_volume(start_time=start_time, conversation_id="conv-1")

        assert len(result) == 0
        assert start_time in mock_db.fetch.call_args[0][1:]
        assert "conv-1" in mock_db.fetch.call_args[0][1:]

    @pytest.mark.asyncio
    async def test_build_time_filter_start_only(self, mock_db):
        """Test _build_time_filter with only start_time."""
        repo = MetricsRepository(mock_db)
        conditions = []
        params = []
        start_time = datetime.now(timezone.utc)

        param_idx = repo._build_time_filter(start_time, None, conditions, params, 1)

        assert len(conditions) == 1
        assert len(params) == 1
        assert param_idx == 2
        assert start_time in params
        assert ">=" in conditions[0]

    @pytest.mark.asyncio
    async def test_build_time_filter_end_only(self, mock_db):
        """Test _build_time_filter with only end_time."""
        repo = MetricsRepository(mock_db)
        conditions = []
        params = []
        end_time = datetime.now(timezone.utc)

        param_idx = repo._build_time_filter(None, end_time, conditions, params, 1)

        assert len(conditions) == 1
        assert len(params) == 1
        assert param_idx == 2
        assert end_time in params
        assert "<=" in conditions[0]

    @pytest.mark.asyncio
    async def test_build_time_filter_both(self, mock_db):
        """Test _build_time_filter with both start and end time."""
        repo = MetricsRepository(mock_db)
        conditions = []
        params = []
        start_time = datetime.now(timezone.utc)
        end_time = datetime.now(timezone.utc)

        param_idx = repo._build_time_filter(start_time, end_time, conditions, params, 1)

        assert len(conditions) == 2
        assert len(params) == 2
        assert param_idx == 3

    @pytest.mark.asyncio
    async def test_build_time_filter_custom_column(self, mock_db):
        """Test _build_time_filter with custom time column."""
        repo = MetricsRepository(mock_db)
        conditions = []
        params = []
        start_time = datetime.now(timezone.utc)

        repo._build_time_filter(start_time, None, conditions, params, 1, time_column="custom_time")

        assert "custom_time" in conditions[0]

    @pytest.mark.asyncio
    async def test_build_conversation_filter(self, mock_db):
        """Test _build_conversation_filter."""
        repo = MetricsRepository(mock_db)
        conditions = []
        params = []

        param_idx = repo._build_conversation_filter("conv-1", conditions, params, 1)

        assert len(conditions) == 1
        assert len(params) == 1
        assert param_idx == 2
        assert "conv-1" in params
        assert "conversation_id" in conditions[0].lower()

    @pytest.mark.asyncio
    async def test_build_conversation_filter_none(self, mock_db):
        """Test _build_conversation_filter with None."""
        repo = MetricsRepository(mock_db)
        conditions = []
        params = []

        param_idx = repo._build_conversation_filter(None, conditions, params, 1)

        assert len(conditions) == 0
        assert len(params) == 0
        assert param_idx == 1

    @pytest.mark.asyncio
    async def test_get_failure_grouping_column_type(self, mock_db):
        """Test _get_failure_grouping_column with type."""
        repo = MetricsRepository(mock_db)

        result = repo._get_failure_grouping_column("type")

        assert result == "f.failure_type"

    @pytest.mark.asyncio
    async def test_get_failure_grouping_column_severity(self, mock_db):
        """Test _get_failure_grouping_column with severity."""
        repo = MetricsRepository(mock_db)

        result = repo._get_failure_grouping_column("severity")

        assert result == "f.severity"

    @pytest.mark.asyncio
    async def test_get_failure_grouping_column_default(self, mock_db):
        """Test _get_failure_grouping_column with unknown defaults to type."""
        repo = MetricsRepository(mock_db)

        result = repo._get_failure_grouping_column("unknown")

        assert result == "f.failure_type"

    @pytest.mark.asyncio
    async def test_get_failure_total_count(self, mock_db):
        """Test _get_failure_total_count."""
        repo = MetricsRepository(mock_db)
        mock_db.fetchrow.return_value = MockRecord({"total": 25})

        result = await repo._get_failure_total_count("WHERE test = $1", ["value"])

        assert result == 25

    @pytest.mark.asyncio
    async def test_get_failure_total_count_none(self, mock_db):
        """Test _get_failure_total_count when fetchrow returns None."""
        repo = MetricsRepository(mock_db)
        mock_db.fetchrow.return_value = None

        result = await repo._get_failure_total_count("", [])

        assert result == 0

    @pytest.mark.asyncio
    async def test_get_failure_total_count_null_total(self, mock_db):
        """Test _get_failure_total_count when total is None."""
        repo = MetricsRepository(mock_db)
        mock_db.fetchrow.return_value = MockRecord({"total": None})

        result = await repo._get_failure_total_count("", [])

        assert result == 0

    @pytest.mark.asyncio
    async def test_build_trend_filters(self, mock_db):
        """Test _build_trend_filters."""
        repo = MetricsRepository(mock_db)
        conditions = []
        params = []
        start_time = datetime.now(timezone.utc)
        end_time = datetime.now(timezone.utc)

        param_idx = repo._build_trend_filters(
            "conv-1", start_time, end_time, "created_at", conditions, params, 1
        )

        assert len(conditions) == 3  # conversation_id + start_time + end_time
        assert len(params) == 3
        assert param_idx == 4

    @pytest.mark.asyncio
    async def test_build_trend_filters_no_filters(self, mock_db):
        """Test _build_trend_filters with no filters."""
        repo = MetricsRepository(mock_db)
        conditions = []
        params = []

        param_idx = repo._build_trend_filters(None, None, None, "created_at", conditions, params, 1)

        assert len(conditions) == 0
        assert param_idx == 1

    @pytest.mark.asyncio
    async def test_get_trends_latency(self, mock_db):
        """Test get_trends for latency metric."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({"timestamp": "2024-01-01T10:00:00Z", "value": 150.0, "rolling_avg": 145.0}),
        ]

        result = await repo.get_trends(metric="latency", window="1h")

        assert len(result) == 1
        assert result[0]["timestamp"] == "2024-01-01T10:00:00Z"
        assert result[0]["value"] == 150.0
        assert result[0]["rolling_avg"] == 145.0
        query = mock_db.fetch.call_args[0][0]
        assert "duration_ms" in query.lower()

    @pytest.mark.asyncio
    async def test_get_trends_failures(self, mock_db):
        """Test get_trends for failures metric."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({"timestamp": "2024-01-01T10:00:00Z", "value": 5.0, "rolling_avg": 4.5}),
        ]

        result = await repo.get_trends(metric="failures", window="1d")

        assert len(result) == 1
        query = mock_db.fetch.call_args[0][0]
        assert "failures" in query.lower()

    @pytest.mark.asyncio
    async def test_get_trends_conversations(self, mock_db):
        """Test get_trends for conversations metric."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({"timestamp": "2024-01-01T10:00:00Z", "value": 10.0, "rolling_avg": 9.5}),
        ]

        result = await repo.get_trends(metric="conversations", window="1w")

        assert len(result) == 1
        query = mock_db.fetch.call_args[0][0]
        assert "conversations" in query.lower()

    @pytest.mark.asyncio
    async def test_get_trends_with_filters(self, mock_db):
        """Test get_trends with filters."""
        repo = MetricsRepository(mock_db)
        start_time = datetime.now(timezone.utc)
        mock_db.fetch.return_value = []

        result = await repo.get_trends(
            metric="latency", start_time=start_time, conversation_id="conv-1"
        )

        assert len(result) == 0
        assert start_time in mock_db.fetch.call_args[0][1:]

    @pytest.mark.asyncio
    async def test_get_trends_null_values(self, mock_db):
        """Test get_trends handles null values."""
        repo = MetricsRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({"timestamp": "2024-01-01T10:00:00Z", "value": None, "rolling_avg": None}),
        ]

        result = await repo.get_trends(metric="latency")

        assert result[0]["value"] is None
        assert result[0]["rolling_avg"] is None

    @pytest.mark.asyncio
    async def test_build_latency_trend_query(self, mock_db):
        """Test _build_latency_trend_query."""
        repo = MetricsRepository(mock_db)

        query = repo._build_latency_trend_query(
            "date_trunc('hour', s.start_time)",
            'YYYY-MM-DD"T"HH24:00:00"Z"',
            1,
            "WHERE test = $1",
        )

        assert "AVG(s.duration_ms)" in query
        assert "rolling" in query.lower() or "window" in query.lower()
        assert "date_trunc('hour'" in query

    @pytest.mark.asyncio
    async def test_build_failures_trend_query(self, mock_db):
        """Test _build_failures_trend_query."""
        repo = MetricsRepository(mock_db)

        query = repo._build_failures_trend_query(
            "date_trunc('day', f.created_at)",
            'YYYY-MM-DD"T"00:00:00"Z"',
            1,
            "WHERE test = $1",
        )

        assert "COUNT" in query
        assert "failures" in query.lower()
        assert "date_trunc('day'" in query

    @pytest.mark.asyncio
    async def test_build_conversations_trend_query(self, mock_db):
        """Test _build_conversations_trend_query."""
        repo = MetricsRepository(mock_db)

        query = repo._build_conversations_trend_query(
            "date_trunc('week', c.created_at)",
            'YYYY-MM-DD"T"00:00:00"Z"',
            1,
            "WHERE test = $1",
        )

        assert "COUNT" in query
        assert "conversations" in query.lower()
        assert "date_trunc('week'" in query
