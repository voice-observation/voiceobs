"""Tests for CLI commands."""

import subprocess
import sys
from unittest.mock import patch

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from typer.testing import CliRunner

from voiceobs.cli import app
from voiceobs.tracing import reset_initialization

runner = CliRunner()


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_outputs_version(self):
        """Test that version command outputs the correct version."""
        from voiceobs._version import __version__

        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert f"voiceobs {__version__}" in result.output


class TestDemoCommand:
    """Tests for the demo command."""

    def test_demo_runs_successfully(self):
        """Test that demo command runs without errors."""
        result = runner.invoke(app, ["demo"])

        assert result.exit_code == 0
        assert "voiceobs Demo" in result.output
        assert "Simulating a voice conversation..." in result.output
        assert "Conversation started:" in result.output
        assert "Conversation ended." in result.output

    def test_demo_shows_initialized_message_when_initialized(self):
        """Test that demo shows initialization message when tracing is initialized."""
        # Mock ensure_tracing_initialized to return True (simulating initialization)
        # Patch where it's imported from (voiceobs module)
        with patch("voiceobs.ensure_tracing_initialized", return_value=True):
            result = runner.invoke(app, ["demo"])

            assert result.exit_code == 0
            assert "Tracing initialized by voiceobs (ConsoleSpanExporter)" in result.output

    def test_demo_shows_existing_config_message_when_provider_exists(self):
        """Test that demo shows existing config message when provider already exists."""
        # Mock ensure_tracing_initialized to return False (simulating existing config)
        with patch("voiceobs.ensure_tracing_initialized", return_value=False):
            result = runner.invoke(app, ["demo"])

            assert result.exit_code == 0
            assert "Using existing tracing configuration" in result.output

    def test_demo_includes_all_expected_output(self):
        """Test that demo includes all expected conversation elements."""
        result = runner.invoke(app, ["demo"])

        assert result.exit_code == 0
        # Check for demo header
        assert "voiceobs Demo" in result.output
        assert "=" * 50 in result.output
        # Check for initialization message
        assert "Initializing tracing with ConsoleSpanExporter..." in result.output
        # Check for conversation simulation
        assert "Simulating a voice conversation..." in result.output
        assert "-" * 50 in result.output
        # Check for user and agent messages
        assert "[User]: Hello, what's the weather like today?" in result.output
        assert "[Agent]: Let me check that for you..." in result.output
        assert "[User]: Thanks! What about tomorrow?" in result.output
        assert "[Agent]: Tomorrow looks sunny with highs around 72F." in result.output
        # Check for ending
        assert "Conversation ended." in result.output
        # Check for span information
        assert "The spans above show the OpenTelemetry trace data." in result.output
        assert "Each voice.turn span includes:" in result.output
        assert "  - voice.conversation.id" in result.output
        assert "  - voice.turn.id" in result.output
        assert "  - voice.turn.index" in result.output
        assert "  - voice.actor (user/agent)" in result.output
        assert "  - voice.schema.version" in result.output


class TestDoctorCommand:
    """Tests for the doctor command."""

    def test_doctor_runs_successfully(self):
        """Test that doctor command runs without errors."""
        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "voiceobs Doctor" in result.output
        assert "voiceobs version:" in result.output
        assert "Schema version:" in result.output
        assert "OpenTelemetry Status:" in result.output

    def test_doctor_shows_version_info(self):
        """Test that doctor shows version information."""
        from voiceobs import VOICE_SCHEMA_VERSION, __version__

        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert f"voiceobs version: {__version__}" in result.output
        assert f"Schema version: {VOICE_SCHEMA_VERSION}" in result.output

    def test_doctor_shows_provider_info(self):
        """Test that doctor shows provider information."""
        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "Provider type:" in result.output
        assert "Is no-op:" in result.output
        assert "Initialized by voiceobs:" in result.output

    def test_doctor_shows_noop_status_when_noop_provider(self):
        """Test that doctor shows noop status when provider is noop."""
        # Mock get_tracer_provider_info to return noop status
        # Patch where it's imported from (voiceobs module)
        mock_info = {
            "provider_type": "NoOpTracerProvider",
            "is_noop": True,
            "voiceobs_initialized": False,
        }
        with patch("voiceobs.get_tracer_provider_info", return_value=mock_info):
            result = runner.invoke(app, ["doctor"])

            assert result.exit_code == 0
            assert "Status: No tracing configured" in result.output
            assert "To enable tracing, either:" in result.output
            assert "  1. Call ensure_tracing_initialized() in your code" in result.output
            assert "  2. Configure your own TracerProvider before using voiceobs" in result.output
            assert "Quick start:" in result.output
            assert "  from voiceobs import ensure_tracing_initialized" in result.output
            assert "  ensure_tracing_initialized()" in result.output

    def test_doctor_shows_active_status_when_provider_exists(self):
        """Test that doctor shows active status when provider exists."""
        # Set up a real provider
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        reset_initialization()

        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "Status: Tracing is active" in result.output
        assert "Spans will be exported via the configured provider." in result.output

    def test_doctor_includes_demo_suggestion(self):
        """Test that doctor includes suggestion to run demo."""
        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "Run 'voiceobs demo' to see tracing in action." in result.output


