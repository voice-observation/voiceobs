"""FastAPI dependencies for voiceobs server.

This module provides dependency injection for database connections
and repositories, supporting both in-memory and PostgreSQL storage.

Storage Adapters
----------------
The API routes need an async interface for storage operations because FastAPI
is async-first. However, we support two storage backends:

1. **In-memory storage** (`SpanStore`): Synchronous, used for development/testing
2. **PostgreSQL storage** (via repositories): Natively async

To provide a uniform async interface to the routes, we use the Adapter pattern:

- `InMemorySpanStoreAdapter`: Wraps the sync `SpanStore` with async methods
- `PostgresSpanStoreAdapter`: Wraps the async `SpanRepository` and adds
  conversation linking logic

Why only span adapters?
-----------------------
Spans are the **primary ingestion point** for the API. All routes that ingest
or query data work with spans. Conversations, turns, and failures are either:
- Derived from span attributes at query time (in-memory mode)
- Stored separately but populated from spans (PostgreSQL mode)

The individual repositories (ConversationRepository, TurnRepository,
FailureRepository) are exposed directly for PostgreSQL mode when needed
for advanced queries, but are not required for basic API operations.
"""

from __future__ import annotations

import os
from typing import Any, Protocol

from voiceobs.server.db.connection import Database
from voiceobs.server.db.repositories import (
    ConversationRepository,
    FailureRepository,
    MetricsRepository,
    SpanRepository,
    TurnRepository,
)
from voiceobs.server.store import SpanStore, get_span_store


