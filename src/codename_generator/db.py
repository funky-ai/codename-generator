"""SQLite database layer for codename inventory."""

from __future__ import annotations

import secrets
import sqlite3
import string
from pathlib import Path
from typing import Optional

_ID_ALPHABET = string.ascii_letters + string.digits
_ID_LENGTH = 8
DEFAULT_LOG_LIMIT = 50


def _generate_unique_id(
    prefix: str,
    conn: sqlite3.Connection,
    table: str,
    column: str,
    max_retries: int = 5,
) -> str:
    """Generate a unique random ID with collision retry."""
    for _ in range(max_retries):
        random_part = "".join(secrets.choice(_ID_ALPHABET) for _ in range(_ID_LENGTH))
        new_id = f"{prefix}-{random_part}"
        exists = conn.execute(
            f"SELECT 1 FROM {table} WHERE {column} = ?", (new_id,)
        ).fetchone()
        if not exists:
            return new_id
    raise RuntimeError(
        f"Failed to generate unique {prefix} ID after {max_retries} attempts"
    )


def generate_codename_id(conn: sqlite3.Connection) -> str:
    """Generate a cryptographically random codename ID (e.g. CN-a3Kx9mBQ)."""
    return _generate_unique_id("CN", conn, "codename_inventory", "codename_id")


def generate_assignment_id(conn: sqlite3.Connection) -> str:
    """Generate a cryptographically random assignment ID (e.g. ASN-x7KmP2qR)."""
    return _generate_unique_id("ASN", conn, "assignments", "assignment_id")

SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS codename_inventory (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    codename_id TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    name_en     TEXT NOT NULL,
    name_zh   TEXT NOT NULL,
    theme     TEXT NOT NULL CHECK (theme IN ('person', 'animal')),
    sub_theme TEXT,
    brief     TEXT NOT NULL,
    status    TEXT NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'assigned')),
    added_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE TABLE IF NOT EXISTS assignments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id TEXT NOT NULL UNIQUE,
    codename_id   INTEGER NOT NULL REFERENCES codename_inventory(id),
    description   TEXT,
    assigned_by   TEXT NOT NULL DEFAULT 'system',
    assigned_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    UNIQUE(codename_id)
);

CREATE TABLE IF NOT EXISTS logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    action      TEXT NOT NULL CHECK (action IN ('added', 'assigned', 'updated')),
    codename_id TEXT NOT NULL,
    operator    TEXT NOT NULL DEFAULT 'system',
    details     TEXT
);

CREATE INDEX IF NOT EXISTS idx_inventory_status ON codename_inventory(status);
CREATE INDEX IF NOT EXISTS idx_inventory_theme ON codename_inventory(theme);
CREATE INDEX IF NOT EXISTS idx_logs_action ON logs(action);
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path) -> None:
    """Create tables if they don't exist, then run migrations. Idempotent."""
    from .migrations import run_all_migrations

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    conn.executescript(SCHEMA_DDL)
    run_all_migrations(conn)
    conn.close()


# ---------------------------------------------------------------------------
# codename_inventory CRUD
# ---------------------------------------------------------------------------


def insert_codename(conn: sqlite3.Connection, data: dict) -> int:
    """Insert a single codename. Returns the new row id."""
    cur = conn.execute(
        """INSERT INTO codename_inventory
           (codename_id, name, name_en, name_zh, theme, sub_theme, brief)
           VALUES (:codename_id, :name, :name_en, :name_zh, :theme, :sub_theme, :brief)""",
        data,
    )
    return cur.lastrowid  # type: ignore[return-value]


def get_codename_by_codename_id(conn: sqlite3.Connection, codename_id: str) -> Optional[dict]:
    """Look up a codename by its public codename_id."""
    row = conn.execute(
        "SELECT * FROM codename_inventory WHERE codename_id = ?", (codename_id,)
    ).fetchone()
    return dict(row) if row else None


def get_codename_by_name(conn: sqlite3.Connection, name: str) -> Optional[dict]:
    """Look up a codename by its canonical name."""
    row = conn.execute(
        "SELECT * FROM codename_inventory WHERE name = ?", (name,)
    ).fetchone()
    return dict(row) if row else None


def get_available_codenames(
    conn: sqlite3.Connection,
    theme: Optional[str] = None,
    sub_theme: Optional[str] = None,
) -> list[dict]:
    """Return all available codenames, optionally filtered."""
    sql = "SELECT * FROM codename_inventory WHERE status = 'available'"
    params: list = []
    if theme:
        sql += " AND theme = ?"
        params.append(theme)
    if sub_theme:
        sql += " AND sub_theme = ?"
        params.append(sub_theme)
    sql += " ORDER BY added_at DESC"
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_random_available(
    conn: sqlite3.Connection,
    count: int,
    theme: Optional[str] = None,
) -> list[dict]:
    """Draw *count* random available codenames."""
    sql = "SELECT * FROM codename_inventory WHERE status = 'available'"
    params: list = []
    if theme:
        sql += " AND theme = ?"
        params.append(theme)
    sql += " ORDER BY RANDOM() LIMIT ?"
    params.append(count)
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def list_codenames(
    conn: sqlite3.Connection,
    theme: Optional[str] = None,
    status: Optional[str] = None,
    sub_theme: Optional[str] = None,
) -> list[dict]:
    """List codenames with optional filters."""
    sql = "SELECT * FROM codename_inventory WHERE 1=1"
    params: list = []
    if theme:
        sql += " AND theme = ?"
        params.append(theme)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if sub_theme:
        sql += " AND sub_theme = ?"
        params.append(sub_theme)
    sql += " ORDER BY added_at DESC"
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def search_codenames(conn: sqlite3.Connection, query: str) -> list[dict]:
    """Search codenames by name/name_en/name_zh/brief."""
    pattern = f"%{query}%"
    sql = """SELECT * FROM codename_inventory
             WHERE name LIKE ? OR name_en LIKE ? OR name_zh LIKE ? OR brief LIKE ?
             ORDER BY added_at DESC"""
    return [dict(r) for r in conn.execute(sql, (pattern,) * 4).fetchall()]


