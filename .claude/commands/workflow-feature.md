---
description: Full feature development workflow — design, implement, test, review, document, and deploy.
argument-hint: <feature description>
allowed-tools: [Skill, Read, Grep, Glob, Bash, TodoWrite, Edit, Write, AskUserQuestion]
---

# Feature Development Workflow

You are developing a new feature for the **codename-generator** project.

**Project context:**
- Python 3.12 MCP server + Web UI: FastMCP + FastAPI + Pydantic + SQLite
- 5-layer architecture:
  - `server.py`: FastMCP tool definitions (MCP interface layer)
  - `api.py`: FastAPI REST API + frontend serving (REST interface layer)
  - `core.py`: `CodenameManager` class (business logic layer)
  - `db.py`: SQLite operations, schema, migrations (data access layer)
  - `models.py`: Pydantic input/output schemas (data model layer)
- Frontend: `web/` (Vite + React + TypeScript + shadcn/ui), build to `src/codename_generator/static/`
- Package managers: **uv** (Python), **pnpm** (frontend)
- Source: `src/codename_generator/`
- Tests: `tests/test_core.py` (business logic), `tests/test_api.py` (REST API)
- Run tests: `uv run pytest tests/ -v`
- IDs use CSPRNG: `secrets` module, format `CN-xxxxxxxx`, `ASN-xxxxxxxx`
- Database: SQLite with WAL mode, foreign keys enabled
- Migrations: idempotent functions in `db.py`

**Feature request:** $ARGUMENTS

---

## Phase 1: Requirements Capture

Parse the feature description from $ARGUMENTS. Identify:
- What is the user trying to accomplish?
- What MCP tools need to be added or modified?
- What data needs to be stored or queried?

If requirements are unclear, use AskUserQuestion to clarify before proceeding.

Create a TodoWrite task list for this feature based on the phases below.

## Phase 2: System Design

Invoke the `engineering:system-design` skill via the Skill tool.

Design the feature covering:
- Data model changes (new Pydantic models in `models.py`?)
- Database schema changes (new tables/columns in `db.py`?)
- API surface (new MCP tools in `server.py`?)
- Core logic (new methods on `CodenameManager` in `core.py`?)

## Phase 3: Architecture Decision

Invoke the `engineering:architecture` skill via the Skill tool.

Create an ADR (Architecture Decision Record) covering:
- Context: why is this feature needed?
- Options considered
- Decision and trade-offs
- File change plan: which files will be modified and how

## CHECKPOINT 1

STOP. Present the design document and architecture decision to the user:
- Data model design
- API design (MCP tool signatures)
- File change plan
- Any trade-offs or open questions

Ask: "Here's the design for this feature. Does the approach look good? Any changes before I start coding?"

Do NOT proceed until the user confirms.

## Phase 4: Implementation

Implement the feature following the 4-layer architecture. Work bottom-up:

1. **models.py** — Add new Pydantic models (input types, output types)
2. **db.py** — Add migration function (idempotent), add CRUD methods
3. **core.py** — Add business logic methods to `CodenameManager`
4. **server.py** — Add FastMCP tool definitions that call `CodenameManager`

Follow existing patterns:
- Database connections: open/close per method call
- ID generation: use `secrets` module
- Error handling: raise `ValueError` with descriptive messages
- Type hints on all function signatures
- Docstrings on all public functions (match existing coverage in `core.py` and `server.py`)
- Every `import` of a third-party package must have a corresponding entry in `pyproject.toml` dependencies (never rely on transitive deps)
- Environment-sensitive config (CORS, host, DB path) must be configurable via env vars
- If frontend changes are needed: rebuild with `cd web && pnpm build` and verify unused deps in `package.json`

## Phase 5: Testing

Invoke the `engineering:testing-strategy` skill via the Skill tool.

1. Design test cases covering:
   - Happy path (feature works as expected)
   - Edge cases (empty inputs, boundary values)
   - Error cases (invalid inputs, constraint violations)
2. Write tests in `tests/test_core.py`:
   - New test class named `Test<FeatureName>`
   - Use `tmp_path` fixture for database isolation
   - Add helper functions if needed
3. Run the full test suite: `uv run pytest tests/ -v`
4. Ensure ALL tests pass (both new and existing)

## CHECKPOINT 2

STOP. Present the implementation and test results:
- Files changed (with line counts)
- New MCP tools added (with signatures)
- Test results (pass/fail count)
- Any issues encountered during implementation

Ask: "Implementation and tests are complete. All tests pass. Should I proceed to code review?"

Do NOT proceed until the user confirms.

## Phase 6: Code Review

Invoke the `engineering:code-review` skill via the Skill tool.

Review **all** changes across the full stack:

**Python backend:**
- **Security**: SQL injection, input validation, CSPRNG usage
- **Performance**: unnecessary DB queries, N+1 problems
- **Correctness**: edge cases, error handling, data integrity
- **Consistency**: follows existing patterns and conventions (docstrings, type hints, error handling style)
- **API design**: MCP tool naming, parameter types, return types

**Frontend (if applicable):**
- **Dependencies**: every package in `package.json` actually imported? Remove unused deps.
- **Consistency**: component patterns match existing code

**Cross-layer checks:**
- **Dependency declarations**: every `import` of a third-party package has a matching entry in `pyproject.toml` dependencies (transitive deps don't count)
- **Config hardcoding**: any environment-sensitive values (CORS, hosts, paths) must be env-var configurable, not hardcoded

Fix any issues found during review.

## Phase 7: Documentation

Invoke the `engineering:documentation` skill via the Skill tool.

**Mandatory checklist** — check every file and update if the feature affects it:
- [ ] `README.md` — features list, quick start, tools table, dev commands
- [ ] `README-zh.md` — keep in sync with English version
- [ ] `CHANGELOG.md` — add entry under new version or "Unreleased"
- [ ] `CHANGELOG-zh.md` — keep in sync with English version
- [ ] `CONTRIBUTING.md` — dev workflow, test instructions
- [ ] `CONTRIBUTING-zh.md` — keep in sync with English version
- [ ] `CLAUDE.md` — architecture, commands, conventions
- [ ] Docstrings on all new public functions (match existing coverage)

## Phase 8: Deploy Checklist

Invoke the `engineering:deploy-checklist` skill via the Skill tool.

Verify:
- [ ] All tests pass (`uv run pytest tests/ -v`)
- [ ] Lint clean (`uv run ruff check src/ tests/`)
- [ ] Code review issues resolved
- [ ] Documentation checklist from Phase 7 completed
- [ ] Database migration is idempotent
- [ ] No breaking changes to existing MCP tools
- [ ] **Dependency audit**: every third-party `import` in `src/` has a matching `pyproject.toml` entry
- [ ] **Frontend dependency audit** (if applicable): every package in `web/package.json` is actually imported in `web/src/`
- [ ] **No hardcoded config**: CORS, host, DB path etc. are env-var configurable
- [ ] Version bump needed? (likely minor for new feature)
- [ ] Frontend rebuilt (`cd web && pnpm build`) if frontend was changed

## CHECKPOINT 3

STOP. Present the complete feature summary:
- What was built (user-facing description)
- Files changed
- New MCP tools available
- Test coverage
- Documentation status
- Deploy readiness

Ask: "Feature development is complete. Everything is reviewed and documented. Ready to commit?"

Do NOT proceed until the user confirms.
