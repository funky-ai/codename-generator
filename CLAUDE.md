# codename-generator

## Project Overview

Python 3.12 MCP server + Web UI for managing project codenames. Built with FastMCP + FastAPI + Pydantic + SQLite.

- Package manager: **uv** (Python), **pnpm** (frontend)
- Current version: 0.0.5
- License: Apache 2.0

## Architecture

Five-layer architecture in `src/codename_generator/`:

| Layer | File | Responsibility |
|-------|------|---------------|
| MCP Interface | `server.py` | FastMCP tool definitions, MCP entry point |
| REST Interface | `api.py` | FastAPI REST API, Web frontend serving |
| Business Logic | `core.py` | `CodenameManager` class, all domain rules |
| Data Access | `db.py` | SQLite schema, migrations, CRUD operations |
| Data Models | `models.py` | Pydantic input/output schemas |

Frontend source in `web/` (Vite + React + TypeScript + shadcn/ui), build output in `src/codename_generator/static/`.

- Data directory: `data/codenames.db` (gitignored, runtime data)
- Two themes: `person` (with `sub_theme`) and `animal`
- All IDs use CSPRNG (`secrets` module): `CN-xxxxxxxx`, `ASN-xxxxxxxx`

## Development Commands

```bash
uv sync                                              # Install Python dependencies
uv run pytest tests/ -v                              # Run tests
uv run fastmcp dev src/codename_generator/server.py  # Run MCP Inspector
uv run python -m codename_generator                  # Run MCP server
uv run python -m codename_generator web              # Run Web server (:8000)
uv run python -m codename_generator web --port 3000  # Web server on custom port

# Frontend development
cd web && pnpm install                               # Install frontend dependencies
cd web && pnpm dev                                   # Vite dev server (proxy to :8000)
cd web && pnpm build                                 # Build to static/
```

## Code Conventions

- Database connections opened/closed per method call in `CodenameManager`
- SQLite with WAL mode and foreign keys enabled
- Migrations are idempotent functions in `db.py`
- Pydantic models for all input/output types
- Type hints required on all function signatures
- Docstrings required on all public functions (match `server.py` and `core.py` coverage)
- Environment-sensitive config (CORS, host, port, DB path) must be configurable via env vars, never hardcoded for a single scenario
- Every `import` must have a corresponding explicit entry in `pyproject.toml` dependencies — transitive deps don't count

## Testing Conventions

- Tests in `tests/test_core.py` (business logic) and `tests/test_api.py` (REST API)
- Use `tmp_path` fixture for database isolation
- API tests use `monkeypatch.setenv` + singleton reset for DB isolation
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

## Workflow Guardrails

These rules supplement `/workflow-feature` to prevent known quality gaps (ref: 2026-04-13 incident postmortem).

### Code Review — Full-stack scope
- Python: security, performance, correctness, docstrings
- Frontend (`web/`): audit `package.json` for unused dependencies, check consistency with backend patterns
- Cross-layer: verify all imports have explicit dependency declarations

### Documentation — Mandatory checklist
Every feature must check and update these files (if applicable):
- [ ] `README.md` + `README-zh.md`
- [ ] `CHANGELOG.md` + `CHANGELOG-zh.md`
- [ ] `CONTRIBUTING.md` + `CONTRIBUTING-zh.md`
- [ ] `CLAUDE.md`
- [ ] Docstrings on all new public functions

### Deploy Checklist — Dependency audit
- [ ] `grep -r "^import\|^from" src/` — every third-party package listed in `pyproject.toml` dependencies?
- [ ] `web/package.json` — every dependency actually imported somewhere in `web/src/`?
- [ ] No hardcoded config that should be env-var controlled

### Config-first principle
When the user mentions a future deployment scenario (cloud, multi-user, public access), make related config (CORS origins, auth, rate limits) **environment-variable configurable at implementation time**, not as a follow-up task.
