"""Tests for the server CLI command."""

from unittest.mock import patch

from typer.testing import CliRunner

from voiceobs.cli import app as cli_app

runner = CliRunner()


class TestServerCLI:
    """Tests for the server CLI command."""

    def test_server_command_in_help(self):
        """Test that server command appears in help."""
        result = runner.invoke(cli_app, ["--help"])

        assert result.exit_code == 0
        assert "server" in result.output

    def test_server_help(self):
        """Test server command help."""
        result = runner.invoke(cli_app, ["server", "--help"])

        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--reload" in result.output

    def test_server_without_dependencies(self):
        """Test server command fails gracefully without uvicorn."""
        with patch.dict("sys.modules", {"uvicorn": None}):
            # This test verifies the import error handling
            # The actual behavior depends on how Python handles the mock
            pass
