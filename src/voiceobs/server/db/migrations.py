"""Database migrations module using Alembic.

This module provides functions to manage database migrations for voiceobs.
It uses Alembic for versioning and applying database schema changes.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine


def get_migrations_directory() -> Path:
    """Get the path to the migrations directory.

    Returns:
        Path to the alembic migrations directory.
    """
    return Path(__file__).parent / "alembic"


def get_alembic_config(database_url: str | None = None) -> Config:
    """Get an Alembic Config object.

    Args:
        database_url: Optional database URL to use. If not provided,
            the URL from environment or config will be used.

    Returns:
        Alembic Config object.
    """
    migrations_dir = get_migrations_directory()
    ini_path = migrations_dir / "alembic.ini"

    config = Config(str(ini_path))
    config.set_main_option("script_location", str(migrations_dir))

    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)

    return config


def _get_database_url() -> str | None:
    """Get the database URL from environment or config.

    Returns:
        Database URL or None if not configured.
    """
    # First check environment variable
    env_url = os.environ.get("VOICEOBS_DATABASE_URL")
    if env_url:
        return env_url

    # Then try config file
    try:
        from voiceobs.config import get_config

        config = get_config()
        return config.server.database_url
    except Exception:
        return None


def _create_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine.

    Args:
        database_url: Database URL to connect to.

    Returns:
        SQLAlchemy Engine instance.
    """
    return create_engine(database_url)


@contextmanager
def _get_connection(database_url: str) -> Iterator[Connection]:
    """Get a database connection.

    Args:
        database_url: Database URL to connect to.

    Yields:
        SQLAlchemy Connection.
    """
    engine = _create_engine(database_url)
    with engine.connect() as connection:
        yield connection


def _get_migration_context(connection: Connection) -> MigrationContext:
    """Get an Alembic migration context.

    Args:
        connection: SQLAlchemy connection.

    Returns:
        Alembic MigrationContext.
    """
    return MigrationContext.configure(connection)


def _get_script_directory(config: Config | None = None) -> ScriptDirectory:
    """Get the Alembic script directory.

    Args:
        config: Optional Alembic config. If not provided, a default is created.

    Returns:
        Alembic ScriptDirectory.
    """
    if config is None:
        config = get_alembic_config()
    return ScriptDirectory.from_config(config)


def get_current_revision(database_url: str) -> str | None:
    """Get the current database revision.

    Args:
        database_url: Database URL to check.

    Returns:
        Current revision string or None if no migrations have been applied.
    """
    with _get_connection(database_url) as connection:
        context = _get_migration_context(connection)
        return context.get_current_revision()


def get_pending_migrations(database_url: str) -> list[str]:
    """Get list of pending migrations.

    Args:
        database_url: Database URL to check.

    Returns:
        List of revision IDs that have not been applied.
    """
    with _get_connection(database_url) as connection:
        context = _get_migration_context(connection)
        current = context.get_current_revision()

        script = _get_script_directory()
        pending = []

        # Get all revisions and find those not yet applied
        for rev in script.walk_revisions():
            if current is None or not script.get_revision(current).is_ancestor_of(rev):
                pending.append(rev.revision)

        # Reverse to get chronological order
        pending.reverse()
        return pending


def _check_alembic_version_table_exists(connection: Connection) -> bool:
    """Check if the alembic_version table exists.

    Args:
        connection: SQLAlchemy connection.

    Returns:
        True if the table exists, False otherwise.
    """
    inspector = inspect(connection)
    tables = inspector.get_table_names()
    return "alembic_version" in tables


def _detect_database_revision(connection: Connection) -> str | None:
    """Detect which migration revision the database is at based on existing tables.

    Args:
        connection: SQLAlchemy connection.

    Returns:
        Revision string or None if database is empty.
    """
    inspector = inspect(connection)
    existing_tables = inspector.get_table_names()

    if not existing_tables:
        return None  # Empty database

    # Check for test tables (from migration 003)
    has_test_tables = any(
        table in existing_tables for table in ["test_suites", "test_scenarios", "test_executions"]
    )
    if has_test_tables:
        return "003"

    # Check for search indexes (from migration 002)
    # Check if turns table has GIN index for full-text search
    has_search_indexes = False
    if "turns" in existing_tables:
        try:
            indexes = inspector.get_indexes("turns")
            index_names = [idx["name"] for idx in indexes]
            # Check for GIN index on transcript
            has_search_indexes = any(
                "transcript_gin" in name.lower() or "gin" in name.lower() for name in index_names
            )
        except Exception:
            pass

    if has_search_indexes:
        return "002"

    # Check for initial schema tables (from migration 001)
    has_initial_schema = any(
        table in existing_tables for table in ["conversations", "spans", "turns", "failures"]
    )
    if has_initial_schema:
        return "001"

    return None


def _ensure_alembic_version_table(database_url: str) -> None:
    """Ensure the alembic_version table exists and is properly initialized.

    If the table doesn't exist but other tables do, this will stamp the database
    with the appropriate revision. Alembic's command.stamp() will automatically
    create the alembic_version table if it doesn't exist. If no tables exist,
    Alembic will create the version table automatically when running migrations.

    Args:
        database_url: Database URL to check.
    """
    with _get_connection(database_url) as connection:
        if _check_alembic_version_table_exists(connection):
            return  # Table already exists, nothing to do

        # Check if any tables exist (indicating database was set up manually)
        detected_revision = _detect_database_revision(connection)

        # If tables exist but alembic_version doesn't, stamp the database
        # command.stamp() will automatically create the alembic_version table
        if detected_revision:
            config = get_alembic_config(database_url)
            # This will create alembic_version table if it doesn't exist
            command.stamp(config, detected_revision)


def run_migrations(
    database_url: str,
    revision: str = "head",
    direction: str = "upgrade",
) -> dict[str, Any]:
    """Run database migrations.

    Args:
        database_url: Database URL to migrate.
        revision: Target revision (default: "head").
        direction: "upgrade" or "downgrade" (default: "upgrade").

    Returns:
        Dictionary with success status and details.
    """
    try:
        # Ensure alembic_version table exists before running migrations
        _ensure_alembic_version_table(database_url)

        config = get_alembic_config(database_url)

        if direction == "upgrade":
            command.upgrade(config, revision)
        else:
            command.downgrade(config, revision)

        return {
            "success": True,
            "revision": revision,
            "direction": direction,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "revision": revision,
            "direction": direction,
        }


def get_migration_history() -> list[dict[str, Any]]:
    """Get the migration history.

    Returns:
        List of dictionaries with migration details.
    """
    script = _get_script_directory()
    history = []

    for rev in script.walk_revisions():
        history.append(
            {
                "revision": rev.revision,
                "down_revision": rev.down_revision,
                "description": rev.doc or "",
            }
        )

    return history


def create_tables_from_schema(database_url: str) -> dict[str, Any]:
    """Create tables directly from the schema SQL file.

    This is an alternative to using migrations for initial setup.

    Args:
        database_url: Database URL to use.

    Returns:
        Dictionary with success status.
    """
    schema_path = Path(__file__).parent / "schema.sql"

    try:
        with _get_connection(database_url) as connection:
            schema_sql = schema_path.read_text()
            connection.execute(text(schema_sql))
            connection.commit()

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
