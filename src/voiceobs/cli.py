"""CLI entry point for voiceobs."""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

import typer

from voiceobs.config import PROJECT_CONFIG_NAME, generate_default_config
from voiceobs.server.db.connection import Database
from voiceobs.server.db.repositories import ConversationRepository, SpanRepository

app = typer.Typer(
    name="voiceobs",
    help="Voice AI observability toolkit",
    no_args_is_help=True,
)

# Database subcommand group
db_app = typer.Typer(
    name="db",
    help="Database management commands",
    no_args_is_help=True,
)
app.add_typer(db_app, name="db")

# Export subcommand group (for otlp export)
export_app = typer.Typer(
    name="export",
    help="Export spans to various formats",
    no_args_is_help=False,  # Allow no subcommand for backward compatibility
)
app.add_typer(export_app, name="export")


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


def import_spans_to_db(
    input_file: Path,
    database_url: str,
) -> dict[str, Any]:
    """Import spans from a JSONL file to the database.

    Args:
        input_file: Path to the JSONL file.
        database_url: Database URL to connect to.

    Returns:
        Dictionary with import results.
    """

    async def _import() -> dict[str, Any]:
        db = Database(database_url=database_url)
        await db.connect()
        await db.init_schema()

        span_repo = SpanRepository(db)
        conv_repo = ConversationRepository(db)

        imported = 0
        errors = 0

        with open(input_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    span_data = json.loads(line)
                    attrs = span_data.get("attributes", {})
                    conversation_id = None

                    # Auto-create conversation if span has conversation ID
                    conv_external_id = attrs.get("voice.conversation.id")
                    if conv_external_id:
                        conv = await conv_repo.get_or_create(conv_external_id)
                        conversation_id = conv.id

                    await span_repo.add(
                        name=span_data.get("name", "unknown"),
                        start_time=span_data.get("start_time"),
                        end_time=span_data.get("end_time"),
                        duration_ms=span_data.get("duration_ms"),
                        attributes=attrs,
                        trace_id=span_data.get("trace_id"),
                        span_id=span_data.get("span_id"),
                        parent_span_id=span_data.get("parent_span_id"),
                        conversation_id=conversation_id,
                    )
                    imported += 1
                except Exception:
                    errors += 1

        await db.disconnect()
        return {"imported": imported, "errors": errors}

    return asyncio.run(_import())


def export_spans_from_db(
    database_url: str,
    output_file: Path | None = None,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Export spans from the database to a JSONL file.

    Args:
        database_url: Database URL to connect to.
        output_file: Path to write the JSONL file. If None, returns spans.
        conversation_id: Optional conversation ID to filter by.

    Returns:
        Dictionary with export results.
    """

    async def _export() -> dict[str, Any]:
        db = Database(database_url=database_url)
        await db.connect()

        span_repo = SpanRepository(db)
        conv_repo = ConversationRepository(db)

        if conversation_id:
            # Find conversation by external ID
            conv = await conv_repo.get_by_external_id(conversation_id)
            if conv:
                spans = await span_repo.get_by_conversation(conv.id)
            else:
                spans = []
        else:
            spans = await span_repo.get_all()

        # Convert to dicts
        span_dicts = []
        for span in spans:
            span_dict = {
                "name": span.name,
                "start_time": span.start_time,
                "end_time": span.end_time,
                "duration_ms": span.duration_ms,
                "attributes": span.attributes,
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "parent_span_id": span.parent_span_id,
            }
            span_dicts.append(span_dict)

        await db.disconnect()

        if output_file:
            with open(output_file, "w") as f:
                for span_dict in span_dicts:
                    f.write(json.dumps(span_dict) + "\n")
            return {"exported": len(span_dicts), "path": str(output_file)}
        else:
            return {"exported": len(span_dicts), "spans": span_dicts}

    return asyncio.run(_export())


# Database commands
@db_app.command("migrate")
def db_migrate(
    revision: str = typer.Option(
        "head",
        "--revision",
        "-r",
        help="Target revision (default: head)",
    ),
) -> None:
    """Run database migrations.

    Applies pending migrations to bring the database to the target revision.

    Example:
        voiceobs db migrate
        voiceobs db migrate --revision abc123
    """
    database_url = _get_database_url()
    if not database_url:
        typer.echo("Error: No database URL configured.", err=True)
        typer.echo(
            "Hint: Set VOICEOBS_DATABASE_URL or configure server.database_url in voiceobs.yaml",
            err=True,
        )
        raise typer.Exit(1)

    try:
        from voiceobs.server.db.migrations import run_migrations

        typer.echo(f"Running migrations to revision: {revision}")
        result = run_migrations(database_url=database_url, revision=revision)

        if result["success"]:
            typer.echo("Migrations completed successfully.")
        else:
            typer.echo(f"Error running migrations: {result.get('error')}", err=True)
            raise typer.Exit(1)

    except ImportError:
        typer.echo("Error: Server dependencies not installed.", err=True)
        typer.echo("Hint: Install with: pip install voiceobs[server]", err=True)
        raise typer.Exit(1)


@db_app.command("status")
def db_status() -> None:
    """Show database migration status.

    Displays the current revision and any pending migrations.

    Example:
        voiceobs db status
    """
    database_url = _get_database_url()
    if not database_url:
        typer.echo("Error: No database URL configured.", err=True)
        typer.echo(
            "Hint: Set VOICEOBS_DATABASE_URL or configure server.database_url in voiceobs.yaml",
            err=True,
        )
        raise typer.Exit(1)

    try:
        from voiceobs.server.db.migrations import (
            get_current_revision,
            get_pending_migrations,
        )

        current = get_current_revision(database_url)
        pending = get_pending_migrations(database_url)

        typer.echo("Database Migration Status")
        typer.echo("=" * 40)
        typer.echo()
        typer.echo(f"Current revision: {current or '(none)'}")

        if pending:
            typer.echo(f"Pending migrations: {len(pending)}")
            for rev in pending:
                typer.echo(f"  - {rev}")
        else:
            typer.echo("Status: Database is up to date")

    except ImportError:
        typer.echo("Error: Server dependencies not installed.", err=True)
        typer.echo("Hint: Install with: pip install voiceobs[server]", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error checking status: {e}", err=True)
        raise typer.Exit(1)


@db_app.command("history")
def db_history() -> None:
    """Show migration history.

    Lists all available migrations in the project.

    Example:
        voiceobs db history
    """
    try:
        from voiceobs.server.db.migrations import get_migration_history

        history = get_migration_history()

        typer.echo("Migration History")
        typer.echo("=" * 40)
        typer.echo()

        if history:
            for migration in history:
                typer.echo(f"  {migration['revision']}: {migration['description']}")
        else:
            typer.echo("No migrations found.")

    except ImportError:
        typer.echo("Error: Server dependencies not installed.", err=True)
        typer.echo("Hint: Install with: pip install voiceobs[server]", err=True)
        raise typer.Exit(1)


# Import command
@app.command("import")
def import_command(
    input_file: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help="Path to the JSONL file to import",
        exists=True,
        readable=True,
    ),
) -> None:
    """Import spans from a JSONL file to the database.

    Reads span data from a JSONL file and stores it in the database.
    Automatically creates conversations for spans with voice.conversation.id.

    Example:
        voiceobs import --input run.jsonl
    """
    database_url = _get_database_url()
    if not database_url:
        typer.echo("Error: No database URL configured.", err=True)
        typer.echo(
            "Hint: Set VOICEOBS_DATABASE_URL or configure server.database_url in voiceobs.yaml",
            err=True,
        )
        raise typer.Exit(1)

    try:
        typer.echo(f"Importing spans from: {input_file}")
        result = import_spans_to_db(input_file, database_url)

        typer.echo(f"Imported {result['imported']} spans")
        if result["errors"] > 0:
            typer.echo(f"Errors: {result['errors']}", err=True)

    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON in file: {input_file}", err=True)
        typer.echo(f"Details: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error importing spans: {e}", err=True)
        raise typer.Exit(1)


# Default export command (backward compatibility - exports JSONL)
@export_app.callback(invoke_without_command=True)
def export_callback(
    ctx: typer.Context,
    output_file: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Path to write the JSONL file (prints to stdout if not specified)",
    ),
    conversation: str = typer.Option(
        None,
        "--conversation",
        "-c",
        help="Filter by conversation ID",
    ),
) -> None:
    """Export spans from the database to a JSONL file.

    This is the default export command for backward compatibility.
    Use 'voiceobs export jsonl' for explicit JSONL export, or
    'voiceobs export otlp' for OTLP export.
    """
    # If a subcommand was invoked, don't run this
    if ctx.invoked_subcommand is not None:
        return

    # Otherwise, run the JSONL export
    export_jsonl_impl(output_file, conversation)


def export_jsonl_impl(
    output_file: Path | None = None,
    conversation: str | None = None,
) -> None:
    """Implementation of JSONL export (shared by callback and jsonl command)."""
    database_url = _get_database_url()
    if not database_url:
        typer.echo("Error: No database URL configured.", err=True)
        typer.echo(
            "Hint: Set VOICEOBS_DATABASE_URL or configure server.database_url in voiceobs.yaml",
            err=True,
        )
        raise typer.Exit(1)

    try:
        result = export_spans_from_db(
            database_url=database_url,
            output_file=output_file,
            conversation_id=conversation,
        )

        if output_file:
            typer.echo(f"Exported {result['exported']} spans to: {output_file}")
        else:
            # Print to stdout
            for span in result.get("spans", []):
                typer.echo(json.dumps(span))

    except Exception as e:
        typer.echo(f"Error exporting spans: {e}", err=True)
        raise typer.Exit(1)


# Export JSONL command (explicit subcommand)
@export_app.command("jsonl")
def export_jsonl_command(
    output_file: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Path to write the JSONL file (prints to stdout if not specified)",
    ),
    conversation: str = typer.Option(
        None,
        "--conversation",
        "-c",
        help="Filter by conversation ID",
    ),
) -> None:
    """Export spans from the database to a JSONL file.

    Reads span data from the database and writes it to a JSONL file
    or stdout if no output file is specified.

    Example:
        voiceobs export jsonl --output run.jsonl
        voiceobs export jsonl --conversation conv-123 --output run.jsonl
        voiceobs export jsonl
    """
    export_jsonl_impl(output_file, conversation)


def _validate_otlp_export_args(
    input_file: Path | None, server: bool, conversation: str | None
) -> None:
    """Validate arguments for OTLP export command.

    Args:
        input_file: Path to JSONL file (optional).
        server: Whether to export from server database.
        conversation: Conversation ID filter (optional).

    Raises:
        typer.Exit: If validation fails.
    """
    if not server and not input_file:
        typer.echo(
            "Error: Either --input or --server must be specified.",
            err=True,
        )
        raise typer.Exit(1)

    if server and input_file:
        typer.echo(
            "Error: Cannot use both --input and --server.",
            err=True,
        )
        raise typer.Exit(1)

    if conversation and not server:
        typer.echo(
            "Error: --conversation can only be used with --server.",
            err=True,
        )
        raise typer.Exit(1)


def _get_otlp_exporter_config(
    endpoint: str | None, protocol: str | None
) -> tuple[str, str, dict[str, str], int, int, int]:
    """Get OTLP exporter configuration, merging CLI overrides with config.

    Args:
        endpoint: CLI endpoint override (optional).
        protocol: CLI protocol override (optional).

    Returns:
        Tuple of (endpoint, protocol, headers, batch_size, batch_timeout_ms, max_retries).
    """
    from voiceobs.config import get_config

    config = get_config()
    otlp_config = config.exporters.otlp

    endpoint_url = endpoint or otlp_config.endpoint
    protocol_type = protocol or otlp_config.protocol
    headers = otlp_config.headers.copy()

    return (
        endpoint_url,
        protocol_type,
        headers,
        otlp_config.batch_size,
        otlp_config.batch_timeout_ms,
        otlp_config.max_retries,
    )


def _load_spans_from_jsonl(input_file: Path) -> list[dict[str, Any]]:
    """Load spans from a JSONL file.

    Args:
        input_file: Path to JSONL file.

    Returns:
        List of span dictionaries.

    Raises:
        FileNotFoundError: If file doesn't exist.
    """
    spans: list[dict[str, Any]] = []

    with open(input_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                span_data = json.loads(line)
                spans.append(span_data)
            except json.JSONDecodeError as e:
                typer.echo(
                    f"Warning: Skipping invalid JSON line: {e}",
                    err=True,
                )

    typer.echo(f"Loaded {len(spans)} spans from {input_file}")
    return spans


def _load_spans_from_database(conversation_id: str | None) -> list[dict[str, Any]]:
    """Load spans from the server database.

    Args:
        conversation_id: Optional conversation ID to filter by.

    Returns:
        List of span dictionaries.

    Raises:
        typer.Exit: If database URL is not configured.
    """
    database_url = _get_database_url()
    if not database_url:
        typer.echo("Error: No database URL configured.", err=True)
        typer.echo(
            "Hint: Set VOICEOBS_DATABASE_URL or configure " "server.database_url in voiceobs.yaml",
            err=True,
        )
        raise typer.Exit(1)

    result = export_spans_from_db(
        database_url=database_url,
        output_file=None,  # Get spans as dicts
        conversation_id=conversation_id,
    )
    spans = result.get("spans", [])
    typer.echo(f"Loaded {len(spans)} spans from database")
    return spans


def _convert_span_dicts_to_otel_spans(
    span_dicts: list[dict[str, Any]],
) -> list[Any]:
    """Convert span dictionaries to OpenTelemetry ReadableSpan objects.

    Args:
        span_dicts: List of span dictionaries from JSONL or database.

    Returns:
        List of OpenTelemetry ReadableSpan objects.
    """
    from collections.abc import Sequence

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExportResult
    from opentelemetry.trace import SpanContext, Status, StatusCode, TraceFlags

    # Create a provider and collect spans
    provider = TracerProvider()
    collected: list[Any] = []

    class Collector:
        def export(self, spans: Sequence[Any]) -> Any:
            collected.extend(spans)
            return SpanExportResult.SUCCESS

        def shutdown(self) -> None:
            pass

        def force_flush(self, timeout_millis: int = 30000) -> bool:
            return True

    provider.add_span_processor(SimpleSpanProcessor(Collector()))
    tracer = provider.get_tracer("voiceobs.export")

    # Create spans by replaying them
    for span_dict in span_dicts:
        try:
            trace_id_hex = span_dict.get("trace_id", "0" * 32)
            span_id_hex = span_dict.get("span_id", "0" * 16)

            trace_id = int(trace_id_hex, 16)
            span_id = int(span_id_hex, 16)

            ctx = trace.set_span_in_context(
                trace.NonRecordingSpan(
                    SpanContext(
                        trace_id=trace_id,
                        span_id=span_id,
                        is_remote=False,
                        trace_flags=TraceFlags(0x01),
                    )
                )
            )

            with tracer.start_as_current_span(
                name=span_dict.get("name", "unknown"), context=ctx
            ) as span:
                # Set attributes
                for key, value in span_dict.get("attributes", {}).items():
                    span.set_attribute(key, value)

                # Set status
                status_data = span_dict.get("status", {})
                status_code = status_data.get("status_code", "UNSET")
                if status_code == "ERROR":
                    span.set_status(Status(StatusCode.ERROR, status_data.get("description")))
                elif status_code == "OK":
                    span.set_status(Status(StatusCode.OK, status_data.get("description")))

                # Override timestamps
                if start_time := span_dict.get("start_time_ns"):
                    span.start_time = start_time
                if end_time := span_dict.get("end_time_ns"):
                    span.end_time = end_time

        except (ValueError, KeyError) as e:
            typer.echo(
                f"Warning: Skipping invalid span: {e}",
                err=True,
            )
            continue

    return collected


def _export_spans_to_otlp(exporter: Any, spans: list[Any], endpoint_url: str) -> None:
    """Export spans to OTLP endpoint.

    Args:
        exporter: OTLPSpanExporter instance.
        spans: List of OpenTelemetry spans to export.
        endpoint_url: OTLP endpoint URL (for logging).

    Raises:
        typer.Exit: If export fails.
    """
    from opentelemetry.sdk.trace.export import SpanExportResult

    typer.echo(f"Exporting {len(spans)} spans to {endpoint_url}...")
    result = exporter.export(spans)
    exporter.force_flush()
    exporter.shutdown()

    if result == SpanExportResult.SUCCESS:
        typer.echo(f"Successfully exported {len(spans)} spans to OTLP endpoint")
    else:
        typer.echo("Error: Failed to export spans to OTLP endpoint", err=True)
        raise typer.Exit(1)


@export_app.command("otlp")
def export_otlp_command(
    input_file: Path = typer.Option(
        None,
        "--input",
        "-i",
        help="Path to JSONL file to export (required if --server not used)",
        exists=True,
        readable=True,
    ),
    server: bool = typer.Option(
        False,
        "--server",
        help="Export from server database instead of JSONL file",
    ),
    endpoint: str = typer.Option(
        None,
        "--endpoint",
        "-e",
        help="OTLP endpoint URL (overrides config)",
    ),
    protocol: str = typer.Option(
        None,
        "--protocol",
        "-p",
        help="Protocol: 'grpc' or 'http/protobuf' (overrides config)",
    ),
    conversation: str = typer.Option(
        None,
        "--conversation",
        "-c",
        help="Filter by conversation ID (only with --server)",
    ),
) -> None:
    """Export spans to an OpenTelemetry-compatible backend via OTLP.

    Exports spans from a JSONL file or from the server database to any
    OTLP-compatible backend (Grafana, Datadog, etc.).

    Configuration is read from voiceobs.yaml, but can be overridden
    with command-line options.

    Example:
        # Export from JSONL file
        voiceobs export otlp --input run.jsonl

        # Export from server database
        voiceobs export otlp --server

        # Override endpoint and protocol
        voiceobs export otlp --input run.jsonl --endpoint http://localhost:4317 --protocol grpc

        # Export specific conversation from server
        voiceobs export otlp --server --conversation conv-123
    """
    try:
        from voiceobs.exporters.otlp import OTLPSpanExporter
    except ImportError:
        typer.echo(
            "Error: OTLP exporter dependencies not installed.",
            err=True,
        )
        typer.echo(
            "Hint: Install with: pip install voiceobs[otlp]",
            err=True,
        )
        raise typer.Exit(1)

    # Validate arguments
    _validate_otlp_export_args(input_file, server, conversation)

    # Get configuration
    (
        endpoint_url,
        protocol_type,
        headers,
        batch_size,
        batch_timeout_ms,
        max_retries,
    ) = _get_otlp_exporter_config(endpoint, protocol)

    try:
        # Create OTLP exporter
        exporter = OTLPSpanExporter(
            endpoint=endpoint_url,
            protocol=protocol_type,
            headers=headers,
            batch_size=batch_size,
            batch_timeout_ms=batch_timeout_ms,
            max_retries=max_retries,
        )

        # Load spans
        if server:
            span_dicts = _load_spans_from_database(conversation)
        else:
            span_dicts = _load_spans_from_jsonl(input_file)

        if not span_dicts:
            typer.echo("No spans to export.")
            return

        # Convert to OpenTelemetry spans
        otlp_spans = _convert_span_dicts_to_otel_spans(span_dicts)

        # Export to OTLP
        _export_spans_to_otlp(exporter, otlp_spans, endpoint_url)

    except FileNotFoundError:
        typer.echo(f"Error: File not found: {input_file}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error exporting to OTLP: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