class SpanStorageProtocol(Protocol):
    """Protocol defining the async interface for span storage.

    This protocol allows API routes to work with either in-memory or
    PostgreSQL storage without knowing which backend is being used.
    """

    async def add_span(
        self,
        name: str,
        start_time: str | None = None,
        end_time: str | None = None,
        duration_ms: float | None = None,
        attributes: dict[str, Any] | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> Any:
        """Add a span to storage."""
        ...

    async def get_span(self, span_id: Any) -> Any:
        """Get a span by ID."""
        ...

    async def get_all_spans(self) -> list[Any]:
        """Get all spans."""
        ...

    async def get_spans_as_dicts(self) -> list[dict[str, Any]]:
        """Get spans as dictionaries for analysis."""
        ...

    async def clear(self) -> int:
        """Clear all spans."""
        ...

    async def count(self) -> int:
        """Count all spans."""
        ...


class InMemorySpanStoreAdapter:
    """Adapter that wraps the synchronous SpanStore with async methods.

    This allows the in-memory store to be used with async API routes.
    The underlying operations are still synchronous but wrapped in async
    methods for interface compatibility.
    """

    def __init__(self, store: SpanStore) -> None:
        """Initialize the adapter.

        Args:
            store: The underlying synchronous SpanStore.
        """
        self._store = store

    async def add_span(
        self,
        name: str,
        start_time: str | None = None,
        end_time: str | None = None,
        duration_ms: float | None = None,
        attributes: dict[str, Any] | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> Any:
        """Add a span to storage."""
        return self._store.add_span(
            name=name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            attributes=attributes,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
        )

    async def get_span(self, span_id: Any) -> Any:
        """Get a span by ID."""
        return self._store.get_span(span_id)

    async def get_all_spans(self) -> list[Any]:
        """Get all spans."""
        return self._store.get_all_spans()

    async def get_spans_as_dicts(self) -> list[dict[str, Any]]:
        """Get spans as dictionaries for analysis."""
        return self._store.get_spans_as_dicts()

    async def clear(self) -> int:
        """Clear all spans."""
        return self._store.clear()

    async def count(self) -> int:
        """Count all spans."""
        return self._store.count()


class PostgresSpanStoreAdapter:
    """Adapter that wraps PostgreSQL repositories with conversation linking.

    This adapter provides the same interface as InMemorySpanStoreAdapter but
    uses PostgreSQL repositories. It also handles automatic conversation
    creation when spans contain a `voice.conversation.id` attribute.
    """

    def __init__(
        self,
        span_repo: SpanRepository,
        conversation_repo: ConversationRepository,
    ) -> None:
        """Initialize the adapter.

        Args:
            span_repo: Repository for span operations.
            conversation_repo: Repository for conversation operations.
        """
        self._span_repo = span_repo
        self._conversation_repo = conversation_repo

    async def add_span(
        self,
        name: str,
        start_time: str | None = None,
        end_time: str | None = None,
        duration_ms: float | None = None,
        attributes: dict[str, Any] | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> Any:
        """Add a span to storage.

        If the span has a `voice.conversation.id` attribute, automatically
        creates or links to the corresponding conversation record.
        """
        attrs = attributes or {}
        conversation_id = None

        # Auto-create conversation if span has conversation ID attribute
        conv_external_id = attrs.get("voice.conversation.id")
        if conv_external_id:
            conversation = await self._conversation_repo.get_or_create(conv_external_id)
            conversation_id = conversation.id

        return await self._span_repo.add(
            name=name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            attributes=attrs,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            conversation_id=conversation_id,
        )

    async def get_span(self, span_id: Any) -> Any:
        """Get a span by ID."""
        return await self._span_repo.get(span_id)

    async def get_all_spans(self) -> list[Any]:
        """Get all spans."""
        return await self._span_repo.get_all()

    async def get_spans_as_dicts(self) -> list[dict[str, Any]]:
        """Get spans as dictionaries for analysis."""
        return await self._span_repo.get_as_dicts()

    async def clear(self) -> int:
        """Clear all spans."""
        return await self._span_repo.clear()

    async def count(self) -> int:
        """Count all spans."""
        return await self._span_repo.count()


# ---------------------------------------------------------------------------
# Global state for dependencies
# ---------------------------------------------------------------------------

_database: Database | None = None
_span_storage: SpanStorageProtocol | None = None
_conversation_repo: ConversationRepository | None = None
_turn_repo: TurnRepository | None = None
_failure_repo: FailureRepository | None = None
_metrics_repo: MetricsRepository | None = None
_use_postgres: bool = False


def _get_database_url() -> str | None:
    """Get the database URL from environment or config.

    Checks in order:
    1. VOICEOBS_DATABASE_URL environment variable
    2. server.database_url in config file

    Returns:
        Database URL or None if not configured.
    """
    # First check environment variable
    env_url = os.environ.get("VOICEOBS_DATABASE_URL")
    if env_url:
        return env_url

    # Then try config file (but don't fail if config can't be loaded)
    try:
        from voiceobs.config import get_config

        config = get_config()
        return config.server.database_url
    except Exception:
        return None


async def init_database() -> None:
    """Initialize database connection if configured.

    Call this on application startup. If a database URL is configured,
    connects to PostgreSQL and initializes the schema. Otherwise,
    uses in-memory storage.
    """
    global _database, _span_storage
    global _conversation_repo, _turn_repo, _failure_repo, _metrics_repo, _use_postgres

    database_url = _get_database_url()

    if database_url:
        # Use PostgreSQL
        _use_postgres = True
        _database = Database(database_url=database_url)
        await _database.connect()
        await _database.init_schema()

        # Initialize repositories
        _conversation_repo = ConversationRepository(_database)
        _turn_repo = TurnRepository(_database)
        _failure_repo = FailureRepository(_database)
        _metrics_repo = MetricsRepository(_database)

        # Create span storage adapter
        _span_storage = PostgresSpanStoreAdapter(
            span_repo=SpanRepository(_database),
            conversation_repo=_conversation_repo,
        )
    else:
        # Use in-memory store
        _use_postgres = False
        _span_storage = InMemorySpanStoreAdapter(get_span_store())
        _conversation_repo = None
        _turn_repo = None
        _failure_repo = None
        _metrics_repo = None


async def shutdown_database() -> None:
    """Close database connection.

    Call this on application shutdown.
    """
    global _database, _span_storage
    global _conversation_repo, _turn_repo, _failure_repo, _metrics_repo, _use_postgres

    if _database is not None:
        await _database.disconnect()
        _database = None

    _span_storage = None
    _conversation_repo = None
    _turn_repo = None
    _failure_repo = None
    _metrics_repo = None
    _use_postgres = False


def get_storage() -> SpanStorageProtocol:
    """Get the span storage adapter.

    Returns:
        Span storage adapter (either in-memory or PostgreSQL).
        Falls back to in-memory if not initialized.
    """
    if _span_storage is None:
        # Fall back to in-memory if not initialized
        return InMemorySpanStoreAdapter(get_span_store())
    return _span_storage


def get_conversation_repository() -> ConversationRepository | None:
    """Get the conversation repository.

    Returns:
        Conversation repository or None if using in-memory storage.
    """
    return _conversation_repo


def get_turn_repository() -> TurnRepository | None:
    """Get the turn repository.

    Returns:
        Turn repository or None if using in-memory storage.
    """
    return _turn_repo


def get_failure_repository() -> FailureRepository | None:
    """Get the failure repository.

    Returns:
        Failure repository or None if using in-memory storage.
    """
    return _failure_repo


def get_metrics_repository() -> MetricsRepository | None:
    """Get the metrics repository.

    Returns:
        Metrics repository or None if using in-memory storage.
    """
    return _metrics_repo


def is_using_postgres() -> bool:
    """Check if using PostgreSQL storage.

    Returns:
        True if using PostgreSQL, False if using in-memory.
    """
    return _use_postgres


def reset_dependencies() -> None:
    """Reset all dependencies (for testing)."""
    global _database, _span_storage
    global _conversation_repo, _turn_repo, _failure_repo, _metrics_repo, _use_postgres
    _database = None
    _span_storage = None
    _conversation_repo = None
    _turn_repo = None
    _failure_repo = None
    _metrics_repo = None
    _use_postgres = False
