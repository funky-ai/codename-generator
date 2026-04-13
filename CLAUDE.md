# codename-generator

## Project Overview

Python 3.12 MCP server for managing project codenames. Built with FastMCP + Pydantic + SQLite.

- Package manager: **uv**
- Current version: 0.0.4
- License: Apache 2.0

## Architecture

Four-layer architecture in `src/codename_generator/`:

| Layer | File | Responsibility |
|-------|------|---------------|
| MCP Interface | `server.py` | FastMCP tool definitions, MCP entry point |
| Business Logic | `core.py` | `CodenameManager` class, all domain rules |
| Data Access | `db.py` | SQLite schema, migrations, CRUD operations |
| Data Models | `models.py` | Pydantic input/output schemas |

- Data directory: `data/codenames.db` (gitignored, runtime data)
- Two themes: `person` (with `sub_theme`) and `animal`
- All IDs use CSPRNG (`secrets` module): `CN-xxxxxxxx`, `ASN-xxxxxxxx`

## Development Commands

```bash
uv sync                                              # Install dependencies
uv run pytest tests/ -v                              # Run tests
uv run fastmcp dev src/codename_generator/server.py  # Run MCP Inspector
uv run python -m codename_generator                  # Run server directly
```

## Code Conventions

- Database connections opened/closed per method call in `CodenameManager`
- SQLite with WAL mode and foreign keys enabled
- Migrations are idempotent functions in `db.py`
- Pydantic models for all input/output types
- Type hints required on all function signatures

## Testing Conventions

- Tests in `tests/test_core.py` using pytest
- Use `tmp_path` fixture for database isolation
- Organize tests in classes by feature (`TestAddCodenames`, `TestAssignCodename`, etc.)
- Helper functions for common setup (e.g., `_add_one`)
- Test both success paths and error cases (`ValueError` assertions)

## Workflow Commands

Available engineering workflows (invoke with `/workflow-*`):

| Command | When to Use |
|---------|-------------|
| `/workflow-feature` | New tool, new model, new MCP prompt, new feature |
| `/workflow-bugfix` | Bug report, test failure, unexpected behavior |
| `/workflow-incident` | MCP server crash, data corruption, production issue |
| `/workflow-release` | Ready to tag a new version, publish changelog |
| `/workflow-health` | Periodic review, refactoring session, debt assessment |
| `/workflow-standup` | Start of work session, progress summary |

## Git Conventions

- Conventional commit-style messages
- Version bumps: update `pyproject.toml` version field
- Changelog: update both `CHANGELOG.md` and `CHANGELOG-zh.md`
- Bilingual documentation: maintain English and Chinese versions
