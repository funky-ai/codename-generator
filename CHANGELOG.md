# Changelog

All notable changes to this project will be documented in this file.

## [0.0.7] - 2026-04-17

### Changed
- **Internal refactor — no functional or visual changes.** Extracted reusable frontend code into a pnpm workspace in preparation for the planned 0.1.0 admin/user client split.
  - Renamed `web/` → `web-admin/` (admin SPA).
  - New `web-shared/` package containing the API client (`lib/api.ts`), `cn` util, shadcn UI primitives, the `useLang` hook factory, and the i18n base translations.
  - Added `pnpm-workspace.yaml` at the repo root; `pnpm-lock.yaml` moved to the root.
  - Admin code now imports shared modules via the `@shared/*` alias (configured in `web-admin/vite.config.ts` and `tsconfig.json`).
  - Admin-only translation keys live in `web-admin/src/lib/admin-i18n.ts` and merge on top of `baseTranslations` at runtime.
- `uv.lock` and the FastAPI app `version=` string synced to 0.0.7.
- `CLAUDE.md`, `README.md`, `README-zh.md`, `CONTRIBUTING.md`, `CONTRIBUTING-zh.md`: updated the frontend commands and architecture description to reflect the workspace layout.

### Verified
- `pnpm build` produces a CSS bundle byte-identical to 0.0.6 (hash unchanged); JS bundle differs by ~240 bytes due to the added i18n factory indirection — behaviour is unchanged.
- `pytest tests/ -v`: 77/77 pass.

## [0.0.6] - 2026-04-16

### Added
- **Project logo**: CN tag logo integrated into Web UI header and browser favicon
- SVG static file serving route in `api.py` for root-level assets (logo, icons)
- 2 new tests for SVG serving endpoint (exists + 404)
- 4 missing docstrings added to `core.py` and `server.py`

### Changed
- CLAUDE.md: added Mandatory Workflow Rule — all code changes must invoke a workflow before implementation

### Fixed
- FastAPI app version corrected from `0.0.4` to `0.0.6` (was missed in v0.0.5 release)
- Replaced default favicon with project-branded CN logo

## [0.0.5] - 2026-04-13

### Added
- **Web UI**: Responsive web interface with React + shadcn/ui (desktop + mobile)
- **REST API**: FastAPI backend (`api.py`) with 9 endpoints wrapping CodenameManager
- Chinese/English bilingual switching in web UI (stored in localStorage)
- `python -m codename_generator web` command to start web server
- 24 new API tests in `tests/test_api.py` (75 total)

### Changed
- `pyproject.toml`: added `fastapi` and `uvicorn` as explicit dependencies
- `CLAUDE.md`: updated architecture docs to include REST layer

### Fixed
- CORS origins now configurable via `CODENAME_CORS_ORIGINS` env var (was hardcoded `*`)
- Removed unused `react-router-dom` dependency from frontend
- Added docstrings to all API route functions
- Updated README, CONTRIBUTING (bilingual) with web frontend docs

### Infrastructure
- Frontend project in `web/` (Vite + React + TypeScript + pnpm)
- Build output to `src/codename_generator/static/`
- Vite dev server proxies API calls to FastAPI backend
- Hardened `/workflow-feature` skill with full-stack code review, mandatory doc checklist, and dependency audit

## [0.0.4] - 2026-04-13

### Added
- GitHub Actions CI workflow (pytest + ruff on push/PR)
- `ruff` linter with E, F, I rules
- `CONTRIBUTING.md` and `CONTRIBUTING-zh.md`
- `CLAUDE.md` with project conventions and workflow routing
- Tests for `list_inventory` (5 tests), `list_assignments` (3 tests), and boundary inputs (4 tests)
- SQL column whitelist validation in `update_codename_fields`
- `DEFAULT_LOG_LIMIT` constant replacing hardcoded `50`

### Changed
- Extracted migration functions from `db.py` into `migrations.py`
- `get_inventory_stats` optimized from 4 queries to 3
- `CodenameManager` initialization changed from module-level to lazy `get_manager()`
- README: added missing `update_codename` tool to tools table

### Fixed
- Removed outdated "one project one codename" text from best-practices docs
- Removed unused imports (`json` in server.py, `tempfile`/`Path` in tests)

## [0.0.3] - 2026-04-13

### Security
- Assignments now use random `assignment_id` (format: `ASN-xxxxxxxx`, CSPRNG) — internal auto-increment `id` no longer exposed in API responses
- Audit logs no longer expose internal auto-increment `id`
- Audit log column changed from mutable display name to stable `codename_id` (`CN-xxxxxxxx`), preserving audit trail integrity across renames
- ID generation now includes collision retry (up to 5 attempts) with clear error on failure

### Changed
- `assign_codename`: required `project_name` replaced with optional `description` — codenames are the project identifiers, not the other way around
- One-project-one-codename constraint removed
- `assigned_at` now returns the actual DB timestamp instead of an empty string
- `details` JSON in logs stores `name` (human-readable) instead of redundant `codename_id` (now in its own column)
- Prompt `assign_project_codename` renamed to `assign_codename_workflow` (no longer requires project name)

### Migration
- Automatic v3 schema migration: generates `assignment_id` for existing assignments, extracts `codename_id` from log details JSON, renames `project_name` to `description`

## [0.0.2] - 2026-04-12

### Added
- `codename_id` as stable unique identifier (format: `CN-xxxxxxxx`, CSPRNG generated, immutable)
- `update_codename` tool for correcting existing codename fields with audit logging
- Database migration for existing databases (auto-generates `codename_id` for pre-existing records)

### Changed
- All lookup operations (assign, update) now use `codename_id` instead of `name`
- `name` demoted to display-only field (UNIQUE constraint removed)
- `add_codenames` return value: `duplicates` replaced by `codename_ids`
- `LogEntry.action` now supports `"updated"` in addition to `"added"` and `"assigned"`

## [0.0.1] - 2026-04-10

### Added
- Codename inventory management (add, search, list)
- Random draw from available codenames
- Permanent codename-to-project assignment
- Person and animal themes with validation
- Audit logging for all operations
- Inventory statistics with low-stock warnings
- Bilingual README (English & Chinese)