def update_codename_status(conn: sqlite3.Connection, codename_id: int, new_status: str) -> None:
    """Update the status of a codename."""
    conn.execute(
        "UPDATE codename_inventory SET status = ? WHERE id = ?",
        (new_status, codename_id),
    )


_UPDATABLE_COLUMNS = frozenset({"name", "name_en", "name_zh", "theme", "sub_theme", "brief"})


def update_codename_fields(conn: sqlite3.Connection, codename_id: int, updates: dict) -> None:
    """Update specified fields of a codename. Keys are column names, values are new values."""
    if not updates:
        return
    invalid = set(updates) - _UPDATABLE_COLUMNS
    if invalid:
        raise ValueError(f"Invalid columns: {invalid}")
    set_clauses = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [codename_id]
    conn.execute(
        f"UPDATE codename_inventory SET {set_clauses} WHERE id = ?",
        values,
    )


# ---------------------------------------------------------------------------
# assignments CRUD
# ---------------------------------------------------------------------------


def insert_assignment(
    conn: sqlite3.Connection,
    assignment_id: str,
    codename_id: int,
    description: Optional[str],
    assigned_by: str,
) -> None:
    """Insert an assignment record."""
    conn.execute(
        """INSERT INTO assignments (assignment_id, codename_id, description, assigned_by)
           VALUES (?, ?, ?, ?)""",
        (assignment_id, codename_id, description, assigned_by),
    )


def get_assignment_by_codename(
    conn: sqlite3.Connection, codename_internal_id: int
) -> Optional[dict]:
    """Get assignment record for a codename (by internal id)."""
    row = conn.execute(
        """SELECT a.assignment_id, c.codename_id, c.name AS codename_name,
                  a.description, a.assigned_by, a.assigned_at
           FROM assignments a JOIN codename_inventory c ON a.codename_id = c.id
           WHERE a.codename_id = ?""",
        (codename_internal_id,),
    ).fetchone()
    return dict(row) if row else None


def get_all_assignments(conn: sqlite3.Connection) -> list[dict]:
    """Return all assignments with codename details."""
    sql = """SELECT a.assignment_id, c.codename_id, c.name AS codename_name,
                    a.description, a.assigned_by, a.assigned_at
             FROM assignments a JOIN codename_inventory c ON a.codename_id = c.id
             ORDER BY a.assigned_at DESC"""
    return [dict(r) for r in conn.execute(sql).fetchall()]


# ---------------------------------------------------------------------------
# logs CRUD
# ---------------------------------------------------------------------------


def insert_log(
    conn: sqlite3.Connection,
    action: str,
    codename_id: str,
    operator: str,
    details: Optional[str] = None,
) -> None:
    """Insert an audit log entry."""
    conn.execute(
        """INSERT INTO logs (action, codename_id, operator, details)
           VALUES (?, ?, ?, ?)""",
        (action, codename_id, operator, details),
    )


def get_logs(
    conn: sqlite3.Connection,
    limit: int = DEFAULT_LOG_LIMIT,
    action: Optional[str] = None,
) -> list[dict]:
    """Return audit logs, most recent first."""
    sql = "SELECT timestamp, action, codename_id, operator, details FROM logs"
    params: list = []
    if action:
        sql += " WHERE action = ?"
        params.append(action)
    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ---------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------


def get_inventory_stats(conn: sqlite3.Connection) -> dict:
    """Return inventory statistics."""
    # Count by status in a single query
    status_counts: dict[str, int] = {}
    for row in conn.execute(
        "SELECT status, COUNT(*) AS cnt FROM codename_inventory GROUP BY status"
    ).fetchall():
        status_counts[row["status"]] = row["cnt"]
    available = status_counts.get("available", 0)
    assigned = status_counts.get("assigned", 0)
    total = available + assigned

    by_theme: dict[str, int] = {}
    for row in conn.execute(
        "SELECT theme, COUNT(*) AS cnt FROM codename_inventory GROUP BY theme"
    ).fetchall():
        by_theme[row["theme"]] = row["cnt"]

    available_by_theme: dict[str, int] = {}
    for row in conn.execute(
        "SELECT theme, COUNT(*) AS cnt FROM codename_inventory"
        " WHERE status = 'available' GROUP BY theme"
    ).fetchall():
        available_by_theme[row["theme"]] = row["cnt"]

    return {
        "total": total,
        "available": available,
        "assigned": assigned,
        "by_theme": by_theme,
        "available_by_theme": available_by_theme,
    }
