"""Tests for the dependencies module."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from voiceobs.server.dependencies import (
    InMemorySpanStoreAdapter,
    PostgresSpanStoreAdapter,
    get_conversation_repository,
    get_failure_repository,
    get_persona_repository,
    get_storage,
    get_turn_repository,
    init_database,
    is_using_postgres,
    reset_dependencies,
    shutdown_database,
)
from voiceobs.server.store import SpanStore


class TestInMemorySpanStoreAdapter:
    """Tests for the InMemorySpanStoreAdapter class."""

    @pytest.fixture
    def mock_store(self):
        """Create a mock SpanStore."""
        store = MagicMock(spec=SpanStore)
        return store

    @pytest.mark.asyncio
    async def test_add_span(self, mock_store):
        """Test add_span delegates to store."""
        adapter = InMemorySpanStoreAdapter(mock_store)
        mock_store.add_span.return_value = uuid4()

        result = await adapter.add_span(
            name="test.span",
            duration_ms=100.0,
            attributes={"key": "value"},
        )

        mock_store.add_span.assert_called_once_with(
            name="test.span",
            start_time=None,
            end_time=None,
            duration_ms=100.0,
            attributes={"key": "value"},
            trace_id=None,
            span_id=None,
            parent_span_id=None,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_span(self, mock_store):
        """Test get_span delegates to store."""
        adapter = InMemorySpanStoreAdapter(mock_store)
        span_id = uuid4()
        mock_store.get_span.return_value = {"id": span_id}

        result = await adapter.get_span(span_id)

        mock_store.get_span.assert_called_once_with(span_id)
        assert result == {"id": span_id}

    @pytest.mark.asyncio
    async def test_get_all_spans(self, mock_store):
        """Test get_all_spans delegates to store."""
        adapter = InMemorySpanStoreAdapter(mock_store)
        mock_store.get_all_spans.return_value = [{"id": uuid4()}]

        result = await adapter.get_all_spans()

        mock_store.get_all_spans.assert_called_once()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_spans_as_dicts(self, mock_store):
        """Test get_spans_as_dicts delegates to store."""
        adapter = InMemorySpanStoreAdapter(mock_store)
        mock_store.get_spans_as_dicts.return_value = [{"name": "test"}]

        result = await adapter.get_spans_as_dicts()

        mock_store.get_spans_as_dicts.assert_called_once()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_clear(self, mock_store):
        """Test clear delegates to store."""
        adapter = InMemorySpanStoreAdapter(mock_store)
        mock_store.clear.return_value = 5

        result = await adapter.clear()

        mock_store.clear.assert_called_once()
        assert result == 5

    @pytest.mark.asyncio
    async def test_count(self, mock_store):
        """Test count delegates to store."""
        adapter = InMemorySpanStoreAdapter(mock_store)
        mock_store.count.return_value = 10

        result = await adapter.count()

        mock_store.count.assert_called_once()
        assert result == 10


class TestPostgresSpanStoreAdapter:
    """Tests for the PostgresSpanStoreAdapter class."""

    @pytest.fixture
    def mock_span_repo(self):
        """Create a mock SpanRepository."""
        return AsyncMock()

    @pytest.fixture
    def mock_conversation_repo(self):
        """Create a mock ConversationRepository."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_add_span_without_conversation(self, mock_span_repo, mock_conversation_repo):
        """Test add_span without conversation ID."""
        adapter = PostgresSpanStoreAdapter(
            span_repo=mock_span_repo,
            conversation_repo=mock_conversation_repo,
        )
        span_id = uuid4()
        mock_span_repo.add.return_value = span_id

        result = await adapter.add_span(
            name="test.span",
            duration_ms=100.0,
            attributes={},
        )

        mock_conversation_repo.get_or_create.assert_not_called()
        mock_span_repo.add.assert_called_once()
        assert result == span_id

    @pytest.mark.asyncio
    async def test_add_span_with_conversation(self, mock_span_repo, mock_conversation_repo):
        """Test add_span with conversation ID."""
        adapter = PostgresSpanStoreAdapter(
            span_repo=mock_span_repo,
            conversation_repo=mock_conversation_repo,
        )
        span_id = uuid4()
        conv_id = uuid4()
        mock_span_repo.add.return_value = span_id
        mock_conversation_repo.get_or_create.return_value = MagicMock(id=conv_id)

        result = await adapter.add_span(
            name="test.span",
            duration_ms=100.0,
            attributes={"voice.conversation.id": "conv-123"},
        )

        mock_conversation_repo.get_or_create.assert_called_once_with("conv-123")
        mock_span_repo.add.assert_called_once()
        assert result == span_id

    @pytest.mark.asyncio
    async def test_get_span(self, mock_span_repo, mock_conversation_repo):
        """Test get_span delegates to repository."""
        adapter = PostgresSpanStoreAdapter(
            span_repo=mock_span_repo,
            conversation_repo=mock_conversation_repo,
        )
        span_id = uuid4()
        mock_span_repo.get.return_value = {"id": span_id}

        result = await adapter.get_span(span_id)

        mock_span_repo.get.assert_called_once_with(span_id)
        assert result == {"id": span_id}

    @pytest.mark.asyncio
    async def test_get_all_spans(self, mock_span_repo, mock_conversation_repo):
        """Test get_all_spans delegates to repository."""
        adapter = PostgresSpanStoreAdapter(
            span_repo=mock_span_repo,
            conversation_repo=mock_conversation_repo,
        )
        mock_span_repo.get_all.return_value = [{"id": uuid4()}]

        result = await adapter.get_all_spans()

        mock_span_repo.get_all.assert_called_once()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_spans_as_dicts(self, mock_span_repo, mock_conversation_repo):
        """Test get_spans_as_dicts delegates to repository."""
        adapter = PostgresSpanStoreAdapter(
            span_repo=mock_span_repo,
            conversation_repo=mock_conversation_repo,
        )
        mock_span_repo.get_as_dicts.return_value = [{"name": "test"}]

        result = await adapter.get_spans_as_dicts()

        mock_span_repo.get_as_dicts.assert_called_once()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_clear(self, mock_span_repo, mock_conversation_repo):
        """Test clear delegates to repository."""
        adapter = PostgresSpanStoreAdapter(
            span_repo=mock_span_repo,
            conversation_repo=mock_conversation_repo,
        )
        mock_span_repo.clear.return_value = 5

        result = await adapter.clear()

        mock_span_repo.clear.assert_called_once()
        assert result == 5

    @pytest.mark.asyncio
    async def test_count(self, mock_span_repo, mock_conversation_repo):
        """Test count delegates to repository."""
        adapter = PostgresSpanStoreAdapter(
            span_repo=mock_span_repo,
            conversation_repo=mock_conversation_repo,
        )
        mock_span_repo.count.return_value = 10

        result = await adapter.count()

        mock_span_repo.count.assert_called_once()
        assert result == 10


