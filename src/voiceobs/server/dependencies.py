"""FastAPI dependencies for voiceobs server.

This module provides dependency injection for database connections and repositories.
PostgreSQL is required for the application to function.

Database Initialization
-----------------------
The application requires PostgreSQL to be configured via:
- VOICEOBS_DATABASE_URL environment variable, or
- server.database_url in voiceobs.yaml configuration file

The application will fail to start if no database is configured.

Storage Adapters
----------------
The API routes use an async interface for storage operations. The PostgresSpanStoreAdapter
wraps the async SpanRepository and adds conversation linking logic.

Spans are the primary ingestion point for the API. All routes that ingest or query data
work with spans. Conversations, turns, and failures are stored separately but populated
from span data.

Repositories
------------
All repositories (ConversationRepository, TurnRepository, FailureRepository, etc.)
are exposed as singletons initialized at startup. They will raise RuntimeError
if accessed before database initialization.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Protocol

from voiceobs.server.db.connection import Database
from voiceobs.server.db.repositories import (
    AgentRepository,
    ConversationRepository,
    FailureRepository,
    MetricsRepository,
    OrganizationInviteRepository,
    OrganizationMemberRepository,
    OrganizationRepository,
    PersonaRepository,
    SpanRepository,
    TestExecutionRepository,
    TestScenarioRepository,
    TestSuiteRepository,
    TurnRepository,
    UserRepository,
)
from voiceobs.server.services.agent_verification.service import AgentVerificationService
from voiceobs.server.services.organization_service import OrganizationService
from voiceobs.server.services.scenario_generation.service import ScenarioGenerationService

logger = logging.getLogger(__name__)


class SpanStorageProtocol(Protocol):
    """Protocol defining the async interface for span storage.

    This protocol defines the interface that span storage adapters must implement.
    In production, PostgresSpanStoreAdapter is used.
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


