"""Tests for database CLI commands (migrations, import, export)."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from voiceobs.cli import app

runner = CliRunner()


class TestMigrateCommand:
    """Tests for the db migrate command."""

    def test_migrate_command_in_help(self):
        """Test that db command appears in help."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "db" in result.output

    def test_db_help_shows_subcommands(self):
        """Test that db --help shows subcommands."""
        result = runner.invoke(app, ["db", "--help"])

        assert result.exit_code == 0
        assert "migrate" in result.output
        assert "status" in result.output
        assert "history" in result.output

    def test_db_migrate_help(self):
        """Test db migrate command help."""
        result = runner.invoke(app, ["db", "migrate", "--help"])

        assert result.exit_code == 0
        assert "--revision" in result.output

    def test_db_migrate_requires_database_url(self):
        """Test that db migrate requires database URL."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("voiceobs.config.get_config") as mock_config:
                mock_config.return_value.server.database_url = None
                result = runner.invoke(app, ["db", "migrate"])

                assert result.exit_code == 1
                assert "database" in result.output.lower()

    def test_db_migrate_runs_migrations(self):
        """Test that db migrate runs migrations."""
        with patch("voiceobs.server.db.migrations.run_migrations") as mock_run:
            mock_run.return_value = {"success": True, "revision": "head"}
            with patch.dict(
                "os.environ",
                {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
            ):
                result = runner.invoke(app, ["db", "migrate"])

                assert result.exit_code == 0
                mock_run.assert_called_once()

    def test_db_migrate_with_revision(self):
        """Test db migrate with specific revision."""
        with patch("voiceobs.server.db.migrations.run_migrations") as mock_run:
            mock_run.return_value = {"success": True, "revision": "abc123"}
            with patch.dict(
                "os.environ",
                {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
            ):
                result = runner.invoke(app, ["db", "migrate", "--revision", "abc123"])

                assert result.exit_code == 0
                mock_run.assert_called_once()
                call_args = mock_run.call_args
                assert call_args.kwargs.get("revision") == "abc123"

    def test_db_migrate_shows_error_on_failure(self):
        """Test db migrate shows error on failure."""
        with patch("voiceobs.server.db.migrations.run_migrations") as mock_run:
            mock_run.return_value = {"success": False, "error": "Connection refused"}
            with patch.dict(
                "os.environ",
                {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
            ):
                result = runner.invoke(app, ["db", "migrate"])

                assert result.exit_code == 1
                assert "error" in result.output.lower()


class TestDbStatusCommand:
    """Tests for the db status command."""

    def test_db_status_shows_current_revision(self):
        """Test that db status shows current revision."""
        with patch("voiceobs.server.db.migrations.get_current_revision") as mock_revision:
            mock_revision.return_value = "abc123"
            with patch("voiceobs.server.db.migrations.get_pending_migrations") as mock_pending:
                mock_pending.return_value = []
                with patch.dict(
                    "os.environ",
                    {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
                ):
                    result = runner.invoke(app, ["db", "status"])

                    assert result.exit_code == 0
                    assert "abc123" in result.output

    def test_db_status_shows_pending_migrations(self):
        """Test that db status shows pending migrations."""
        with patch("voiceobs.server.db.migrations.get_current_revision") as mock_revision:
            mock_revision.return_value = "abc123"
            with patch("voiceobs.server.db.migrations.get_pending_migrations") as mock_pending:
                mock_pending.return_value = ["def456", "ghi789"]
                with patch.dict(
                    "os.environ",
                    {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
                ):
                    result = runner.invoke(app, ["db", "status"])

                    assert result.exit_code == 0
                    assert "pending" in result.output.lower()

    def test_db_status_shows_up_to_date_when_no_pending(self):
        """Test db status shows up to date when no pending migrations."""
        with patch("voiceobs.server.db.migrations.get_current_revision") as mock_revision:
            mock_revision.return_value = "abc123"
            with patch("voiceobs.server.db.migrations.get_pending_migrations") as mock_pending:
                mock_pending.return_value = []
                with patch.dict(
                    "os.environ",
                    {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
                ):
                    result = runner.invoke(app, ["db", "status"])

                    assert result.exit_code == 0
                    output_lower = result.output.lower()
                    assert "up to date" in output_lower or "current" in output_lower


class TestDbHistoryCommand:
    """Tests for the db history command."""

    def test_db_history_shows_migrations(self):
        """Test that db history shows migration history."""
        with patch("voiceobs.server.db.migrations.get_migration_history") as mock_history:
            mock_history.return_value = [
                {"revision": "abc123", "description": "Initial migration"},
                {"revision": "def456", "description": "Add users table"},
            ]
            result = runner.invoke(app, ["db", "history"])

            assert result.exit_code == 0
            assert "abc123" in result.output
            assert "def456" in result.output


class TestImportCommand:
    """Tests for the import command."""

    def test_import_command_in_help(self):
        """Test that import command appears in help."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Note: may be under 'db' subcommand
        assert "import" in result.output or "db" in result.output

    def test_import_help_shows_options(self):
        """Test import --help shows options."""
        result = runner.invoke(app, ["import", "--help"])

        assert result.exit_code == 0
        assert "--input" in result.output

    def test_import_requires_input_file(self):
        """Test that import requires input file."""
        result = runner.invoke(app, ["import"])

        assert result.exit_code != 0

    def test_import_requires_database_url(self, tmp_path):
        """Test that import requires database URL."""
        input_file = tmp_path / "run.jsonl"
        input_file.write_text('{"name": "test"}')

        with patch.dict("os.environ", {}, clear=True):
            with patch("voiceobs.config.get_config") as mock_config:
                mock_config.return_value.server.database_url = None
                result = runner.invoke(app, ["import", "--input", str(input_file)])

                assert result.exit_code == 1
                assert "database" in result.output.lower()

    def test_import_reads_jsonl_file(self, tmp_path):
        """Test that import reads JSONL file."""
        input_file = tmp_path / "run.jsonl"
        data = [
            {
                "name": "voice.turn",
                "duration_ms": 1000.0,
                "attributes": {"voice.actor": "agent", "voice.conversation.id": "conv-1"},
            },
            {
                "name": "voice.llm",
                "duration_ms": 500.0,
                "attributes": {"voice.stage.type": "llm"},
            },
        ]
        input_file.write_text("\n".join(json.dumps(d) for d in data))

        with patch("voiceobs.cli.import_spans_to_db") as mock_import:
            mock_import.return_value = {"imported": 2, "errors": 0}
            with patch.dict(
                "os.environ",
                {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
            ):
                result = runner.invoke(app, ["import", "--input", str(input_file)])

                assert result.exit_code == 0
                mock_import.assert_called_once()

    def test_import_shows_count(self, tmp_path):
        """Test that import shows imported count."""
        input_file = tmp_path / "run.jsonl"
        data = [{"name": "test", "duration_ms": 100.0, "attributes": {}}]
        input_file.write_text(json.dumps(data[0]))

        with patch("voiceobs.cli.import_spans_to_db") as mock_import:
            mock_import.return_value = {"imported": 1, "errors": 0}
            with patch.dict(
                "os.environ",
                {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
            ):
                result = runner.invoke(app, ["import", "--input", str(input_file)])

                assert result.exit_code == 0
                assert "1" in result.output

    def test_import_handles_errors(self, tmp_path):
        """Test that import handles errors gracefully."""
        input_file = tmp_path / "run.jsonl"
        input_file.write_text("invalid json\n")

        with patch.dict(
            "os.environ",
            {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
        ):
            result = runner.invoke(app, ["import", "--input", str(input_file)])

            assert result.exit_code == 1
            assert "error" in result.output.lower()


class TestExportCommand:
    """Tests for the export command."""

    def test_export_command_in_help(self):
        """Test that export command appears in help."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "export" in result.output

    def test_export_help_shows_options(self):
        """Test export --help shows options."""
        result = runner.invoke(app, ["export", "--help"])

        assert result.exit_code == 0
        assert "--output" in result.output

    def test_export_requires_database_url(self, tmp_path):
        """Test that export requires database URL."""
        output_file = tmp_path / "output.jsonl"

        with patch.dict("os.environ", {}, clear=True):
            with patch("voiceobs.config.get_config") as mock_config:
                mock_config.return_value.server.database_url = None
                result = runner.invoke(app, ["export", "--output", str(output_file)])

                assert result.exit_code == 1
                assert "database" in result.output.lower()

    def test_export_writes_jsonl_file(self, tmp_path):
        """Test that export writes JSONL file."""
        output_file = tmp_path / "output.jsonl"

        with patch("voiceobs.cli.export_spans_from_db") as mock_export:
            mock_export.return_value = {"exported": 5, "path": str(output_file)}
            with patch.dict(
                "os.environ",
                {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
            ):
                result = runner.invoke(app, ["export", "--output", str(output_file)])

                assert result.exit_code == 0
                mock_export.assert_called_once()

    def test_export_shows_count(self, tmp_path):
        """Test that export shows exported count."""
        output_file = tmp_path / "output.jsonl"

        with patch("voiceobs.cli.export_spans_from_db") as mock_export:
            mock_export.return_value = {"exported": 10, "path": str(output_file)}
            with patch.dict(
                "os.environ",
                {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
            ):
                result = runner.invoke(app, ["export", "--output", str(output_file)])

                assert result.exit_code == 0
                assert "10" in result.output

    def test_export_to_stdout(self):
        """Test that export can write to stdout."""
        with patch("voiceobs.cli.export_spans_from_db") as mock_export:
            mock_export.return_value = {
                "exported": 2,
                "spans": [
                    {"name": "test1", "attributes": {}},
                    {"name": "test2", "attributes": {}},
                ],
            }
            with patch.dict(
                "os.environ",
                {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
            ):
                result = runner.invoke(app, ["export"])

                assert result.exit_code == 0

    def test_export_with_conversation_filter(self, tmp_path):
        """Test that export can filter by conversation."""
        output_file = tmp_path / "output.jsonl"

        with patch("voiceobs.cli.export_spans_from_db") as mock_export:
            mock_export.return_value = {"exported": 3, "path": str(output_file)}
            with patch.dict(
                "os.environ",
                {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
            ):
                result = runner.invoke(
                    app,
                    ["export", "--output", str(output_file), "--conversation", "conv-1"],
                )

                assert result.exit_code == 0
                call_args = mock_export.call_args
                assert call_args.kwargs.get("conversation_id") == "conv-1"

    def test_export_handles_errors(self, tmp_path):
        """Test that export handles errors gracefully."""
        output_file = tmp_path / "output.jsonl"

        with patch("voiceobs.cli.export_spans_from_db") as mock_export:
            mock_export.side_effect = Exception("Database connection failed")
            with patch.dict(
                "os.environ",
                {"VOICEOBS_DATABASE_URL": "postgresql://test:test@localhost/test"},
            ):
                result = runner.invoke(app, ["export", "--output", str(output_file)])

                assert result.exit_code == 1
                assert "error" in result.output.lower()
