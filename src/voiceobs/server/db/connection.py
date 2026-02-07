"""Database connection management for voiceobs server.

This module provides async database connection pooling using asyncpg.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import asyncpg

# Default database URL for local development
DEFAULT_DATABASE_URL = "postgresql://voiceobs:voiceobs@localhost:5432/voiceobs"


class Database:
    """Async database connection manager with connection pooling.

    This class manages a connection pool to PostgreSQL and provides
    methods for executing queries and managing transactions.
    """

    def __init__(
        self,
        database_url: str | None = None,
        min_pool_size: int = 2,
        max_pool_size: int = 10,
    ) -> None:
        """Initialize the database manager.

        Args:
            database_url: PostgreSQL connection URL.
            min_pool_size: Minimum number of connections in the pool.
            max_pool_size: Maximum number of connections in the pool.
        """
        self._database_url = database_url or os.environ.get(
            "VOICEOBS_DATABASE_URL", DEFAULT_DATABASE_URL
        )
        self._min_pool_size = min_pool_size
        self._max_pool_size = max_pool_size
        self._pool: asyncpg.Pool | None = None

    @property
    def is_connected(self) -> bool:
        """Check if the database is connected."""
        return self._pool is not None

    async def connect(self) -> None:
        """Connect to the database and create the connection pool.

        Raises:
            asyncpg.PostgresError: If connection fails.
        """
        if self._pool is not None:
            return

        self._pool = await asyncpg.create_pool(
            self._database_url,
            min_size=self._min_pool_size,
            max_size=self._max_pool_size,
        )

    async def disconnect(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def execute(self, query: str, *args: Any) -> str:
        """Execute a query that doesn't return rows.

        Args:
            query: SQL query to execute.
            *args: Query parameters.

        Returns:
            Status string from the query.

        Raises:
            RuntimeError: If not connected to the database.
        """
        if self._pool is None:
            raise RuntimeError("Database not connected")
        return await self._pool.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        """Execute a query and return all rows.

        Args:
            query: SQL query to execute.
            *args: Query parameters.

        Returns:
            List of records.

        Raises:
            RuntimeError: If not connected to the database.
        """
        if self._pool is None:
            raise RuntimeError("Database not connected")
        return await self._pool.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None:
        """Execute a query and return a single row.

        Args:
            query: SQL query to execute.
            *args: Query parameters.

        Returns:
            Single record or None.

        Raises:
            RuntimeError: If not connected to the database.
        """
        if self._pool is None:
            raise RuntimeError("Database not connected")
        return await self._pool.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        """Execute a query and return a single value.

        Args:
            query: SQL query to execute.
            *args: Query parameters.

        Returns:
            Single value.

        Raises:
            RuntimeError: If not connected to the database.
        """
        if self._pool is None:
            raise RuntimeError("Database not connected")
        return await self._pool.fetchval(query, *args)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        """Start a database transaction.

        Yields a connection with an active transaction that will be
        committed on successful exit or rolled back on exception.

        Yields:
            Connection with active transaction.

        Raises:
            RuntimeError: If not connected to the database.
        """
        if self._pool is None:
            raise RuntimeError("Database not connected")

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def init_schema(self) -> None:
        """Initialize the database schema.

        Reads and executes the schema.sql file to create tables.
        """
        # Get the schema file path
        schema_path = Path(__file__).parent / "schema.sql"
        schema_sql = schema_path.read_text()

        if self._pool is None:
            raise RuntimeError("Database not connected")

        await self._pool.execute(schema_sql)


# Global database instance
_database: Database | None = None


def get_database() -> Database:
    """Get the global database instance.

    Returns:
        The database singleton.
    """
    global _database
    if _database is None:
        _database = Database()
    return _database


def reset_database() -> None:
    """Reset the global database instance (for testing)."""
    global _database
    _database = None