class PostgresSpanStoreAdapter:
    """Adapter that wraps PostgreSQL repositories with conversation linking.

    This adapter implements the SpanStorageProtocol using PostgreSQL repositories.
    It handles automatic conversation creation when spans contain a
    `voice.conversation.id` attribute.
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
_test_suite_repo: TestSuiteRepository | None = None
_test_scenario_repo: TestScenarioRepository | None = None
_test_execution_repo: TestExecutionRepository | None = None
_persona_repo: PersonaRepository | None = None
_agent_repo: AgentRepository | None = None
_user_repo: UserRepository | None = None
_organization_repo: OrganizationRepository | None = None
_organization_member_repo: OrganizationMemberRepository | None = None
_organization_invite_repo: OrganizationInviteRepository | None = None
_agent_verification_service: AgentVerificationService | None = None
_organization_service: OrganizationService | None = None
_scenario_generation_service: ScenarioGenerationService | None = None
_use_postgres: bool = False
_audio_storage: Any | None = None


def _get_database_url() -> str | None:
    """Get the database URL from environment variable or config file.

    Checks in order:
    1. VOICEOBS_DATABASE_URL environment variable (takes precedence)
    2. server.database_url in config file (voiceobs.yaml) (fallback)

    Returns:
        Database URL or None if not configured.
    """
    # First check environment variable (takes precedence)
    env_url = os.environ.get("VOICEOBS_DATABASE_URL")
    if env_url:
        logger.info(f"Database URL found in environment variable: {env_url[:30]}...")
        return env_url

    # Fallback to config file (voiceobs.yaml)
    try:
        from voiceobs.config import get_config

        config = get_config()
        config_url = config.server.database_url
        if config_url:
            logger.info(f"Database URL found in config file (voiceobs.yaml): {config_url[:30]}...")
            return config_url
        else:
            logger.info("Database URL is None in config file (voiceobs.yaml)")
    except Exception as e:
        logger.warning(f"Failed to load database URL from config file: {e}", exc_info=True)

    logger.warning("No database URL configured (neither in environment variable nor config file)")
    return None


async def init_database() -> None:
    """Initialize database connection.

    Call this on application startup. Connects to PostgreSQL and initializes
    the schema. Raises RuntimeError if database URL is not configured.

    Raises:
        RuntimeError: If database URL is not configured.
    """
    global _database, _span_storage
    global _conversation_repo, _turn_repo, _failure_repo, _metrics_repo
    global _test_suite_repo, _test_scenario_repo, _test_execution_repo, _persona_repo, _agent_repo
    global _user_repo, _organization_repo, _organization_member_repo, _organization_invite_repo
    global _agent_verification_service, _organization_service, _use_postgres

    database_url = _get_database_url()
    logger.info(f"Database URL retrieved: {'configured' if database_url else 'not configured'}")

    if not database_url:
        error_msg = (
            "PostgreSQL database is required but not configured. "
            "Please set VOICEOBS_DATABASE_URL environment variable or configure "
            "server.database_url in voiceobs.yaml"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Initialize PostgreSQL
    logger.info("Initializing PostgreSQL database connection")
    _use_postgres = True
    _database = Database(database_url=database_url)
    await _database.connect()
    await _database.init_schema()

    # Initialize repositories
    _conversation_repo = ConversationRepository(_database)
    _turn_repo = TurnRepository(_database)
    _failure_repo = FailureRepository(_database)
    _metrics_repo = MetricsRepository(_database)
    _persona_repo = PersonaRepository(_database)
    _agent_repo = AgentRepository(_database)
    _user_repo = UserRepository(_database)
    _organization_repo = OrganizationRepository(_database)
    _organization_member_repo = OrganizationMemberRepository(_database)
    _organization_invite_repo = OrganizationInviteRepository(_database)
    _agent_verification_service = AgentVerificationService(_agent_repo)
    _organization_service = OrganizationService(
        org_repo=_organization_repo,
        member_repo=_organization_member_repo,
        user_repo=_user_repo,
    )
    _test_suite_repo = TestSuiteRepository(_database)
    _test_scenario_repo = TestScenarioRepository(_database, _persona_repo)
    _test_execution_repo = TestExecutionRepository(_database)

    # Create span storage adapter
    _span_storage = PostgresSpanStoreAdapter(
        span_repo=SpanRepository(_database),
        conversation_repo=_conversation_repo,
    )


async def shutdown_database() -> None:
    """Close database connection.

    Call this on application shutdown.
    """
    global _database, _span_storage
    global _conversation_repo, _turn_repo, _failure_repo, _metrics_repo
    global _test_suite_repo, _test_scenario_repo, _test_execution_repo, _persona_repo, _agent_repo
    global _user_repo, _organization_repo, _organization_member_repo, _organization_invite_repo
    global _agent_verification_service, _organization_service, _scenario_generation_service
    global _use_postgres

    if _database is not None:
        await _database.disconnect()
        _database = None

    _span_storage = None
    _conversation_repo = None
    _turn_repo = None
    _failure_repo = None
    _metrics_repo = None
    _test_suite_repo = None
    _test_scenario_repo = None
    _test_execution_repo = None
    _persona_repo = None
    _agent_repo = None
    _user_repo = None
    _organization_repo = None
    _organization_member_repo = None
    _organization_invite_repo = None
    _agent_verification_service = None
    _organization_service = None
    _scenario_generation_service = None
    _use_postgres = False


def _ensure_initialized(component: Any | None, component_name: str) -> Any:
    """Ensure a database component is initialized.

    Args:
        component: The component to check (repository, service, etc.).
        component_name: Human-readable name for error messages.

    Returns:
        The component if initialized.

    Raises:
        RuntimeError: If component is None (database not initialized).
    """
    if component is None:
        raise RuntimeError(
            f"{component_name} is not available. "
            "Database not initialized. Call init_database() first."
        )
    return component


def get_storage() -> SpanStorageProtocol:
    """Get the span storage adapter.

    Returns:
        PostgreSQL span storage adapter.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_span_storage, "Span storage")


def get_conversation_repository() -> ConversationRepository:
    """Get the conversation repository.

    Returns:
        Conversation repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_conversation_repo, "Conversation repository")


def get_turn_repository() -> TurnRepository:
    """Get the turn repository.

    Returns:
        Turn repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_turn_repo, "Turn repository")


def get_failure_repository() -> FailureRepository:
    """Get the failure repository.

    Returns:
        Failure repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_failure_repo, "Failure repository")


def get_metrics_repository() -> MetricsRepository:
    """Get the metrics repository.

    Returns:
        Metrics repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_metrics_repo, "Metrics repository")


def get_test_suite_repository() -> TestSuiteRepository:
    """Get the test suite repository.

    Returns:
        Test suite repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_test_suite_repo, "Test suite repository")


def get_test_scenario_repository() -> TestScenarioRepository:
    """Get the test scenario repository.

    Returns:
        Test scenario repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_test_scenario_repo, "Test scenario repository")


def get_test_execution_repository() -> TestExecutionRepository:
    """Get the test execution repository.

    Returns:
        Test execution repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_test_execution_repo, "Test execution repository")


def get_persona_repository() -> PersonaRepository:
    """Get the persona repository.

    Returns:
        Persona repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_persona_repo, "Persona repository")


