# Contributing

[中文版](CONTRIBUTING-zh.md)

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
uv run python -m codename_generator web              # User HTTP server  (:8000)
uv run python -m codename_generator admin            # Admin HTTP server (:8001)
```

### Frontend Development

Requires Node.js and pnpm.

Frontend is a pnpm workspace with `web-admin/` (admin SPA), `web-user/` (public-facing read-only SPA), and `web-shared/` (reusable API client, UI components, i18n base).

```bash
pnpm install                    # From repo root — installs all workspace deps
cd web-admin && pnpm dev        # Vite :5174, proxies /api to :8001 (admin)
cd web-admin && pnpm build      # Build to src/codename_generator/static_admin/
cd web-user  && pnpm dev        # Vite :5173, proxies /api to :8000 (user)
cd web-user  && pnpm build      # Build to src/codename_generator/static_user/
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

- Business logic tests in `tests/test_core.py`
- API endpoint tests in `tests/test_api.py`
- Use `tmp_path` fixture for database isolation
- Organize tests in classes by feature
- Cover both success paths and error cases
