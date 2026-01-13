"""Additional tests for ConversationRepository search functionality."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from voiceobs.server.db.repositories.conversation import ConversationRepository

from .conftest import MockRecord


class TestConversationRepositorySearch:
    """Tests for ConversationRepository search functionality."""

    @pytest.mark.asyncio
    async def test_search_no_filters(self, mock_db):
        """Test search with no filters returns all conversations."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": uuid4(),
                    "conversation_id": "conv-1",
                    "span_count": 5,
                    "turn_count": 3,
                    "has_failures": False,
                }
            )
        ]
        mock_db.fetchval.return_value = 1

        results, total = await repo.search()

        assert len(results) == 1
        assert total == 1
        assert results[0]["id"] == "conv-1"

    @pytest.mark.asyncio
    async def test_search_with_query(self, mock_db):
        """Test search with query parameter."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(query="test query")

        assert len(results) == 0
        assert total == 0
        # Verify query condition was added
        query = mock_db.fetch.call_args[0][0]
        assert "ILIKE" in query or "plainto_tsquery" in query

    @pytest.mark.asyncio
    async def test_search_with_start_time(self, mock_db):
        """Test search with start_time filter."""
        repo = ConversationRepository(mock_db)
        start_time = datetime.now(timezone.utc)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(start_time=start_time)

        assert len(results) == 0
        query = mock_db.fetch.call_args[0][0]
        assert "start_time" in query.lower()
        assert start_time in mock_db.fetch.call_args[0][1:]

    @pytest.mark.asyncio
    async def test_search_with_end_time(self, mock_db):
        """Test search with end_time filter."""
        repo = ConversationRepository(mock_db)
        end_time = datetime.now(timezone.utc)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(end_time=end_time)

        assert len(results) == 0
        assert end_time in mock_db.fetch.call_args[0][1:]

    @pytest.mark.asyncio
    async def test_search_with_actor(self, mock_db):
        """Test search with actor filter."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(actor="user")

        assert len(results) == 0
        query = mock_db.fetch.call_args[0][0]
        assert "actor" in query.lower()
        assert "user" in mock_db.fetch.call_args[0][1:]

    @pytest.mark.asyncio
    async def test_search_with_has_failures_true(self, mock_db):
        """Test search with has_failures=True."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(has_failures=True)

        assert len(results) == 0
        query = mock_db.fetch.call_args[0][0]
        assert "EXISTS" in query
        assert "failures" in query.lower()

    @pytest.mark.asyncio
    async def test_search_with_has_failures_false(self, mock_db):
        """Test search with has_failures=False."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(has_failures=False)

        assert len(results) == 0
        query = mock_db.fetch.call_args[0][0]
        assert "NOT EXISTS" in query
        assert "failures" in query.lower()

    @pytest.mark.asyncio
    async def test_search_with_failure_type(self, mock_db):
        """Test search with failure_type filter."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(failure_type="timeout")

        assert len(results) == 0
        query = mock_db.fetch.call_args[0][0]
        assert "failure_type" in query.lower()
        assert "timeout" in mock_db.fetch.call_args[0][1:]

    @pytest.mark.asyncio
    async def test_search_with_min_latency(self, mock_db):
        """Test search with min_latency_ms filter."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(min_latency_ms=100.5)

        assert len(results) == 0
        query = mock_db.fetch.call_args[0][0]
        assert "duration_ms" in query.lower()
        assert 100.5 in mock_db.fetch.call_args[0][1:]

    @pytest.mark.asyncio
    async def test_search_with_multiple_filters(self, mock_db):
        """Test search with multiple filters."""
        repo = ConversationRepository(mock_db)
        start_time = datetime.now(timezone.utc)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(
            query="test",
            start_time=start_time,
            actor="agent",
            has_failures=True,
            min_latency_ms=50.0,
        )

        assert len(results) == 0
        query = mock_db.fetch.call_args[0][0]
        # Should have multiple conditions
        assert query.count("AND") >= 3

    @pytest.mark.asyncio
    async def test_search_sort_by_start_time(self, mock_db):
        """Test search sorted by start_time."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(sort="start_time", sort_order="asc")

        assert len(results) == 0
        query = mock_db.fetch.call_args[0][0]
        assert "MIN(span_times.start_time)" in query
        assert "ASC" in query

    @pytest.mark.asyncio
    async def test_search_sort_by_latency(self, mock_db):
        """Test search sorted by latency."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(sort="latency", sort_order="desc")

        assert len(results) == 0
        query = mock_db.fetch.call_args[0][0]
        assert "AVG(span_times.duration_ms)" in query
        assert "DESC" in query

    @pytest.mark.asyncio
    async def test_search_sort_by_relevance(self, mock_db):
        """Test search sorted by relevance."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(sort="relevance", query="test query")

        assert len(results) == 0
        query = mock_db.fetch.call_args[0][0]
        assert "ts_rank" in query or "tsvector" in query.lower()

    @pytest.mark.asyncio
    async def test_search_sort_by_default(self, mock_db):
        """Test search with default sort (created_at)."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 0

        results, total = await repo.search(sort="unknown")

        assert len(results) == 0
        query = mock_db.fetch.call_args[0][0]
        assert "c.created_at" in query

    @pytest.mark.asyncio
    async def test_search_with_limit_and_offset(self, mock_db):
        """Test search with pagination."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 10

        results, total = await repo.search(limit=20, offset=10)

        assert len(results) == 0
        assert total == 10
        # Verify LIMIT and OFFSET are in query
        query = mock_db.fetch.call_args[0][0]
        assert "LIMIT" in query
        assert "OFFSET" in query
        # Verify limit and offset values are passed
        assert 20 in mock_db.fetch.call_args[0][1:]
        assert 10 in mock_db.fetch.call_args[0][1:]

    @pytest.mark.asyncio
    async def test_search_returns_formatted_results(self, mock_db):
        """Test search returns properly formatted results."""
        repo = ConversationRepository(mock_db)
        conv_id = uuid4()
        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": conv_id,
                    "conversation_id": "conv-1",
                    "span_count": 5,
                    "turn_count": 3,
                    "has_failures": True,
                }
            )
        ]
        mock_db.fetchval.return_value = 1

        results, total = await repo.search()

        assert len(results) == 1
        assert results[0]["id"] == "conv-1"
        assert results[0]["span_count"] == 5
        assert results[0]["turn_count"] == 3
        assert results[0]["has_failures"] is True

    @pytest.mark.asyncio
    async def test_search_count_query_excludes_limit_offset(self, mock_db):
        """Test that count query doesn't include LIMIT/OFFSET."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = 5

        results, total = await repo.search(limit=10, offset=5)

        assert total == 5
        # Verify fetchval was called with count query (no LIMIT/OFFSET)
        count_query = mock_db.fetchval.call_args[0][0]
        assert "LIMIT" not in count_query
        assert "OFFSET" not in count_query

    @pytest.mark.asyncio
    async def test_search_count_zero_when_none(self, mock_db):
        """Test search returns 0 when count is None."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = []
        mock_db.fetchval.return_value = None

        results, total = await repo.search()

        assert total == 0

    @pytest.mark.asyncio
    async def test_build_search_conditions_all_filters(self, mock_db):
        """Test _build_search_conditions with all filters."""
        repo = ConversationRepository(mock_db)
        start_time = datetime.now(timezone.utc)
        end_time = datetime.now(timezone.utc)

        conditions, params, param_idx = repo._build_search_conditions(
            query="test",
            start_time=start_time,
            end_time=end_time,
            actor="user",
            has_failures=True,
            failure_type="error",
            min_latency_ms=100.0,
        )

        # Query adds 1 condition (but uses 2 params), others add 1 each
        # Total: query(1) + start_time(1) + end_time(1) + actor(1) +
        # has_failures(1) + failure_type(1) + min_latency(1) = 7
        assert len(conditions) == 7  # All 7 conditions should be added
        assert len(params) > 0
        assert param_idx > 1

    @pytest.mark.asyncio
    async def test_build_search_conditions_no_filters(self, mock_db):
        """Test _build_search_conditions with no filters."""
        repo = ConversationRepository(mock_db)

        conditions, params, param_idx = repo._build_search_conditions(
            query=None,
            start_time=None,
            end_time=None,
            actor=None,
            has_failures=None,
            failure_type=None,
            min_latency_ms=None,
        )

        assert len(conditions) == 0
        assert len(params) == 0
        assert param_idx == 1

    @pytest.mark.asyncio
    async def test_add_query_condition(self, mock_db):
        """Test _add_query_condition helper."""
        repo = ConversationRepository(mock_db)
        conditions = []
        params = []

        param_idx = repo._add_query_condition("test query", conditions, params, 1)

        assert len(conditions) == 1
        assert len(params) == 2  # ILIKE param and tsquery param
        assert param_idx == 3
        assert "%test query%" in params
        assert "test query" in params

    @pytest.mark.asyncio
    async def test_add_start_time_condition(self, mock_db):
        """Test _add_start_time_condition helper."""
        repo = ConversationRepository(mock_db)
        conditions = []
        params = []
        start_time = datetime.now(timezone.utc)

        param_idx = repo._add_start_time_condition(start_time, conditions, params, 1)

        assert len(conditions) == 1
        assert len(params) == 1
        assert param_idx == 2
        assert start_time in params
        assert "start_time" in conditions[0].lower()

    @pytest.mark.asyncio
    async def test_add_end_time_condition(self, mock_db):
        """Test _add_end_time_condition helper."""
        repo = ConversationRepository(mock_db)
        conditions = []
        params = []
        end_time = datetime.now(timezone.utc)

        param_idx = repo._add_end_time_condition(end_time, conditions, params, 1)

        assert len(conditions) == 1
        assert len(params) == 1
        assert param_idx == 2
        assert end_time in params

    @pytest.mark.asyncio
    async def test_add_actor_condition(self, mock_db):
        """Test _add_actor_condition helper."""
        repo = ConversationRepository(mock_db)
        conditions = []
        params = []

        param_idx = repo._add_actor_condition("agent", conditions, params, 1)

        assert len(conditions) == 1
        assert len(params) == 1
        assert param_idx == 2
        assert "agent" in params
        assert "actor" in conditions[0].lower()

    @pytest.mark.asyncio
    async def test_add_has_failures_condition_true(self, mock_db):
        """Test _add_has_failures_condition with True."""
        repo = ConversationRepository(mock_db)
        conditions = []

        repo._add_has_failures_condition(True, conditions)

        assert len(conditions) == 1
        assert "EXISTS" in conditions[0]
        assert "NOT EXISTS" not in conditions[0]

    @pytest.mark.asyncio
    async def test_add_has_failures_condition_false(self, mock_db):
        """Test _add_has_failures_condition with False."""
        repo = ConversationRepository(mock_db)
        conditions = []

        repo._add_has_failures_condition(False, conditions)

        assert len(conditions) == 1
        assert "NOT EXISTS" in conditions[0]

    @pytest.mark.asyncio
    async def test_add_failure_type_condition(self, mock_db):
        """Test _add_failure_type_condition helper."""
        repo = ConversationRepository(mock_db)
        conditions = []
        params = []

        param_idx = repo._add_failure_type_condition("timeout", conditions, params, 1)

        assert len(conditions) == 1
        assert len(params) == 1
        assert param_idx == 2
        assert "timeout" in params
        assert "failure_type" in conditions[0].lower()

    @pytest.mark.asyncio
    async def test_add_min_latency_condition(self, mock_db):
        """Test _add_min_latency_condition helper."""
        repo = ConversationRepository(mock_db)
        conditions = []
        params = []

        param_idx = repo._add_min_latency_condition(100.5, conditions, params, 1)

        assert len(conditions) == 1
        assert len(params) == 1
        assert param_idx == 2
        assert 100.5 in params
        assert "duration_ms" in conditions[0].lower()

    @pytest.mark.asyncio
    async def test_build_order_by_start_time(self, mock_db):
        """Test _build_order_by with start_time sort."""
        repo = ConversationRepository(mock_db)

        order_by = repo._build_order_by("start_time", "asc", None, None)

        assert "MIN(span_times.start_time)" in order_by
        assert "ASC" in order_by

    @pytest.mark.asyncio
    async def test_build_order_by_latency(self, mock_db):
        """Test _build_order_by with latency sort."""
        repo = ConversationRepository(mock_db)

        order_by = repo._build_order_by("latency", "desc", None, None)

        assert "AVG(span_times.duration_ms)" in order_by
        assert "DESC" in order_by

    @pytest.mark.asyncio
    async def test_build_order_by_relevance(self, mock_db):
        """Test _build_order_by with relevance sort."""
        repo = ConversationRepository(mock_db)

        order_by = repo._build_order_by("relevance", "desc", "test query", 2)

        assert "ts_rank" in order_by or "tsvector" in order_by.lower()
        assert "DESC" in order_by

    @pytest.mark.asyncio
    async def test_build_order_by_relevance_no_query(self, mock_db):
        """Test _build_order_by with relevance but no query falls back to created_at."""
        repo = ConversationRepository(mock_db)

        order_by = repo._build_order_by("relevance", "desc", None, None)

        assert "c.created_at" in order_by

    @pytest.mark.asyncio
    async def test_build_order_by_default(self, mock_db):
        """Test _build_order_by with unknown sort falls back to created_at."""
        repo = ConversationRepository(mock_db)

        order_by = repo._build_order_by("unknown", "asc", None, None)

        assert "c.created_at" in order_by
        assert "ASC" in order_by
