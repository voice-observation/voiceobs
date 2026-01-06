"""Tests for database migrations module."""

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestMigrationsModule:
    """Tests for the migrations module."""

    def test_get_alembic_config_returns_config(self):
        """Test that get_alembic_config returns an Alembic Config object."""
        from voiceobs.server.db.migrations import get_alembic_config

        config = get_alembic_config()
        assert config is not None
        # Verify it has the expected alembic.ini location
        assert config.config_file_name is not None

    def test_get_alembic_config_with_database_url(self):
        """Test that get_alembic_config can accept a database URL."""
        from voiceobs.server.db.migrations import get_alembic_config

        test_url = "postgresql://test:test@localhost:5432/testdb"
        config = get_alembic_config(database_url=test_url)
        assert config is not None

    def test_migrations_directory_exists(self):
        """Test that the migrations directory exists."""
        from voiceobs.server.db.migrations import get_migrations_directory

        migrations_dir = get_migrations_directory()
        assert migrations_dir.exists()
        assert migrations_dir.is_dir()

    def test_alembic_ini_exists(self):
        """Test that alembic.ini file exists."""
        from voiceobs.server.db.migrations import get_alembic_config

        config = get_alembic_config()
        ini_path = Path(config.config_file_name)
        assert ini_path.exists()


class TestMigrationOperations:
    """Tests for migration operations."""

    def test_get_current_revision_returns_none_for_fresh_db(self):
        """Test that get_current_revision returns None for a fresh database."""
        from voiceobs.server.db.migrations import get_current_revision

        # Mock the database connection
        with patch("voiceobs.server.db.migrations._get_connection") as mock_conn:
            # Simulate fresh database with no alembic_version table
            mock_conn.return_value.__enter__ = MagicMock()
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            mock_context = MagicMock()
            mock_context.get_current_revision.return_value = None
            with patch(
                "voiceobs.server.db.migrations._get_migration_context",
                return_value=mock_context,
            ):
                result = get_current_revision("postgresql://test:test@localhost/test")
                assert result is None

    def test_get_pending_migrations_returns_list(self):
        """Test that get_pending_migrations returns a list of pending migrations."""
        from voiceobs.server.db.migrations import get_pending_migrations

        # Mock at connection and context level
        with patch("voiceobs.server.db.migrations._get_connection") as mock_conn:
            mock_conn.return_value.__enter__ = MagicMock()
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)

            with patch("voiceobs.server.db.migrations._get_migration_context") as mock_context:
                mock_context.return_value.get_current_revision.return_value = None

                with patch("voiceobs.server.db.migrations._get_script_directory") as mock_scripts:
                    mock_scripts.return_value.walk_revisions.return_value = []

                    result = get_pending_migrations("postgresql://test:test@localhost/test")
                    assert isinstance(result, list)


class TestMigrationRunner:
    """Tests for running migrations."""

    def test_run_migrations_upgrade_head(self):
        """Test that run_migrations can upgrade to head."""
        from voiceobs.server.db.migrations import run_migrations

        with patch("voiceobs.server.db.migrations.command") as mock_command:
            with patch("voiceobs.server.db.migrations._ensure_alembic_version_table"):
                run_migrations(
                    database_url="postgresql://test:test@localhost/test",
                    revision="head",
                )
                mock_command.upgrade.assert_called_once()

    def test_run_migrations_downgrade(self):
        """Test that run_migrations can downgrade."""
        from voiceobs.server.db.migrations import run_migrations

        with patch("voiceobs.server.db.migrations.command") as mock_command:
            with patch("voiceobs.server.db.migrations._ensure_alembic_version_table"):
                run_migrations(
                    database_url="postgresql://test:test@localhost/test",
                    revision="-1",
                    direction="downgrade",
                )
                mock_command.downgrade.assert_called_once()

    def test_run_migrations_returns_success(self):
        """Test that run_migrations returns success status."""
        from voiceobs.server.db.migrations import run_migrations

        with patch("voiceobs.server.db.migrations.command"):
            with patch("voiceobs.server.db.migrations._ensure_alembic_version_table"):
                result = run_migrations(
                    database_url="postgresql://test:test@localhost/test",
                    revision="head",
                )
                assert result["success"] is True

    def test_run_migrations_returns_error_on_failure(self):
        """Test that run_migrations returns error on failure."""
        from voiceobs.server.db.migrations import run_migrations

        with patch("voiceobs.server.db.migrations.command") as mock_command:
            with patch("voiceobs.server.db.migrations._ensure_alembic_version_table"):
                mock_command.upgrade.side_effect = Exception("Migration failed")
                result = run_migrations(
                    database_url="postgresql://test:test@localhost/test",
                    revision="head",
                )
                assert result["success"] is False
                assert "error" in result


class TestMigrationHistory:
    """Tests for migration history."""

    def test_get_migration_history_returns_list(self):
        """Test that get_migration_history returns a list."""
        from voiceobs.server.db.migrations import get_migration_history

        with patch("voiceobs.server.db.migrations._get_script_directory") as mock_scripts:
            mock_revision = MagicMock()
            mock_revision.revision = "abc123"
            mock_revision.down_revision = None
            mock_revision.doc = "Initial migration"
            mock_scripts.return_value.walk_revisions.return_value = [mock_revision]
            result = get_migration_history()
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["revision"] == "abc123"


class TestGetDatabaseUrl:
    """Tests for _get_database_url helper."""

    def test_get_database_url_from_env(self):
        """Test getting database URL from environment."""
        from voiceobs.server.db.migrations import _get_database_url

        with patch.dict(
            "os.environ",
            {"VOICEOBS_DATABASE_URL": "postgresql://test/db"},
            clear=True,
        ):
            result = _get_database_url()
            assert result == "postgresql://test/db"

    def test_get_database_url_from_config(self):
        """Test getting database URL from config when env not set."""
        from voiceobs.server.db.migrations import _get_database_url

        # Need to also mock os.environ.get since the module imports os
        with patch("voiceobs.server.db.migrations.os.environ.get") as mock_get:
            mock_get.return_value = None  # No env var set
            with patch("voiceobs.config.get_config") as mock_config:
                mock_config.return_value.server.database_url = "postgresql://config/db"
                result = _get_database_url()
                assert result == "postgresql://config/db"

    def test_get_database_url_returns_none_when_not_configured(self):
        """Test returning None when no URL configured."""
        from voiceobs.server.db.migrations import _get_database_url

        with patch("voiceobs.server.db.migrations.os.environ.get") as mock_get:
            mock_get.return_value = None  # No env var set
            with patch("voiceobs.config.get_config") as mock_config:
                mock_config.side_effect = Exception("No config")
                result = _get_database_url()
                assert result is None


class TestCreateTablesFromSchema:
    """Tests for create_tables_from_schema."""

    def test_create_tables_from_schema_success(self):
        """Test creating tables from schema SQL."""
        from voiceobs.server.db.migrations import create_tables_from_schema

        with patch("voiceobs.server.db.migrations._get_connection") as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_connection)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)

            with patch("pathlib.Path.read_text") as mock_read:
                mock_read.return_value = "CREATE TABLE test (id INT);"
                result = create_tables_from_schema("postgresql://test/db")

                assert result["success"] is True

    def test_create_tables_from_schema_failure(self):
        """Test handling failure when creating tables."""
        from voiceobs.server.db.migrations import create_tables_from_schema

        with patch("voiceobs.server.db.migrations._get_connection") as mock_conn:
            mock_conn.side_effect = Exception("Connection failed")

            result = create_tables_from_schema("postgresql://test/db")

            assert result["success"] is False
            assert "error" in result
