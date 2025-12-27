# CLAUDE.md - Development Guidelines for voiceobs

## Test-Driven Development (TDD)

All code changes MUST follow TDD:

1. **Write tests first** - Before implementing, write failing tests that define expected behavior
2. **Run tests to see them fail** - Verify tests fail for the right reason
3. **Implement minimum code** - Write just enough code to make tests pass
4. **Refactor** - Clean up while keeping tests green

## After Completing Any Task

Always run these commands in order:

```bash
# 1. Lint and auto-fix issues
uv run ruff check src/voiceobs/ --fix
uv run ruff check tests/ --fix

# 2. Run all unit tests (must pass)
uv run python -m pytest tests/ -v

# 3. Check coverage for new code (must be >95%)
uv run python -m pytest tests/ --cov=src/voiceobs --cov-report=term-missing --cov-branch
```

## Coverage Requirements

New code changes MUST have:
- **Line coverage: >95%**
- **Branch coverage: >95%**

To check coverage for a specific module:
```bash
uv run python -m pytest tests/ --cov=src/voiceobs/<module>.py --cov-report=term-missing --cov-branch
```

## Code Style

- Type hints required for all public functions
- Docstrings required for all public classes and functions
- Use `unittest.mock.patch` for mocking dependencies
