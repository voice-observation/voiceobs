"""CLI entry point for voiceobs."""

import time

import typer

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


if __name__ == "__main__":
    app()
