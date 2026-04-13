# Contributing

## Setup

```bash
git clone https://github.com/funky-ai/codename-generator.git
cd codename-generator
uv sync
```

## Development

```bash
uv run pytest tests/ -v              # Run tests
uv run ruff check src/ tests/        # Lint
uv run ruff format src/ tests/       # Format
uv run fastmcp dev src/codename_generator/server.py  # MCP Inspector
```

## Code Style

- Linted with [ruff](https://docs.astral.sh/ruff/) (rules: E, F, I)
- Type hints required on all function signatures
- Pydantic models for all input/output types

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add batch delete tool
fix: handle empty search query
docs: update README tool table
refactor: extract migrations to separate module
```

## Architecture

See [CLAUDE.md](CLAUDE.md) for project architecture and conventions.

## Tests

- Write tests in `tests/test_core.py`
- Use `tmp_path` fixture for database isolation
- Organize tests in classes by feature
- Cover both success paths and error cases