def get_agent_repository() -> AgentRepository:
    """Get the agent repository.

    Returns:
        Agent repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_agent_repo, "Agent repository")


def get_user_repository() -> UserRepository:
    """Get the user repository.

    Returns:
        User repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_user_repo, "User repository")


def get_organization_repository() -> OrganizationRepository:
    """Get the organization repository.

    Returns:
        Organization repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_organization_repo, "Organization repository")


def get_organization_member_repository() -> OrganizationMemberRepository:
    """Get the organization member repository.

    Returns:
        Organization member repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_organization_member_repo, "Organization member repository")


def get_organization_invite_repository() -> OrganizationInviteRepository:
    """Get the organization invite repository.

    Returns:
        Organization invite repository instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_organization_invite_repo, "Organization invite repository")


def get_agent_verification_service() -> AgentVerificationService:
    """Get the agent verification service.

    Returns:
        Agent verification service instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_agent_verification_service, "Agent verification service")


def get_organization_service() -> OrganizationService:
    """Get the organization service.

    Returns:
        Organization service instance.

    Raises:
        RuntimeError: If database is not initialized.
    """
    return _ensure_initialized(_organization_service, "Organization service")


def get_scenario_generation_service() -> ScenarioGenerationService | None:
    """Get the scenario generation service.

    Creates a ScenarioGenerationService instance lazily using LLMServiceFactory.

    Returns:
        ScenarioGenerationService instance or None if LLM service cannot be created.

    Note:
        Returns None if LLM service creation fails (e.g., missing API keys).
        This is acceptable since scenario generation is an optional feature.
    """
    global _scenario_generation_service

    # Create service lazily if not already created
    if _scenario_generation_service is None:
        try:
            from voiceobs.server.services.llm_factory import LLMServiceFactory

            llm_service = LLMServiceFactory.create()
            _scenario_generation_service = ScenarioGenerationService(
                llm_service=llm_service,
                test_suite_repo=get_test_suite_repository(),
                test_scenario_repo=get_test_scenario_repository(),
                persona_repo=get_persona_repository(),
                agent_repo=get_agent_repository(),
            )
            logger.info("Created ScenarioGenerationService")
        except Exception as e:
            logger.warning(f"Failed to create ScenarioGenerationService: {e}")
            return None

    return _scenario_generation_service


def is_using_postgres() -> bool:
    """Check if PostgreSQL is initialized.

    Returns:
        True if PostgreSQL database has been initialized, False otherwise.

    Note:
        This function is primarily used for startup checks. In normal operation,
        PostgreSQL should always be initialized, so this should always return True.
    """
    return _use_postgres


def get_audio_storage() -> Any:
    """Get the audio storage instance.

    Returns:
        AudioStorage instance configured from environment or defaults.
    """
    global _audio_storage

    if _audio_storage is None:
        from voiceobs.server.storage import AudioStorage

        # Get configuration from environment
        provider = os.environ.get("VOICEOBS_AUDIO_STORAGE_PROVIDER", "local")
        base_path = os.environ.get("VOICEOBS_AUDIO_STORAGE_PATH", "/tmp/voiceobs-audio")

        if provider == "s3":
            bucket_name = os.environ.get("VOICEOBS_AUDIO_S3_BUCKET", base_path)
            aws_region = os.environ.get("VOICEOBS_AUDIO_S3_REGION", "us-east-1")
            _audio_storage = AudioStorage(
                provider="s3",
                base_path=bucket_name,
                aws_region=aws_region,
            )
        else:
            _audio_storage = AudioStorage(
                provider="local",
                base_path=base_path,
            )

    return _audio_storage


def reset_dependencies() -> None:
    """Reset all dependencies (for testing)."""
    global _database, _span_storage
    global _conversation_repo, _turn_repo, _failure_repo, _metrics_repo
    global _test_suite_repo, _test_scenario_repo, _test_execution_repo, _persona_repo, _agent_repo
    global _user_repo, _organization_repo, _organization_member_repo, _organization_invite_repo
    global _agent_verification_service, _organization_service, _scenario_generation_service
    global _use_postgres, _audio_storage
    _database = None
    _span_storage = None
    _conversation_repo = None
    _turn_repo = None
    _failure_repo = None
    _metrics_repo = None
    _test_suite_repo = None
    _test_scenario_repo = None
    _test_execution_repo = None
    _persona_repo = None
    _agent_repo = None
    _user_repo = None
    _organization_repo = None
    _organization_member_repo = None
    _organization_invite_repo = None
    _agent_verification_service = None
    _organization_service = None
    _scenario_generation_service = None
    _use_postgres = False
    _audio_storage = None
