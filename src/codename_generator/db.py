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
MAX_CATEGORY_DEPTH = 3


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


def generate_category_id(conn: sqlite3.Connection) -> str:
    """Generate a cryptographically random category ID (e.g. CAT-pq8Tk2Xz)."""
    return _generate_unique_id("CAT", conn, "categories", "category_id")


# Tables created in final shape. On a fresh install everything lines up. On an
# upgrade from 0.0.x, CREATE TABLE IF NOT EXISTS is a no-op for pre-existing
# tables, and the v4 migration reshapes codename_inventory / logs afterwards.
SCHEMA_DDL_TABLES = """
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id TEXT NOT NULL UNIQUE,
    slug        TEXT NOT NULL,
    name_en     TEXT NOT NULL,
    name_zh     TEXT NOT NULL,
    parent_id   INTEGER REFERENCES categories(id) ON DELETE RESTRICT,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    is_archived INTEGER NOT NULL DEFAULT 0 CHECK (is_archived IN (0,1)),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
    UNIQUE(parent_id, slug)
);

CREATE TABLE IF NOT EXISTS codename_inventory (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    codename_id TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    name_en     TEXT NOT NULL,
    name_zh     TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    brief       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'assigned')),
    added_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
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
    action      TEXT NOT NULL CHECK (action IN (
        'added', 'assigned', 'updated',
        'category_added', 'category_updated', 'category_archived', 'category_deleted'
    )),
    codename_id TEXT NOT NULL,
    operator    TEXT NOT NULL DEFAULT 'system',
    details     TEXT
);

CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_top_slug
    ON categories(slug) WHERE parent_id IS NULL;
"""

# Inventory/logs indexes run AFTER migrations so we don't try to index a
# not-yet-migrated column (e.g. `idx_inventory_category` referencing
# `category_id` before v4 added it).
SCHEMA_DDL_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_inventory_status ON codename_inventory(status);
CREATE INDEX IF NOT EXISTS idx_inventory_category ON codename_inventory(category_id);
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
    """Create tables, run migrations, create indexes. Idempotent."""
    from .migrations import run_all_migrations

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    conn.executescript(SCHEMA_DDL_TABLES)
    run_all_migrations(conn)
    conn.executescript(SCHEMA_DDL_INDEXES)
    conn.close()


# ---------------------------------------------------------------------------
# categories CRUD + tree helpers
# ---------------------------------------------------------------------------


def get_category_by_public_id(
    conn: sqlite3.Connection, category_id: str
) -> Optional[dict]:
    """Look up a category by its public CAT-xxxxxxxx id."""
    row = conn.execute(
        "SELECT * FROM categories WHERE category_id = ?", (category_id,)
    ).fetchone()
    return dict(row) if row else None


def get_category_by_pk(conn: sqlite3.Connection, pk: int) -> Optional[dict]:
    """Look up a category by its internal integer pk."""
    row = conn.execute("SELECT * FROM categories WHERE id = ?", (pk,)).fetchone()
    return dict(row) if row else None


