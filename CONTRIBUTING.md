# Contributing to voiceobs

Thank you for your interest in contributing to voiceobs! This guide will help you get set up for development.

## Development Setup

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/voiceobs.git
   cd voiceobs
   ```

2. Install dependencies with uv:
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

### Running Tests

Run the full test suite:
```bash
uv run python -m pytest tests/ -v
```

Run tests with coverage:
```bash
uv run python -m pytest tests/ -v --cov=voiceobs --cov-report=term-missing
```

### Linting and Formatting

This project uses [ruff](https://docs.astral.sh/ruff/) for both linting and formatting.

**Check for linting issues:**
```bash
uv run ruff check src tests
```

**Auto-fix linting issues:**
```bash
uv run ruff check src tests --fix
```

**Check formatting:**
```bash
uv run ruff format --check src tests
```

**Auto-fix formatting:**
```bash
uv run ruff format src tests
```

### Before Committing

Run both linting and formatting checks:
```bash
uv run ruff check src tests && uv run ruff format --check src tests
```

Or fix everything automatically:
```bash
uv run ruff check src tests --fix && uv run ruff format src tests
```

Then run tests:
```bash
uv run python -m pytest tests/ -v
```

## Building the Package

Build distribution packages:
```bash
uv pip install build
uv run python -m build
```

This creates:
- `dist/voiceobs-x.x.x.tar.gz` (source distribution)
- `dist/voiceobs-x.x.x-py3-none-any.whl` (wheel)

## Testing the CLI

After installation, test the CLI:
```bash
# Run the demo
uv run voiceobs demo

# Check diagnostics
uv run voiceobs doctor

# Show version
uv run voiceobs version
```

## Project Structure

```
voiceobs/
├── src/voiceobs/          # Main package
│   ├── __init__.py        # Public API exports
│   ├── _version.py        # Version string
│   ├── context.py         # Conversation/turn context managers
│   ├── tracing.py         # OpenTelemetry initialization
│   └── cli.py             # Typer CLI commands
├── tests/                 # Test suite
│   ├── conftest.py        # Pytest fixtures
│   ├── test_context.py    # Context manager tests
│   ├── test_tracing.py    # Tracing tests
│   └── test_cli.py        # CLI tests
├── integrations/          # Integration examples
│   └── pipecat-examples/  # Pipecat integration
├── pyproject.toml         # Project configuration
└── CONTRIBUTING.md        # This file
```

## Code Style

- Use modern Python type hints (`X | None` instead of `Optional[X]`)
- Use `from __future__ import annotations` for forward references
- Follow PEP 8 naming conventions
- Keep functions focused and small
- Write docstrings for public APIs

## Submitting Changes

1. Create a new branch for your changes
2. Make your changes and add tests
3. Ensure all tests pass and linting is clean
4. Submit a pull request with a clear description

## Questions?

Open an issue on GitHub if you have questions or run into problems.
