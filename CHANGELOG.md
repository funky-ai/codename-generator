# Changelog

All notable changes to this project will be documented in this file.

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
