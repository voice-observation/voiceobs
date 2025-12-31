"""Tests for the database connection module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voiceobs.server.db.connection import (
    DEFAULT_DATABASE_URL,
    Database,
    get_database,
    reset_database,
)

ASYNCPG_CREATE_POOL = "voiceobs.server.db.connection.asyncpg.create_pool"


class TestDatabase:
    """Tests for the Database class."""

    def test_init_default_url(self):
        """Test default database URL is used."""
        db = Database()
        assert db._database_url == DEFAULT_DATABASE_URL

    def test_init_custom_url(self):
        """Test custom database URL is used."""
        custom_url = "postgresql://custom:password@localhost:5432/testdb"
        db = Database(database_url=custom_url)
        assert db._database_url == custom_url

    def test_init_from_env_var(self):
        """Test database URL from environment variable."""
        env = {"VOICEOBS_DATABASE_URL": "postgresql://env:var@host/db"}
        with patch.dict("os.environ", env):
            db = Database()
            assert db._database_url == "postgresql://env:var@host/db"

    def test_init_pool_sizes(self):
        """Test pool size configuration."""
        db = Database(min_pool_size=5, max_pool_size=20)
        assert db._min_pool_size == 5
        assert db._max_pool_size == 20

    def test_is_connected_false_initially(self):
        """Test is_connected is False before connecting."""
        db = Database()
        assert db.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_creates_pool(self):
        """Test connect creates a connection pool."""
        db = Database()
        mock_pool = MagicMock()

        with patch(ASYNCPG_CREATE_POOL, new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_pool

            await db.connect()

            mock_create.assert_called_once_with(
                db._database_url,
                min_size=db._min_pool_size,
                max_size=db._max_pool_size,
            )
            assert db.is_connected is True
            assert db._pool == mock_pool

    @pytest.mark.asyncio
    async def test_connect_idempotent(self):
        """Test calling connect multiple times is safe."""
        db = Database()
        mock_pool = MagicMock()

        with patch(ASYNCPG_CREATE_POOL, new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_pool

            await db.connect()
            await db.connect()  # Second call should be no-op

            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_closes_pool(self):
        """Test disconnect closes the connection pool."""
        db = Database()
        mock_pool = AsyncMock()

        with patch(ASYNCPG_CREATE_POOL, new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_pool

            await db.connect()
            await db.disconnect()

            mock_pool.close.assert_called_once()
            assert db.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_without_connect(self):
        """Test disconnect without connect is safe."""
        db = Database()
        await db.disconnect()  # Should not raise
        assert db.is_connected is False

    @pytest.mark.asyncio
    async def test_execute_requires_connection(self):
        """Test execute raises error if not connected."""
        db = Database()

        with pytest.raises(RuntimeError, match="Database not connected"):
            await db.execute("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_delegates_to_pool(self):
        """Test execute calls pool.execute."""
        db = Database()
        mock_pool = AsyncMock()
        mock_pool.execute.return_value = "INSERT 0 1"

        with patch(ASYNCPG_CREATE_POOL, new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_pool

            await db.connect()
            result = await db.execute("INSERT INTO test VALUES ($1)", "value")

            mock_pool.execute.assert_called_once_with("INSERT INTO test VALUES ($1)", "value")
            assert result == "INSERT 0 1"

    @pytest.mark.asyncio
    async def test_fetch_requires_connection(self):
        """Test fetch raises error if not connected."""
        db = Database()

        with pytest.raises(RuntimeError, match="Database not connected"):
            await db.fetch("SELECT * FROM test")

    @pytest.mark.asyncio
    async def test_fetch_delegates_to_pool(self):
        """Test fetch calls pool.fetch."""
        db = Database()
        mock_pool = AsyncMock()
        mock_rows = [{"id": 1}, {"id": 2}]
        mock_pool.fetch.return_value = mock_rows

        with patch(ASYNCPG_CREATE_POOL, new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_pool

            await db.connect()
            result = await db.fetch("SELECT * FROM test WHERE id = $1", 1)

            mock_pool.fetch.assert_called_once_with("SELECT * FROM test WHERE id = $1", 1)
            assert result == mock_rows

    @pytest.mark.asyncio
    async def test_fetchrow_requires_connection(self):
        """Test fetchrow raises error if not connected."""
        db = Database()

        with pytest.raises(RuntimeError, match="Database not connected"):
            await db.fetchrow("SELECT * FROM test WHERE id = 1")

    @pytest.mark.asyncio
    async def test_fetchrow_delegates_to_pool(self):
        """Test fetchrow calls pool.fetchrow."""
        db = Database()
        mock_pool = AsyncMock()
        mock_row = {"id": 1, "name": "test"}
        mock_pool.fetchrow.return_value = mock_row

        with patch(ASYNCPG_CREATE_POOL, new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_pool

            await db.connect()
            result = await db.fetchrow("SELECT * FROM test WHERE id = $1", 1)

            mock_pool.fetchrow.assert_called_once_with("SELECT * FROM test WHERE id = $1", 1)
            assert result == mock_row

    @pytest.mark.asyncio
    async def test_fetchval_requires_connection(self):
        """Test fetchval raises error if not connected."""
        db = Database()

        with pytest.raises(RuntimeError, match="Database not connected"):
            await db.fetchval("SELECT COUNT(*) FROM test")

    @pytest.mark.asyncio
    async def test_fetchval_delegates_to_pool(self):
        """Test fetchval calls pool.fetchval."""
        db = Database()
        mock_pool = AsyncMock()
        mock_pool.fetchval.return_value = 42

        with patch(ASYNCPG_CREATE_POOL, new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_pool

            await db.connect()
            result = await db.fetchval("SELECT COUNT(*) FROM test")

            mock_pool.fetchval.assert_called_once_with("SELECT COUNT(*) FROM test")
            assert result == 42

    @pytest.mark.asyncio
    async def test_init_schema_requires_connection(self):
        """Test init_schema raises error if not connected."""
        db = Database()

        with pytest.raises(RuntimeError, match="Database not connected"):
            await db.init_schema()

    @pytest.mark.asyncio
    async def test_init_schema_executes_sql(self):
        """Test init_schema executes the schema SQL."""
        db = Database()
        mock_pool = AsyncMock()

        with patch(ASYNCPG_CREATE_POOL, new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_pool

            await db.connect()
            await db.init_schema()

            # Verify execute was called with some SQL containing CREATE TABLE
            call_args = mock_pool.execute.call_args[0][0]
            assert "CREATE TABLE IF NOT EXISTS" in call_args


class TestGetDatabase:
    """Tests for the get_database function."""

    def teardown_method(self):
        """Reset database after each test."""
        reset_database()

    def test_get_database_returns_singleton(self):
        """Test get_database returns the same instance."""
        db1 = get_database()
        db2 = get_database()
        assert db1 is db2

    def test_reset_database_clears_singleton(self):
        """Test reset_database clears the singleton."""
        db1 = get_database()
        reset_database()
        db2 = get_database()
        assert db1 is not db2
