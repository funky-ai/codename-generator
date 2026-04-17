# codename-generator

## Project Overview

Python 3.12 MCP server + Web UI for managing project codenames. Built with FastMCP + FastAPI + Pydantic + SQLite.

- Package manager: **uv** (Python), **pnpm** (frontend)
- Current version: 0.1.0
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

Frontend is a pnpm workspace with three packages, each serving a distinct role:

- `web-admin/` — admin SPA (Vite + React + TypeScript + shadcn/ui), build output in `src/codename_generator/static_admin/`, consumed by the `admin` CLI subcommand.
- `web-user/` — public-facing read-only SPA, build output in `src/codename_generator/static_user/`, consumed by the `web` CLI subcommand.
- `web-shared/` — shared library (API client, UI components, i18n base translations, hooks) consumed by both clients.

Imports from shared code use the `@shared/*` alias configured in each app's `vite.config.ts` and `tsconfig.json`.

- Data directory: `data/codenames.db` (gitignored, runtime data)
- Categories are a first-class tree entity (max depth 3, adjacency-list). Codenames bind to **leaf** categories via `category_id`. Two top-level defaults seed on first run: `person` (10 leaf sub-categories — philosophy / art / science / economics / literature / music / politics / medicine / mathematics / engineering) and `animal` (3 — raptor / marine / mammal). Users can add / re-parent / archive / delete categories via the admin UI or the `create_category` / `update_category` / `delete_category` MCP tools.
- All IDs use CSPRNG (`secrets` module): `CN-xxxxxxxx`, `ASN-xxxxxxxx`, `CAT-xxxxxxxx`

## Development Commands

```bash
uv sync                                              # Install Python dependencies
uv run pytest tests/ -v                              # Run tests
uv run fastmcp dev src/codename_generator/server.py  # Run MCP Inspector
uv run python -m codename_generator                  # Run MCP server
uv run python -m codename_generator web              # Run user  server — static_user/  (default :8000)
uv run python -m codename_generator admin            # Run admin server — static_admin/ (default :8001)
uv run python -m codename_generator web   --port 3000  # Override port
uv run python -m codename_generator admin --port 3001  # Override port

# Env vars: CODENAME_HOST, CODENAME_WEB_PORT, CODENAME_ADMIN_PORT, CODENAME_DB_PATH, CODENAME_CORS_ORIGINS

# Frontend development (pnpm workspace — run `pnpm install` from repo root)
pnpm install                                         # Install all workspace dependencies
cd web-admin && pnpm dev                             # Vite dev :5174, proxies /api to :8001 (admin)
cd web-admin && pnpm build                           # Build to src/codename_generator/static_admin/
cd web-user  && pnpm dev                             # Vite dev :5173, proxies /api to :8000 (user)
cd web-user  && pnpm build                           # Build to src/codename_generator/static_user/
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

## Mandatory Rule

Every code change MUST invoke the matching workflow BEFORE writing any code:

| Trigger | Workflow |
|---------|----------|
| Any new feature, UI change, new API endpoint, new tool | `/workflow-feature` |
| Bug report, test failure, unexpected behavior | `/workflow-bugfix` |
| Server crash, data corruption, service outage | `/workflow-incident` |
| Version bump, changelog, publish | `/workflow-release` |
| Refactoring, tech debt, periodic review | `/workflow-health` |
| Start of work session, progress check | `/workflow-standup` |

**No exceptions.** "Looks simple" is not a valid reason to skip.
If uncertain which workflow applies, ask the user before proceeding.

## Git Conventions

- Conventional commit-style messages
- Version bumps: update `pyproject.toml` version field
- Changelog: update both `CHANGELOG.md` and `CHANGELOG-zh.md`
- Bilingual documentation: maintain English and Chinese versions

