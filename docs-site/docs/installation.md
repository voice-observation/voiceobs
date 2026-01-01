# Installation

## Requirements

- Python 3.10 or higher

## Basic Installation

Install voiceobs from PyPI:

```bash
pip install voiceobs
```

## Optional Dependencies

### Server Support

To use the REST API server:

```bash
pip install voiceobs[server]
```

This includes:
- FastAPI for the web framework
- SQLAlchemy and Alembic for database migrations
- PostgreSQL drivers (asyncpg, psycopg2-binary)

### Evaluation Support

To use semantic evaluation features:

```bash
pip install voiceobs[eval]
```

This includes:
- LangChain for LLM integration
- LangChain providers for OpenAI, Anthropic, and Google Gemini

## Verify Installation

Check that voiceobs is installed correctly:

```bash
voiceobs --version
```

You should see the version number (e.g., `0.0.2`).

## Quick Test

Run the demo to verify everything works:

```bash
voiceobs demo
```

This simulates a 4-turn conversation and prints the spans to the console.

## Next Steps

- [Overview](./overview.md)
- [Learn about configuration](./guides/configuration.md)
