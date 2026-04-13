---
description: Release preparation — tech debt review, testing, version bump, changelog, and deploy checklist.
argument-hint: <version hint, e.g. "patch" or "0.0.4">
allowed-tools: [Skill, Read, Grep, Glob, Bash, TodoWrite, Edit, Write, AskUserQuestion]
---

# Release Workflow

You are preparing a release for the **codename-generator** project.

**Project context:**
- Python 3.12 MCP server: FastMCP + Pydantic + SQLite
- Version defined in `pyproject.toml` (currently check for latest)
- Tests: `uv run pytest tests/ -v`
- Changelogs: `CHANGELOG.md` (English) and `CHANGELOG-zh.md` (Chinese)
- Changelog format: date header, sections (Added / Changed / Fixed / Security / Migration)

**Version hint:** $ARGUMENTS

---

## Phase 1: Tech Debt Review

Invoke the `engineering:tech-debt` skill via the Skill tool.

Quick scan before release:
- Any critical TODOs that should be addressed before release?
- Known bugs or regressions?
- Dependency issues?
- Any incomplete migrations in `db.py`?

## CHECKPOINT 1

STOP. Present tech debt findings relevant to the release.

Ask: "Here are items that may need attention before release. Which (if any) should we address first? Or should we proceed with the release as-is?"

Do NOT proceed until the user confirms.

## Phase 2: Testing

Invoke the `engineering:testing-strategy` skill via the Skill tool.

- Run full test suite: `uv run pytest tests/ -v`
- Ensure ALL tests pass
- Check for any flaky or skipped tests
- Verify test coverage of recent changes (check `git log` since last version bump)

If tests fail, STOP and report the failures. Do not proceed with a release if tests are failing.

## Phase 3: Version Determination

1. Read current version from `pyproject.toml`
2. Review changes since last version bump: `git log --oneline` (find last "Bump version" commit)
3. Determine appropriate version based on semver:
   - **patch** (0.0.x): bug fixes, minor improvements
   - **minor** (0.x.0): new features, new MCP tools
   - **major** (x.0.0): breaking changes to MCP interface
4. If $ARGUMENTS contains a version hint, factor it in

## CHECKPOINT 2

STOP. Present version recommendation:
- Current version: X.Y.Z
- Changes since last release (summary)
- Recommended new version: A.B.C
- Reasoning

Ask: "I recommend version [X.Y.Z]. Does this look right?"

Do NOT proceed until the user confirms the version number.

## Phase 4: Deploy Checklist

Invoke the `engineering:deploy-checklist` skill via the Skill tool.

Verify:
- [ ] All tests pass
- [ ] No uncommitted changes (except what we're about to create)
- [ ] Database migrations are idempotent
- [ ] No breaking changes without major version bump
- [ ] README reflects current functionality

## Phase 5: Update Changelog & Version

Invoke the `engineering:documentation` skill via the Skill tool.

1. Update `pyproject.toml` with new version number
2. Update `CLAUDE.md` version number to match
3. Update `CHANGELOG.md` following existing format:
   - Date header
   - Sections: Added / Changed / Fixed / Security / Migration (as applicable)
   - List each change with a concise description
3. Update `CHANGELOG-zh.md` with Chinese translation of the same content

## Phase 6: GitHub Release

After committing and pushing, create a GitHub Release using `gh release create`:
- Tag: `v{version}` (e.g. `v0.0.5`)
- Title: `v{version}`
- **Release notes must be bilingual**: English section first, then `---` separator, then Chinese translation (same structure as `CHANGELOG.md` + `CHANGELOG-zh.md`)
- Reference `v0.0.4` release format as the template

## CHECKPOINT 3

STOP. Present the complete release summary:
- New version number
- Changelog entries (both languages)
- All checklist items status

Ask: "Release preparation is complete. The version has been bumped and changelogs updated. Ready to commit?"

Do NOT proceed until the user confirms.
