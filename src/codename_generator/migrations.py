"""Database migration functions. Each migration is idempotent."""

from __future__ import annotations

import json
import secrets
import sqlite3
import string

_ID_ALPHABET = string.ascii_letters + string.digits
_ID_LENGTH = 8


def _migrate_logs_action_constraint(conn: sqlite3.Connection) -> None:
    """Ensure the logs table CHECK constraint includes 'updated'. Idempotent."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='logs'"
    ).fetchone()
    if not row:
        return
    if "'updated'" in row[0]:
        return
    conn.executescript("""
        ALTER TABLE logs RENAME TO _logs_old;
        CREATE TABLE logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
            action    TEXT NOT NULL CHECK (action IN ('added', 'assigned', 'updated')),
            codename  TEXT NOT NULL,
            operator  TEXT NOT NULL DEFAULT 'system',
            details   TEXT
        );
        INSERT INTO logs SELECT * FROM _logs_old;
        DROP TABLE _logs_old;
        CREATE INDEX IF NOT EXISTS idx_logs_action ON logs(action);
    """)


def _migrate_inventory_codename_id(conn: sqlite3.Connection) -> None:
    """Add codename_id column and remove UNIQUE from name. Idempotent."""
    from .db import generate_codename_id

    columns = [row[1] for row in conn.execute("PRAGMA table_info(codename_inventory)").fetchall()]
    if "codename_id" in columns:
        return
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("BEGIN")
    conn.execute("ALTER TABLE codename_inventory RENAME TO _inventory_old")
    conn.execute("""
        CREATE TABLE codename_inventory (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            codename_id TEXT NOT NULL UNIQUE,
            name        TEXT NOT NULL,
            name_en     TEXT NOT NULL,
            name_zh     TEXT NOT NULL,
            theme       TEXT NOT NULL CHECK (theme IN ('person', 'animal')),
            sub_theme   TEXT,
            brief       TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'assigned')),
            added_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
        )
    """)
    rows = conn.execute("SELECT * FROM _inventory_old").fetchall()
    for row in rows:
        conn.execute(
            """INSERT INTO codename_inventory
               (id, codename_id, name, name_en, name_zh, theme, sub_theme, brief, status, added_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (row["id"], generate_codename_id(conn), row["name"], row["name_en"], row["name_zh"],
             row["theme"], row["sub_theme"], row["brief"], row["status"], row["added_at"]),
        )
    conn.execute("DROP TABLE _inventory_old")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_status ON codename_inventory(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_theme ON codename_inventory(theme)")
    conn.commit()
    conn.execute("PRAGMA foreign_keys=ON")


def _migrate_v3_schema(conn: sqlite3.Connection) -> None:
    """Migrate assignments (add assignment_id, project_name->description) and
    logs (codename->codename_id). Idempotent."""
    columns = [row[1] for row in conn.execute("PRAGMA table_info(assignments)").fetchall()]
    if not columns:
        return  # table doesn't exist yet (fresh DB handles it via SCHEMA_DDL)
    if "assignment_id" in columns:
        return  # already migrated

    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("BEGIN")

    # --- Migrate assignments ---
    conn.execute("ALTER TABLE assignments RENAME TO _assignments_old")
    conn.execute("""
        CREATE TABLE assignments (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id TEXT NOT NULL UNIQUE,
            codename_id   INTEGER NOT NULL REFERENCES codename_inventory(id),
            description   TEXT,
            assigned_by   TEXT NOT NULL DEFAULT 'system',
            assigned_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
            UNIQUE(codename_id)
        )
    """)
    old_assignments = conn.execute("SELECT * FROM _assignments_old").fetchall()
    for row in old_assignments:
        random_part = "".join(secrets.choice(_ID_ALPHABET) for _ in range(_ID_LENGTH))
        asn_id = f"ASN-{random_part}"
        conn.execute(
            """INSERT INTO assignments
               (id, assignment_id, codename_id, description, assigned_by, assigned_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (row["id"], asn_id, row["codename_id"],
             row["project_name"], row["assigned_by"], row["assigned_at"]),
        )
    conn.execute("DROP TABLE _assignments_old")

    # --- Migrate logs ---
    conn.execute("ALTER TABLE logs RENAME TO _logs_old")
    conn.execute("""
        CREATE TABLE logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
            action      TEXT NOT NULL CHECK (action IN ('added', 'assigned', 'updated')),
            codename_id TEXT NOT NULL,
            operator    TEXT NOT NULL DEFAULT 'system',
            details     TEXT
        )
    """)
    old_logs = conn.execute("SELECT * FROM _logs_old").fetchall()
    for row in old_logs:
        # Extract stable codename_id from details JSON (all actions store it)
        cn_id = row["codename"]  # fallback to old display name
        if row["details"]:
            try:
                details = json.loads(row["details"])
                if "codename_id" in details:
                    cn_id = details["codename_id"]
            except (json.JSONDecodeError, KeyError):
                pass
        conn.execute(
            """INSERT INTO logs (id, timestamp, action, codename_id, operator, details)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (row["id"], row["timestamp"], row["action"], cn_id,
             row["operator"], row["details"]),
        )
    conn.execute("DROP TABLE _logs_old")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_action ON logs(action)")

    conn.commit()
    conn.execute("PRAGMA foreign_keys=ON")


def run_all_migrations(conn: sqlite3.Connection) -> None:
    """Run all migrations in order. Each is idempotent."""
    _migrate_logs_action_constraint(conn)
    _migrate_inventory_codename_id(conn)
    _migrate_v3_schema(conn)
