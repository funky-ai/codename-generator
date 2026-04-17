# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added — Categories as first-class entities

- **`categories` table** with adjacency-list parent pointers: `category_id` (CAT-xxxxxxxx, CSPRNG), `slug`, `name_en` / `name_zh`, `parent_id`, `sort_order`, `is_archived`, `created_at`. Partial unique index on `(slug)` where `parent_id IS NULL` (SQLite's `UNIQUE` doesn't deduplicate NULL parents).
- **5 new MCP tools** and **5 new REST endpoints** for category CRUD:
  - `create_category` / `list_categories` / `get_category_tree` / `update_category` / `delete_category`
  - `GET/POST/PUT/DELETE /api/categories` + `GET /api/categories/{id}`
- **Admin UI Categories page** (`web-admin/src/pages/Categories.tsx`): left-side tree with expand/collapse, right-side edit form (rename / re-parent / sort / archive / delete), depth-aware parent dropdown.
- **`_migrate_v4_categories`** — idempotent migration that seeds 2 top-level + 13 leaf default categories (2 person top-level + animal top-level; philosophy / art / science / economics / literature / music / politics / medicine / mathematics / engineering; raptor / marine / mammal) and rebuilds `codename_inventory` to replace `theme` / `sub_theme` with `category_id` (INTEGER FK to `categories`). Existing `(animal, NULL)` rows migrate to the animal top-level — the only allowed non-leaf binding, documented for user migration follow-up.
- `category_path` field on `Codename` — slug list from root to leaf, filled via a single recursive CTE (no N+1).
- `tests/test_categories.py` (28 tests) and `tests/test_migrations.py` (12 tests) covering CRUD, depth / cycle invariants, archive semantics, and upgrade-from-v3 scenarios.

### Changed — BREAKING

- **`theme` / `sub_theme` fields removed** from `Codename`, `CodenameInput`, `CodenameUpdate`, MCP tools, and REST endpoints. Replace with `category_id` (public `CAT-xxxxxxxx`), which must resolve to a **non-archived leaf category**.
- **Filter parameters changed**: `theme` / `sub_theme` → `category_id` + `include_descendants: bool = True` (defaults to subtree-inclusive) on `list_inventory`, `draw_random`, `GET /api/codenames`, `GET /api/codenames/random`.
- **`InventoryStats` response shape**: `by_theme` / `available_by_theme` removed; replaced by `by_category: list[CategoryStat]` (direct counts per category, not rolled up).
- **`logs.action` CHECK** extended with `category_added` / `category_updated` / `category_archived` / `category_deleted`.
- Admin UI pages (Add / Inventory / Draw / Dashboard) and the `web-user` Browse / Draw pages refactored to the category model with cascading selectors that display `parent › child` paths.
- MCP server instructions and the two code-generation prompts (`generate_person_codenames`, `generate_animal_codenames`) now direct the model to resolve a leaf `category_id` from `get_category_tree` before calling `add_codenames`.

### Migration notes

- Invariants: codenames bind to **non-archived leaf categories only**; category depth ≤ 3; re-parenting rejects cycles and subtree-height violations; delete refuses when codenames reference the category or non-archived subcategories exist.
- **Back up `data/codenames.db` before upgrading.** Running `0.0.7` → `0.1.0-rc` automatically seeds categories and remaps existing codenames. Old `(animal, NULL)` rows land on the animal top-level (a non-leaf) — move them to a specific leaf (raptor / marine / mammal or a user-defined one) via the Categories page at your convenience.

### Added — Two independent frontend clients

- **Two independent frontend clients.** The admin UI and the public-facing user UI now ship as separate pnpm packages and run on independent processes/ports, sharing the same SQLite database and REST surface.
  - New `web-user/` package — read-only client with pages: Home (simplified overview with Available / Total / Assigned cards and two CTAs), Browse (read-only inventory table with search / theme / status filters), Draw (random suggestions, no Assign action), Assignments (read-only).
  - `web-user/src/lib/user-i18n.ts` — friendlier public-facing labels, layered over `@shared/lib/i18n-base`.
  - `web-user` imports only GET methods from `@shared/lib/api` (no `addCodenames` / `updateCodename` / `assignCodename`).
- **New `admin` CLI subcommand.** `python -m codename_generator admin` starts the admin HTTP server on port `8001` (serves `static_admin/`), in parallel with `python -m codename_generator web` on port `8000` (serves `static_user/`).
- `CODENAME_WEB_PORT` / `CODENAME_ADMIN_PORT` / `CODENAME_HOST` env vars override the default bind host + ports without code changes.
- `create_app(mode)` factory in `api.py` — returns a FastAPI instance wired for either `"user"` or `"admin"` static mounts. Module-level `app` is now `create_app("user")`, so `uvicorn codename_generator.api:app` serves the user bundle by default.

### Changed
- **Breaking (for operators only):** `python -m codename_generator web` now serves the user frontend, not the admin frontend. Run `python -m codename_generator admin` to get the admin UI.
- Static output path: the single `src/codename_generator/static/` tree is replaced by `src/codename_generator/static_admin/` (built by `web-admin`) and `src/codename_generator/static_user/` (built by `web-user`). `.gitignore` updated accordingly.
- `web-admin/vite.config.ts` builds into `../src/codename_generator/static_admin/` and proxies `/api` to `http://127.0.0.1:8001` (admin server).
- FastAPI app `title` includes the mode (`Codename Generator (user)` / `Codename Generator (admin)`) to make process origin obvious in `/openapi.json`.
- `tests/test_api.py` static-dir references now point at `static_user/` (module-level `app` is user mode).

### Verified
- `pytest tests/ -v`: **148/148 pass** (test_core.py 56, test_api.py 52, test_categories.py 28, test_migrations.py 12).
- `ruff check src/ tests/`: clean.
- `cd web-admin && pnpm build` and `cd web-user && pnpm build` both succeed, emitting into `static_admin/` and `static_user/` respectively.
- Smoke tests: admin server (`:8001`) loads Dashboard with real migrated data, Categories page renders the 15-category tree with auto-expanded top-level, Add page dropdown lists exactly 13 leaf categories as `parent › child`, `/openapi.json` reports version `0.1.0`.

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