def insert_category(
    conn: sqlite3.Connection,
    category_id: str,
    slug: str,
    name_en: str,
    name_zh: str,
    parent_id: Optional[int],
    sort_order: int = 0,
) -> int:
    """Insert a category row. Returns the new integer pk."""
    cur = conn.execute(
        """INSERT INTO categories
           (category_id, slug, name_en, name_zh, parent_id, sort_order)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (category_id, slug, name_en, name_zh, parent_id, sort_order),
    )
    return cur.lastrowid  # type: ignore[return-value]


_CATEGORY_UPDATABLE = frozenset(
    {"slug", "name_en", "name_zh", "parent_id", "sort_order", "is_archived"}
)


def update_category_fields(
    conn: sqlite3.Connection, pk: int, updates: dict
) -> None:
    """Update specified columns of a category row by integer pk."""
    if not updates:
        return
    invalid = set(updates) - _CATEGORY_UPDATABLE
    if invalid:
        raise ValueError(f"Invalid category columns: {invalid}")
    set_clauses = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [pk]
    conn.execute(
        f"UPDATE categories SET {set_clauses} WHERE id = ?", values
    )


def delete_category_row(conn: sqlite3.Connection, pk: int) -> None:
    """Delete a category row by pk. Caller is responsible for pre-flight checks."""
    conn.execute("DELETE FROM categories WHERE id = ?", (pk,))


def get_category_depths(conn: sqlite3.Connection) -> dict[int, int]:
    """Return {category_pk: depth} for all categories, depth 1 = top-level."""
    sql = """
    WITH RECURSIVE cat_depth(id, depth) AS (
        SELECT id, 1 FROM categories WHERE parent_id IS NULL
        UNION ALL
        SELECT c.id, cd.depth + 1
        FROM categories c JOIN cat_depth cd ON c.parent_id = cd.id
    )
    SELECT id, depth FROM cat_depth
    """
    return {row["id"]: row["depth"] for row in conn.execute(sql).fetchall()}


# Record Separator (U+001E) — an ASCII control character guaranteed not to
# appear in user-entered slugs; used as a path delimiter inside the recursive
# CTE below so we can split() safely in Python.
_PATH_SEP = chr(30)


def get_category_path_map(conn: sqlite3.Connection) -> dict[int, list[str]]:
    """Return {category_pk: [root_slug, ..., leaf_slug]} for every category.

    Single recursive CTE walk → O(1) queries even for many codenames.
    """
    sql = f"""
    WITH RECURSIVE cat_walk(id, parent_id, slug, path_slugs) AS (
        SELECT id, parent_id, slug, slug
        FROM categories WHERE parent_id IS NULL
        UNION ALL
        SELECT c.id, c.parent_id, c.slug,
               cw.path_slugs || '{_PATH_SEP}' || c.slug
        FROM categories c JOIN cat_walk cw ON c.parent_id = cw.id
    )
    SELECT id, path_slugs FROM cat_walk
    """
    out: dict[int, list[str]] = {}
    for row in conn.execute(sql).fetchall():
        out[row["id"]] = row["path_slugs"].split(_PATH_SEP)
    return out


def get_descendant_ids(conn: sqlite3.Connection, root_pk: int) -> list[int]:
    """Return [root_pk, child_pk, ...] — root plus all transitive descendants."""
    sql = """
    WITH RECURSIVE descendants(id) AS (
        SELECT id FROM categories WHERE id = ?
        UNION ALL
        SELECT c.id FROM categories c JOIN descendants d ON c.parent_id = d.id
    )
    SELECT id FROM descendants
    """
    return [row["id"] for row in conn.execute(sql, (root_pk,)).fetchall()]


def get_subtree_max_relative_depth(
    conn: sqlite3.Connection, root_pk: int
) -> int:
    """Return the max depth of the subtree rooted at root_pk, root itself = 1."""
    sql = """
    WITH RECURSIVE sub(id, depth) AS (
        SELECT id, 1 FROM categories WHERE id = ?
        UNION ALL
        SELECT c.id, s.depth + 1
        FROM categories c JOIN sub s ON c.parent_id = s.id
    )
    SELECT MAX(depth) AS max_depth FROM sub
    """
    row = conn.execute(sql, (root_pk,)).fetchone()
    return row["max_depth"] or 1


def count_children(
    conn: sqlite3.Connection, parent_pk: int, include_archived: bool = False
) -> int:
    """Count direct children of a category."""
    sql = "SELECT COUNT(*) AS c FROM categories WHERE parent_id = ?"
    params: list = [parent_pk]
    if not include_archived:
        sql += " AND is_archived = 0"
    return conn.execute(sql, params).fetchone()["c"]


def count_codenames_in_category(conn: sqlite3.Connection, pk: int) -> int:
    """Count codenames directly bound to this category (no descendants)."""
    return conn.execute(
        "SELECT COUNT(*) AS c FROM codename_inventory WHERE category_id = ?", (pk,)
    ).fetchone()["c"]


def list_categories_flat(
    conn: sqlite3.Connection,
    include_archived: bool = False,
    parent_pk: Optional[int] = None,
    parent_filter_active: bool = False,
) -> list[dict]:
    """List categories as flat rows ordered by (parent_id, sort_order, id).

    parent_filter_active=False  → no filter (all categories)
    parent_filter_active=True, parent_pk=None  → top-level only
    parent_filter_active=True, parent_pk=int   → direct children of that parent
    """
    sql = "SELECT * FROM categories WHERE 1=1"
    params: list = []
    if not include_archived:
        sql += " AND is_archived = 0"
    if parent_filter_active:
        if parent_pk is None:
            sql += " AND parent_id IS NULL"
        else:
            sql += " AND parent_id = ?"
            params.append(parent_pk)
    sql += " ORDER BY COALESCE(parent_id, 0), sort_order, id"
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ---------------------------------------------------------------------------
# codename_inventory CRUD
# ---------------------------------------------------------------------------


def insert_codename(conn: sqlite3.Connection, data: dict) -> int:
    """Insert a single codename. Returns the new row id.

    Expected keys: codename_id, name, name_en, name_zh, category_id (int pk), brief.
    """
    cur = conn.execute(
        """INSERT INTO codename_inventory
           (codename_id, name, name_en, name_zh, category_id, brief)
           VALUES (:codename_id, :name, :name_en, :name_zh, :category_id, :brief)""",
        data,
    )
    return cur.lastrowid  # type: ignore[return-value]


def _hydrate_codename_rows(
    conn: sqlite3.Connection, rows: list[dict]
) -> list[dict]:
    """Attach category_id (public) and category_path to each row; remove internal pk."""
    if not rows:
        return rows
    path_map = get_category_path_map(conn)
    pks = {r["category_id"] for r in rows}
    if not pks:
        return rows
    placeholders = ",".join("?" * len(pks))
    pk_to_public: dict[int, str] = {
        row["id"]: row["category_id"]
        for row in conn.execute(
            f"SELECT id, category_id FROM categories WHERE id IN ({placeholders})",
            tuple(pks),
        ).fetchall()
    }
    for r in rows:
        pk = r["category_id"]
        r["category_path"] = path_map.get(pk, [])
        r["category_id"] = pk_to_public.get(pk, "")
    return rows


def get_codename_by_codename_id(
    conn: sqlite3.Connection, codename_id: str
) -> Optional[dict]:
    """Look up a codename by public id. Raw row (category_id is int pk)."""
    row = conn.execute(
        "SELECT * FROM codename_inventory WHERE codename_id = ?", (codename_id,)
    ).fetchone()
    return dict(row) if row else None


def get_codename_hydrated(
    conn: sqlite3.Connection, codename_id: str
) -> Optional[dict]:
    """Look up a codename and hydrate category_id (public) + category_path."""
    row = get_codename_by_codename_id(conn, codename_id)
    if not row:
        return None
    return _hydrate_codename_rows(conn, [row])[0]


def get_codename_by_name(conn: sqlite3.Connection, name: str) -> Optional[dict]:
    """Look up a codename by its canonical name."""
    row = conn.execute(
        "SELECT * FROM codename_inventory WHERE name = ?", (name,)
    ).fetchone()
    return dict(row) if row else None


def get_random_available(
    conn: sqlite3.Connection,
    count: int,
    category_pks: Optional[list[int]] = None,
) -> list[dict]:
    """Draw *count* random available codenames, optionally restricted to category pks."""
    sql = "SELECT * FROM codename_inventory WHERE status = 'available'"
    params: list = []
    if category_pks is not None:
        if not category_pks:
            return []
        placeholders = ",".join("?" * len(category_pks))
        sql += f" AND category_id IN ({placeholders})"
        params.extend(category_pks)
    sql += " ORDER BY RANDOM() LIMIT ?"
    params.append(count)
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    return _hydrate_codename_rows(conn, rows)


def list_codenames(
    conn: sqlite3.Connection,
    category_pks: Optional[list[int]] = None,
    status: Optional[str] = None,
) -> list[dict]:
    """List codenames with optional filters. Caller expands descendant pks if wanted."""
    sql = "SELECT * FROM codename_inventory WHERE 1=1"
    params: list = []
    if category_pks is not None:
        if not category_pks:
            return []
        placeholders = ",".join("?" * len(category_pks))
        sql += f" AND category_id IN ({placeholders})"
        params.extend(category_pks)
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY added_at DESC"
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    return _hydrate_codename_rows(conn, rows)


def search_codenames(conn: sqlite3.Connection, query: str) -> list[dict]:
    """Search codenames by name/name_en/name_zh/brief."""
    pattern = f"%{query}%"
    sql = """SELECT * FROM codename_inventory
             WHERE name LIKE ? OR name_en LIKE ? OR name_zh LIKE ? OR brief LIKE ?
             ORDER BY added_at DESC"""
    rows = [dict(r) for r in conn.execute(sql, (pattern,) * 4).fetchall()]
    return _hydrate_codename_rows(conn, rows)


def update_codename_status(
    conn: sqlite3.Connection, codename_id: int, new_status: str
) -> None:
    """Update the status of a codename (by integer pk)."""
    conn.execute(
        "UPDATE codename_inventory SET status = ? WHERE id = ?",
        (new_status, codename_id),
    )


_UPDATABLE_COLUMNS = frozenset(
    {"name", "name_en", "name_zh", "category_id", "brief"}
)


def update_codename_fields(
    conn: sqlite3.Connection, codename_id: int, updates: dict
) -> None:
    """Update specified fields of a codename by integer pk."""
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
    """Return inventory statistics grouped by category (direct counts, no rollup)."""
    status_counts: dict[str, int] = {}
    for row in conn.execute(
        "SELECT status, COUNT(*) AS cnt FROM codename_inventory GROUP BY status"
    ).fetchall():
        status_counts[row["status"]] = row["cnt"]
    available = status_counts.get("available", 0)
    assigned = status_counts.get("assigned", 0)
    total = available + assigned

    depths = get_category_depths(conn)
    per_cat: dict[int, dict] = {}
    for row in conn.execute(
        """SELECT category_id, status, COUNT(*) AS cnt
             FROM codename_inventory GROUP BY category_id, status"""
    ).fetchall():
        bucket = per_cat.setdefault(
            row["category_id"], {"total": 0, "available": 0, "assigned": 0}
        )
        bucket[row["status"]] = row["cnt"]
        bucket["total"] += row["cnt"]

    by_category: list[dict] = []
    cat_rows = conn.execute(
        "SELECT id, category_id, slug, name_en, name_zh FROM categories ORDER BY id"
    ).fetchall()
    for row in cat_rows:
        pk = row["id"]
        counts = per_cat.get(pk, {"total": 0, "available": 0, "assigned": 0})
        by_category.append(
            {
                "category_id": row["category_id"],
                "slug": row["slug"],
                "name_en": row["name_en"],
                "name_zh": row["name_zh"],
                "depth": depths.get(pk, 1),
                "total": counts["total"],
                "available": counts["available"],
                "assigned": counts["assigned"],
            }
        )

    return {
        "total": total,
        "available": available,
        "assigned": assigned,
        "by_category": by_category,
    }
