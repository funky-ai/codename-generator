# Changelog

All notable changes to this project will be documented in this file.

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
