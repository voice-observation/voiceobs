"""CLI entry point for voiceobs."""

import json
import time
from pathlib import Path

import typer

from voiceobs.config import PROJECT_CONFIG_NAME, generate_default_config

app = typer.Typer(
    name="voiceobs",
    help="Voice AI observability toolkit",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Show the voiceobs version."""
    from voiceobs._version import __version__

    typer.echo(f"voiceobs {__version__}")


@app.command()
def init(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing config file",
    ),
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Custom path for config file (default: ./voiceobs.yaml)",
    ),
) -> None:
    """Initialize a voiceobs configuration file.

    Creates a voiceobs.yaml file with default settings and helpful comments.
    The config file controls exporter settings, failure thresholds,
    regression detection, and LLM evaluator options.

    Example:
        voiceobs init
        voiceobs init --force
        voiceobs init --path ./config/voiceobs.yaml
    """
    config_path = path or Path.cwd() / PROJECT_CONFIG_NAME

    if config_path.exists() and not force:
        typer.echo(f"Config file already exists: {config_path}", err=True)
        typer.echo("Use --force to overwrite.", err=True)
        raise typer.Exit(1)

    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate and write config
    config_content = generate_default_config()
    config_path.write_text(config_content)

    typer.echo(f"Created config file: {config_path}")
    typer.echo()
    typer.echo("Configuration options:")
    typer.echo("  - exporters: Configure JSONL and console output")
    typer.echo("  - failures: Set detection thresholds")
    typer.echo("  - regression: Set comparison thresholds")
    typer.echo("  - eval: Configure LLM evaluator")
    typer.echo()
    typer.echo("Edit the file to customize settings for your project.")


@app.command()
def demo() -> None:
    """Run a demo showing voice turn tracing.

    Simulates a simple conversation with user and agent turns,
    emitting OpenTelemetry spans to the console.
    """
    from voiceobs import ensure_tracing_initialized, voice_conversation, voice_turn

    typer.echo("voiceobs Demo")
    typer.echo("=" * 50)
    typer.echo()
    typer.echo("Initializing tracing with ConsoleSpanExporter...")
    typer.echo()

    # Initialize tracing with console output
    initialized = ensure_tracing_initialized()
    if initialized:
        typer.echo("Tracing initialized by voiceobs (ConsoleSpanExporter)")
    else:
        typer.echo("Using existing tracing configuration")
    typer.echo()

    typer.echo("Simulating a voice conversation...")
    typer.echo("-" * 50)
    typer.echo()

    # Simulate a conversation
    with voice_conversation() as conv:
        typer.echo(f"Conversation started: {conv.conversation_id}")
        typer.echo()

        # User turn
        typer.echo("[User]: Hello, what's the weather like today?")
        with voice_turn("user"):
            time.sleep(0.1)  # Simulate processing time

        # Agent turn
        typer.echo("[Agent]: Let me check that for you...")
        with voice_turn("agent"):
            time.sleep(0.15)  # Simulate LLM/TTS processing

        # User turn
        typer.echo("[User]: Thanks! What about tomorrow?")
        with voice_turn("user"):
            time.sleep(0.1)

        # Agent turn
        typer.echo("[Agent]: Tomorrow looks sunny with highs around 72F.")
        with voice_turn("agent"):
            time.sleep(0.12)

    typer.echo()
    typer.echo("-" * 50)
    typer.echo("Conversation ended.")
    typer.echo()
    typer.echo("The spans above show the OpenTelemetry trace data.")
    typer.echo("Each voice.turn span includes:")
    typer.echo("  - voice.conversation.id")
    typer.echo("  - voice.turn.id")
    typer.echo("  - voice.turn.index")
    typer.echo("  - voice.actor (user/agent)")
    typer.echo("  - voice.schema.version")


@app.command()
def doctor() -> None:
    """Check OpenTelemetry configuration and voiceobs status.

    Prints diagnostic information about the current tracing setup.
    """
    from voiceobs import VOICE_SCHEMA_VERSION, __version__, get_tracer_provider_info

    typer.echo("voiceobs Doctor")
    typer.echo("=" * 50)
    typer.echo()

    # Version info
    typer.echo(f"voiceobs version: {__version__}")
    typer.echo(f"Schema version: {VOICE_SCHEMA_VERSION}")
    typer.echo()

    # Tracer provider info
    typer.echo("OpenTelemetry Status:")
    typer.echo("-" * 30)

    info = get_tracer_provider_info()

    typer.echo(f"  Provider type: {info['provider_type']}")
    typer.echo(f"  Is no-op: {info['is_noop']}")
    typer.echo(f"  Initialized by voiceobs: {info['voiceobs_initialized']}")
    typer.echo()

    # Status assessment
    if info["is_noop"]:
        typer.echo("Status: No tracing configured")
        typer.echo()
        typer.echo("To enable tracing, either:")
        typer.echo("  1. Call ensure_tracing_initialized() in your code")
        typer.echo("  2. Configure your own TracerProvider before using voiceobs")
        typer.echo()
        typer.echo("Quick start:")
        typer.echo("  from voiceobs import ensure_tracing_initialized")
        typer.echo("  ensure_tracing_initialized()")
    else:
        typer.echo("Status: Tracing is active")
        typer.echo()
        typer.echo("Spans will be exported via the configured provider.")

    typer.echo()
    typer.echo("Run 'voiceobs demo' to see tracing in action.")


@app.command()
def analyze(
    input_file: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help="Path to the JSONL file to analyze",
        exists=True,
        readable=True,
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON for machine processing",
    ),
) -> None:
    """Analyze a JSONL trace file and print latency metrics.

    Reads spans from a JSONL file and computes:
    - ASR / LLM / TTS latency percentiles
    - Average and p95 response latency (silence after user)
    - Interruption rate

    To enable JSONL export, configure it in voiceobs.yaml:
        exporters:
          jsonl:
            enabled: true
            path: "./run.jsonl"

    Example:
        voiceobs analyze --input run.jsonl
        voiceobs analyze --input run.jsonl --json
    """
    from voiceobs.analyzer import analyze_file

    try:
        result = analyze_file(input_file)
        if output_json:
            typer.echo(json.dumps(result.to_dict(), indent=2))
        else:
            typer.echo(result.format_report())
    except FileNotFoundError:
        typer.echo(f"Error: File not found: {input_file}", err=True)
        typer.echo("Hint: Check the file path and ensure the file exists.", err=True)
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in file: {input_file}", err=True)
        typer.echo(
            f"Hint: Ensure the file contains valid JSONL (one JSON object per line). Details: {e}",
            err=True,
        )
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error analyzing file: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def compare(
    baseline_file: Path = typer.Option(
        ...,
        "--baseline",
        "-b",
        help="Path to the baseline JSONL file",
        exists=True,
        readable=True,
    ),
    current_file: Path = typer.Option(
        ...,
        "--current",
        "-c",
        help="Path to the current JSONL file to compare",
        exists=True,
        readable=True,
    ),
    fail_on_regression: bool = typer.Option(
        False,
        "--fail-on-regression",
        help="Exit with non-zero code if regressions are detected",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON for machine processing",
    ),
) -> None:
    """Compare two JSONL trace files and detect regressions.

    Compares metrics between a baseline and current run, highlighting:
    - Latency deltas (ASR, LLM, TTS p95)
    - Response latency deltas (silence after user)
    - Interruption rate changes
    - Semantic score changes (intent correctness, relevance)

    Use --fail-on-regression in CI to fail the build on detected regressions.

    Example:
        voiceobs compare --baseline baseline.jsonl --current current.jsonl
        voiceobs compare -b baseline.jsonl -c current.jsonl --fail-on-regression
        voiceobs compare -b baseline.jsonl -c current.jsonl --json
    """
    from voiceobs.analyzer import analyze_file
    from voiceobs.compare import compare_runs

    try:
        baseline_result = analyze_file(baseline_file)
        current_result = analyze_file(current_file)

        comparison = compare_runs(
            baseline=baseline_result,
            current=current_result,
            baseline_file=str(baseline_file),
            current_file=str(current_file),
        )

        if output_json:
            typer.echo(json.dumps(comparison.to_dict(), indent=2))
        else:
            typer.echo(comparison.format_report())

        if fail_on_regression and comparison.has_regressions:
            typer.echo("Regression(s) detected. Failing build.", err=True)
            raise typer.Exit(1)

    except FileNotFoundError as e:
        typer.echo(f"Error: File not found: {e}", err=True)
        typer.echo("Hint: Check that both baseline and current files exist.", err=True)
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        typer.echo("Error: Invalid JSON in input file", err=True)
        typer.echo(f"Hint: Ensure files contain valid JSONL. Details: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error comparing files: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def report(
    input_file: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help="Path to the JSONL file to analyze",
        exists=True,
        readable=True,
    ),
    format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format: 'markdown', 'html', or 'json' (default: markdown)",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (prints to stdout if not specified)",
    ),
    title: str = typer.Option(
        None,
        "--title",
        "-t",
        help="Custom report title",
    ),
) -> None:
    """Generate a report from a JSONL trace file.

    Creates a formatted report with:
    - Summary (conversation count, turn count, span count)
    - Latency breakdown (ASR/LLM/TTS p50/p95/p99)
    - Failure summary by type and severity
    - Semantic evaluation summary (if available)
    - Recommendations based on detected issues

    The report can be output as markdown (for terminal/GitHub),
    HTML (self-contained, suitable for sharing via email/Slack),
    or JSON (for machine processing and automation).

    Example:
        voiceobs report --input run.jsonl
        voiceobs report --input run.jsonl --format html --output report.html
        voiceobs report -i run.jsonl -f markdown -o report.md
        voiceobs report -i run.jsonl -f json
    """
    from voiceobs.analyzer import analyze_file
    from voiceobs.report import generate_report_from_file

    # Validate format
    valid_formats = ("markdown", "html", "json")
    if format not in valid_formats:
        typer.echo(
            f"Error: Invalid format '{format}'. Use 'markdown', 'html', or 'json'.",
            err=True,
        )
        raise typer.Exit(1)

    try:
        # Handle JSON format separately (uses analyzer directly)
        if format == "json":
            result = analyze_file(input_file)
            report_content = json.dumps(result.to_dict(), indent=2)
        else:
            report_content = generate_report_from_file(
                input_file,
                format=format,  # type: ignore[arg-type]
                title=title,
            )

        if output:
            # Ensure parent directory exists
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(report_content)
            typer.echo(f"Report saved to: {output}")
        else:
            typer.echo(report_content)

    except FileNotFoundError:
        typer.echo(f"Error: File not found: {input_file}", err=True)
        typer.echo("Hint: Check the file path and ensure the file exists.", err=True)
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in file: {input_file}", err=True)
        typer.echo(f"Hint: Ensure the file contains valid JSONL. Details: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error generating report: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def server(
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Host to bind the server to",
    ),
    port: int = typer.Option(
        8765,
        "--port",
        "-p",
        help="Port to bind the server to",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        help="Enable auto-reload for development",
    ),
) -> None:
    """Start the voiceobs REST API server.

    Starts a FastAPI server that accepts spans via HTTP and provides
    analysis endpoints. Use this to integrate voiceobs with external
    tools or build custom dashboards.

    Example:
        voiceobs server
        voiceobs server --port 9000
        voiceobs server --host 0.0.0.0 --port 8080 --reload
    """
    try:
        import uvicorn
    except ImportError:
        typer.echo(
            "Error: Server dependencies not installed.",
            err=True,
        )
        typer.echo(
            "Hint: Install with: pip install voiceobs[server]",
            err=True,
        )
        raise typer.Exit(1)

    from voiceobs._version import __version__

    typer.echo(f"Starting voiceobs server v{__version__}")
    typer.echo(f"  Host: {host}")
    typer.echo(f"  Port: {port}")
    typer.echo(f"  Reload: {reload}")
    typer.echo()
    typer.echo(f"API docs: http://{host}:{port}/docs")
    typer.echo(f"Health check: http://{host}:{port}/health")
    typer.echo()

    uvicorn.run(
        "voiceobs.server.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


if __name__ == "__main__":
    app()