class TestCompareCommand:
    """Tests for the compare command."""

    def test_compare_runs_successfully(self, tmp_path):
        """Test that compare command runs without errors."""
        import json

        # Create baseline file
        baseline_file = tmp_path / "baseline.jsonl"
        baseline_data = [
            {
                "name": "voice.llm",
                "duration_ms": 200.0,
                "attributes": {
                    "voice.conversation.id": "conv-1",
                    "voice.stage.type": "llm",
                },
            },
            {
                "name": "voice.turn",
                "duration_ms": 500.0,
                "attributes": {
                    "voice.conversation.id": "conv-1",
                    "voice.actor": "agent",
                    "voice.silence.after_user_ms": 100.0,
                },
            },
        ]
        baseline_file.write_text("\n".join(json.dumps(d) for d in baseline_data))

        # Create current file (identical to baseline)
        current_file = tmp_path / "current.jsonl"
        current_file.write_text("\n".join(json.dumps(d) for d in baseline_data))

        result = runner.invoke(
            app, ["compare", "--baseline", str(baseline_file), "--current", str(current_file)]
        )

        assert result.exit_code == 0
        assert "voiceobs Comparison Report" in result.output
        assert "No regressions detected" in result.output

    def test_compare_detects_regression(self, tmp_path):
        """Test that compare command detects regressions."""
        import json

        # Create baseline file
        baseline_file = tmp_path / "baseline.jsonl"
        baseline_data = [
            {
                "name": "voice.llm",
                "duration_ms": 200.0,
                "attributes": {"voice.stage.type": "llm"},
            },
        ]
        baseline_file.write_text(json.dumps(baseline_data[0]))

        # Create current file with 50% increase (above critical threshold)
        current_file = tmp_path / "current.jsonl"
        current_data = [
            {
                "name": "voice.llm",
                "duration_ms": 300.0,
                "attributes": {"voice.stage.type": "llm"},
            },
        ]
        current_file.write_text(json.dumps(current_data[0]))

        result = runner.invoke(
            app, ["compare", "--baseline", str(baseline_file), "--current", str(current_file)]
        )

        assert result.exit_code == 0  # Without --fail-on-regression, should still succeed
        assert "Regressions" in result.output

    def test_compare_fail_on_regression_flag(self, tmp_path):
        """Test that --fail-on-regression exits with code 1 on regressions."""
        import json

        # Create baseline file
        baseline_file = tmp_path / "baseline.jsonl"
        baseline_data = [
            {
                "name": "voice.llm",
                "duration_ms": 200.0,
                "attributes": {"voice.stage.type": "llm"},
            },
        ]
        baseline_file.write_text(json.dumps(baseline_data[0]))

        # Create current file with 50% increase (above critical threshold)
        current_file = tmp_path / "current.jsonl"
        current_data = [
            {
                "name": "voice.llm",
                "duration_ms": 300.0,
                "attributes": {"voice.stage.type": "llm"},
            },
        ]
        current_file.write_text(json.dumps(current_data[0]))

        result = runner.invoke(
            app,
            [
                "compare",
                "--baseline",
                str(baseline_file),
                "--current",
                str(current_file),
                "--fail-on-regression",
            ],
        )

        assert result.exit_code == 1
        assert "Regression(s) detected" in result.output

    def test_compare_no_regression_with_fail_flag(self, tmp_path):
        """Test that --fail-on-regression exits with code 0 when no regressions."""
        import json

        # Create identical files
        baseline_file = tmp_path / "baseline.jsonl"
        baseline_data = [
            {
                "name": "voice.llm",
                "duration_ms": 200.0,
                "attributes": {"voice.stage.type": "llm"},
            },
        ]
        baseline_file.write_text(json.dumps(baseline_data[0]))

        current_file = tmp_path / "current.jsonl"
        current_file.write_text(json.dumps(baseline_data[0]))

        result = runner.invoke(
            app,
            [
                "compare",
                "--baseline",
                str(baseline_file),
                "--current",
                str(current_file),
                "--fail-on-regression",
            ],
        )

        assert result.exit_code == 0
        assert "No regressions detected" in result.output

    def test_compare_missing_baseline_file(self, tmp_path):
        """Test that compare command handles missing baseline file."""
        current_file = tmp_path / "current.jsonl"
        current_file.write_text("{}")

        result = runner.invoke(
            app,
            ["compare", "--baseline", "nonexistent.jsonl", "--current", str(current_file)],
        )

        assert result.exit_code != 0

    def test_compare_shows_in_help(self):
        """Test that compare command appears in help output."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "compare" in result.output


class TestCliApp:
    """Tests for the CLI app itself."""

    def test_no_args_shows_help(self):
        """Test that running without args shows help."""
        result = runner.invoke(app, [])

        # Typer may return exit code 0 or 2 for help, both are acceptable
        assert result.exit_code in [0, 2]
        assert "Voice AI observability toolkit" in result.output
        # Typer may show "Usage:" or "Commands:" depending on version
        assert "Usage:" in result.output or "Commands:" in result.output
        assert "version" in result.output
        assert "demo" in result.output
        assert "doctor" in result.output

    def test_help_flag_shows_help(self):
        """Test that --help flag shows help."""
        result = runner.invoke(app, ["--help"])

        # Typer returns exit code 0 for --help
        assert result.exit_code == 0
        assert "Voice AI observability toolkit" in result.output
        assert "Commands:" in result.output or "Usage:" in result.output

    def test_invalid_command_shows_error(self):
        """Test that invalid command shows error."""
        result = runner.invoke(app, ["invalid-command"])

        # The main assertion is that exit code is non-zero (indicates error)
        assert result.exit_code != 0
        # Check output for error indicators (stderr may not be separately captured)
        output = result.output
        # If there's output, verify it contains some indication of error
        # If no output, the non-zero exit code is sufficient proof of error
        if output.strip():
            error_indicators = [
                "No such command",
                "Error",
                "Unknown command",
                "Invalid value",
                "invalid-command",  # Command name might appear in error
            ]
            assert any(indicator in output for indicator in error_indicators)

    def test_main_entry_point(self):
        """Test that the module can be run as a script (if __name__ == '__main__')."""
        # Test that app is callable (which is what __main__ does)
        assert callable(app)

        # Verify the module has the expected structure
        import voiceobs.cli

        assert hasattr(voiceobs.cli, "app")
        assert callable(voiceobs.cli.app)

        # Test the actual __main__ branch by running as subprocess with --help
        # This ensures 100% coverage of the if __name__ == "__main__" block
        # We use --help to avoid hanging (since app() would normally wait for input)
        result = subprocess.run(
            [sys.executable, "-m", "voiceobs.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Should succeed and show help
        assert result.returncode == 0
        assert "Voice AI observability toolkit" in result.stdout


class TestInitCommand:
    """Tests for the init command."""

    def test_init_creates_config_file(self, tmp_path):
        """Test that init command creates a config file."""
        config_path = tmp_path / "voiceobs.yaml"

        result = runner.invoke(app, ["init", "--path", str(config_path)])

        assert result.exit_code == 0
        assert config_path.exists()
        assert "Created config file:" in result.output

    def test_init_generates_valid_yaml(self, tmp_path):
        """Test that init command generates valid YAML."""
        import yaml

        config_path = tmp_path / "voiceobs.yaml"

        result = runner.invoke(app, ["init", "--path", str(config_path)])

        assert result.exit_code == 0
        content = config_path.read_text()
        parsed = yaml.safe_load(content)
        assert "exporters" in parsed
        assert "failures" in parsed
        assert "regression" in parsed
        assert "eval" in parsed

    def test_init_fails_if_file_exists(self, tmp_path):
        """Test that init fails if config file already exists."""
        config_path = tmp_path / "voiceobs.yaml"
        config_path.write_text("existing: content")

        result = runner.invoke(app, ["init", "--path", str(config_path)])

        assert result.exit_code == 1
        assert "Config file already exists" in result.output
        assert "Use --force to overwrite" in result.output

    def test_init_force_overwrites_existing(self, tmp_path):
        """Test that init with --force overwrites existing config."""
        config_path = tmp_path / "voiceobs.yaml"
        config_path.write_text("existing: content")

        result = runner.invoke(app, ["init", "--force", "--path", str(config_path)])

        assert result.exit_code == 0
        content = config_path.read_text()
        assert "existing: content" not in content
        assert "exporters:" in content

    def test_init_creates_parent_directories(self, tmp_path):
        """Test that init creates parent directories if needed."""
        config_path = tmp_path / "subdir" / "nested" / "voiceobs.yaml"

        result = runner.invoke(app, ["init", "--path", str(config_path)])

        assert result.exit_code == 0
        assert config_path.exists()

    def test_init_shows_configuration_options(self, tmp_path):
        """Test that init shows available configuration options."""
        config_path = tmp_path / "voiceobs.yaml"

        result = runner.invoke(app, ["init", "--path", str(config_path)])

        assert result.exit_code == 0
        assert "Configuration options:" in result.output
        assert "exporters:" in result.output
        assert "failures:" in result.output
        assert "regression:" in result.output
        assert "eval:" in result.output

    def test_init_help_shows_examples(self):
        """Test that init --help shows usage examples."""
        result = runner.invoke(app, ["init", "--help"])

        assert result.exit_code == 0
        assert "voiceobs init" in result.output
        assert "--force" in result.output
        assert "--path" in result.output


class TestReportCommand:
    """Tests for the report command."""

    def test_report_generates_markdown_by_default(self, tmp_path):
        """Test that report command generates markdown by default."""
        import json

        # Create a JSONL file
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

        result = runner.invoke(app, ["report", "--input", str(input_file)])

        assert result.exit_code == 0
        assert "# voiceobs Analysis Report" in result.output
        assert "## Summary" in result.output
        assert "## Latency Breakdown" in result.output

    def test_report_generates_html_format(self, tmp_path):
        """Test that report command generates HTML when specified."""
        import json

        input_file = tmp_path / "run.jsonl"
        data = [
            {
                "name": "voice.turn",
                "duration_ms": 1000.0,
                "attributes": {"voice.actor": "agent"},
            },
        ]
        input_file.write_text(json.dumps(data[0]))

        result = runner.invoke(app, ["report", "--input", str(input_file), "--format", "html"])

        assert result.exit_code == 0
        assert "<html" in result.output
        assert "</html>" in result.output

    def test_report_saves_to_output_file(self, tmp_path):
        """Test that report command saves to output file when specified."""
        import json

        input_file = tmp_path / "run.jsonl"
        output_file = tmp_path / "report.md"
        data = [
            {
                "name": "voice.turn",
                "duration_ms": 1000.0,
                "attributes": {"voice.actor": "agent"},
            },
        ]
        input_file.write_text(json.dumps(data[0]))

        result = runner.invoke(
            app, ["report", "--input", str(input_file), "--output", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()
        assert "Report saved to:" in result.output
        content = output_file.read_text()
        assert "# voiceobs Analysis Report" in content

    def test_report_saves_html_to_output_file(self, tmp_path):
        """Test that report command saves HTML to output file."""
        import json

        input_file = tmp_path / "run.jsonl"
        output_file = tmp_path / "report.html"
        data = [
            {
                "name": "voice.turn",
                "duration_ms": 1000.0,
                "attributes": {"voice.actor": "agent"},
            },
        ]
        input_file.write_text(json.dumps(data[0]))

        result = runner.invoke(
            app,
            [
                "report",
                "--input",
                str(input_file),
                "--format",
                "html",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "<html" in content

    def test_report_with_custom_title(self, tmp_path):
        """Test that report command uses custom title."""
        import json

        input_file = tmp_path / "run.jsonl"
        data = [
            {
                "name": "voice.turn",
                "duration_ms": 1000.0,
                "attributes": {"voice.actor": "agent"},
            },
        ]
        input_file.write_text(json.dumps(data[0]))

        result = runner.invoke(
            app, ["report", "--input", str(input_file), "--title", "My Custom Report"]
        )

        assert result.exit_code == 0
        assert "# My Custom Report" in result.output

    def test_report_invalid_format_fails(self, tmp_path):
        """Test that report command fails with invalid format."""
        import json

        input_file = tmp_path / "run.jsonl"
        data = [{"name": "voice.turn", "duration_ms": 1000.0, "attributes": {}}]
        input_file.write_text(json.dumps(data[0]))

        result = runner.invoke(app, ["report", "--input", str(input_file), "--format", "pdf"])

        assert result.exit_code == 1
        assert "Invalid format" in result.output

    def test_report_missing_file_fails(self):
        """Test that report command fails when file is missing."""
        result = runner.invoke(app, ["report", "--input", "nonexistent.jsonl"])

        assert result.exit_code != 0

    def test_report_creates_parent_directories_for_output(self, tmp_path):
        """Test that report command creates parent directories for output."""
        import json

        input_file = tmp_path / "run.jsonl"
        output_file = tmp_path / "subdir" / "nested" / "report.md"
        data = [
            {
                "name": "voice.turn",
                "duration_ms": 1000.0,
                "attributes": {"voice.actor": "agent"},
            },
        ]
        input_file.write_text(json.dumps(data[0]))

        result = runner.invoke(
            app, ["report", "--input", str(input_file), "--output", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()

    def test_report_shows_in_help(self):
        """Test that report command appears in help output."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "report" in result.output

    def test_report_help_shows_options(self):
        """Test that report --help shows all options."""
        result = runner.invoke(app, ["report", "--help"])

        assert result.exit_code == 0
        assert "--input" in result.output
        assert "--format" in result.output
        assert "--output" in result.output
        assert "--title" in result.output
        assert "markdown" in result.output
        assert "html" in result.output
