"""SQLite database layer for codename inventory."""

from __future__ import annotations

import json
import secrets
import sqlite3
import string
from pathlib import Path
from typing import Optional

_ID_ALPHABET = string.ascii_letters + string.digits
_ID_LENGTH = 8


def generate_codename_id() -> str:
    """Generate a cryptographically random codename ID (e.g. CN-a3Kx9mBQ)."""
    random_part = "".join(secrets.choice(_ID_ALPHABET) for _ in range(_ID_LENGTH))
    return f"CN-{random_part}"

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
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    codename_id  INTEGER NOT NULL REFERENCES codename_inventory(id),
    project_name TEXT NOT NULL,
    assigned_by  TEXT NOT NULL DEFAULT 'system',
    assigned_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    UNIQUE(codename_id)
);

CREATE TABLE IF NOT EXISTS logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    action    TEXT NOT NULL CHECK (action IN ('added', 'assigned', 'updated')),
    codename  TEXT NOT NULL,
    operator  TEXT NOT NULL DEFAULT 'system',
    details   TEXT
);

CREATE INDEX IF NOT EXISTS idx_inventory_status ON codename_inventory(status);
CREATE INDEX IF NOT EXISTS idx_inventory_theme ON codename_inventory(theme);
CREATE INDEX IF NOT EXISTS idx_assignments_project ON assignments(project_name);
CREATE INDEX IF NOT EXISTS idx_logs_action ON logs(action);
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


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
            (row["id"], generate_codename_id(), row["name"], row["name_en"], row["name_zh"],
             row["theme"], row["sub_theme"], row["brief"], row["status"], row["added_at"]),
        )
    conn.execute("DROP TABLE _inventory_old")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_status ON codename_inventory(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_inventory_theme ON codename_inventory(theme)")
    conn.commit()
    conn.execute("PRAGMA foreign_keys=ON")


def init_db(db_path: Path) -> None:
    """Create tables if they don't exist. Idempotent."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    conn.executescript(SCHEMA_DDL)
    _migrate_logs_action_constraint(conn)
    _migrate_inventory_codename_id(conn)
    conn.close()


# ---------------------------------------------------------------------------
# codename_inventory CRUD
# ---------------------------------------------------------------------------


def insert_codename(conn: sqlite3.Connection, data: dict) -> int:
    """Insert a single codename. Returns the new row id."""
    cur = conn.execute(
        """INSERT INTO codename_inventory (codename_id, name, name_en, name_zh, theme, sub_theme, brief)
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


def update_codename_fields(conn: sqlite3.Connection, codename_id: int, updates: dict) -> None:
    """Update specified fields of a codename. Keys are column names, values are new values."""
    if not updates:
        return
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
    codename_id: int,
    project_name: str,
    assigned_by: str,
) -> int:
    """Insert an assignment record. Returns the new row id."""
    cur = conn.execute(
        """INSERT INTO assignments (codename_id, project_name, assigned_by)
           VALUES (?, ?, ?)""",
        (codename_id, project_name, assigned_by),
    )
    return cur.lastrowid  # type: ignore[return-value]


def get_assignment_by_project(conn: sqlite3.Connection, project_name: str) -> Optional[dict]:
    """Check if a project already has a codename assigned."""
    row = conn.execute(
        """SELECT a.id, c.codename_id, c.name AS codename_name,
                  a.project_name, a.assigned_by, a.assigned_at
           FROM assignments a JOIN codename_inventory c ON a.codename_id = c.id
           WHERE a.project_name = ?""",
        (project_name,),
    ).fetchone()
    return dict(row) if row else None


def get_all_assignments(conn: sqlite3.Connection) -> list[dict]:
    """Return all assignments with codename details."""
    sql = """SELECT a.id, c.codename_id, c.name AS codename_name,
                    a.project_name, a.assigned_by, a.assigned_at
             FROM assignments a JOIN codename_inventory c ON a.codename_id = c.id
             ORDER BY a.assigned_at DESC"""
    return [dict(r) for r in conn.execute(sql).fetchall()]


# ---------------------------------------------------------------------------
# logs CRUD
# ---------------------------------------------------------------------------


def insert_log(
    conn: sqlite3.Connection,
    action: str,
    codename: str,
    operator: str,
    details: Optional[str] = None,
) -> int:
    """Insert an audit log entry."""
    cur = conn.execute(
        """INSERT INTO logs (action, codename, operator, details)
           VALUES (?, ?, ?, ?)""",
        (action, codename, operator, details),
    )
    return cur.lastrowid  # type: ignore[return-value]


def get_logs(
    conn: sqlite3.Connection,
    limit: int = 50,
    action: Optional[str] = None,
) -> list[dict]:
    """Return audit logs, most recent first."""
    sql = "SELECT * FROM logs"
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
    total = conn.execute("SELECT COUNT(*) FROM codename_inventory").fetchone()[0]
    available = conn.execute(
        "SELECT COUNT(*) FROM codename_inventory WHERE status = 'available'"
    ).fetchone()[0]
    assigned = conn.execute(
        "SELECT COUNT(*) FROM codename_inventory WHERE status = 'assigned'"
    ).fetchone()[0]

    by_theme = {}
    for row in conn.execute(
        "SELECT theme, COUNT(*) AS cnt FROM codename_inventory GROUP BY theme"
    ).fetchall():
        by_theme[row["theme"]] = row["cnt"]

    available_by_theme = {}
    for row in conn.execute(
        "SELECT theme, COUNT(*) AS cnt FROM codename_inventory WHERE status = 'available' GROUP BY theme"
    ).fetchall():
        available_by_theme[row["theme"]] = row["cnt"]

    return {
        "total": total,
        "available": available,
        "assigned": assigned,
        "by_theme": by_theme,
        "available_by_theme": available_by_theme,
    }
