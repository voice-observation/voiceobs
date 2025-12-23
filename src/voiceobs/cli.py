"""CLI entry point for voiceobs."""

import typer

app = typer.Typer(
    name="voiceobs",
    help="Voice AI observability toolkit",
    no_args_is_help=True,
)


@app.command()
def version():
    """Show the voiceobs version."""
    from voiceobs._version import __version__

    typer.echo(f"voiceobs {__version__}")


@app.command()
def demo():
    """Run a demo showing voice turn tracing."""
    typer.echo("Demo command coming soon...")


if __name__ == "__main__":
    app()