class TestDependencyFunctions:
    """Tests for the dependency management functions."""

    def teardown_method(self):
        """Reset dependencies after each test."""
        reset_dependencies()

    @pytest.mark.asyncio
    async def test_init_database_without_url(self):
        """Test init_database uses in-memory when no URL configured."""
        # Ensure no URL is set
        with patch.dict("os.environ", {}, clear=True):
            with patch("voiceobs.server.dependencies._get_database_url", return_value=None):
                await init_database()

        assert not is_using_postgres()
        storage = get_storage()
        assert isinstance(storage, InMemorySpanStoreAdapter)

    @pytest.mark.asyncio
    async def test_init_database_with_url(self):
        """Test init_database uses PostgreSQL when URL configured."""
        mock_db = AsyncMock()
        mock_db.connect = AsyncMock()
        mock_db.init_schema = AsyncMock()

        mock_settings = MagicMock()
        mock_settings.livekit_url = "wss://test.livekit.cloud"
        mock_settings.livekit_api_key = "test_key"
        mock_settings.livekit_api_secret = "test_secret"
        mock_settings.sip_outbound_trunk_id = "trunk_123"

        with patch(
            "voiceobs.server.dependencies._get_database_url",
            return_value="postgresql://test:test@localhost/test",
        ):
            with patch("voiceobs.server.dependencies.Database", return_value=mock_db):
                with patch(
                    "voiceobs.server.services.agent_verification.service.get_verification_settings",
                    return_value=mock_settings,
                ):
                    await init_database()

        assert is_using_postgres()
        mock_db.connect.assert_called_once()
        mock_db.init_schema.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_database(self):
        """Test shutdown_database clears state."""
        # First init with postgres
        mock_db = AsyncMock()
        mock_db.connect = AsyncMock()
        mock_db.init_schema = AsyncMock()
        mock_db.disconnect = AsyncMock()

        mock_settings = MagicMock()
        mock_settings.livekit_url = "wss://test.livekit.cloud"
        mock_settings.livekit_api_key = "test_key"
        mock_settings.livekit_api_secret = "test_secret"
        mock_settings.sip_outbound_trunk_id = "trunk_123"

        with patch(
            "voiceobs.server.dependencies._get_database_url",
            return_value="postgresql://test:test@localhost/test",
        ):
            with patch("voiceobs.server.dependencies.Database", return_value=mock_db):
                with patch(
                    "voiceobs.server.services.agent_verification.service.get_verification_settings",
                    return_value=mock_settings,
                ):
                    await init_database()

        assert is_using_postgres()

        await shutdown_database()

        assert not is_using_postgres()
        mock_db.disconnect.assert_called_once()

    def test_get_storage_fallback(self):
        """Test get_storage falls back to in-memory when not initialized."""
        reset_dependencies()
        storage = get_storage()
        assert isinstance(storage, InMemorySpanStoreAdapter)

    def test_get_conversation_repository_none_for_in_memory(self):
        """Test get_conversation_repository returns None for in-memory."""
        reset_dependencies()
        repo = get_conversation_repository()
        assert repo is None

    def test_get_turn_repository_none_for_in_memory(self):
        """Test get_turn_repository returns None for in-memory."""
        reset_dependencies()
        repo = get_turn_repository()
        assert repo is None

    def test_get_failure_repository_none_for_in_memory(self):
        """Test get_failure_repository returns None for in-memory."""
        reset_dependencies()
        repo = get_failure_repository()
        assert repo is None

    def test_get_persona_repository_none_for_in_memory(self):
        """Test get_persona_repository returns None for in-memory."""
        reset_dependencies()
        repo = get_persona_repository()
        assert repo is None

    def test_reset_dependencies(self):
        """Test reset_dependencies clears all state."""
        reset_dependencies()
        assert not is_using_postgres()
        assert get_conversation_repository() is None
        assert get_persona_repository() is None


class TestGetDatabaseUrl:
    """Tests for the _get_database_url function."""

    def test_returns_env_var_if_set(self):
        """Test returns env var when set."""
        with patch.dict("os.environ", {"VOICEOBS_DATABASE_URL": "postgresql://env/db"}):
            from voiceobs.server.dependencies import _get_database_url

            url = _get_database_url()
            assert url == "postgresql://env/db"

    def test_returns_config_if_no_env_var(self):
        """Test returns config value when env var not set."""
        mock_config = MagicMock()
        mock_config.server.database_url = "postgresql://config/db"

        with patch.dict("os.environ", {}, clear=True):
            with patch("voiceobs.config.get_config", return_value=mock_config):
                from voiceobs.server.dependencies import _get_database_url

                url = _get_database_url()
                assert url == "postgresql://config/db"

    def test_returns_none_if_config_fails(self):
        """Test returns None when config fails to load."""
        with patch.dict("os.environ", {}, clear=True):
            with patch(
                "voiceobs.config.get_config",
                side_effect=Exception("Config error"),
            ):
                from voiceobs.server.dependencies import _get_database_url

                url = _get_database_url()
                assert url is None
