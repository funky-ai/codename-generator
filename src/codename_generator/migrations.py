"""Database migration functions. Each migration is idempotent."""

from __future__ import annotations

import json
import secrets
import sqlite3
import string
from typing import Optional

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
    if not columns:
        return  # table doesn't exist yet (fresh DB handled by SCHEMA_DDL_TABLES)
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
        return  # table doesn't exist yet (fresh DB handled by SCHEMA_DDL_TABLES)
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


# ---------------------------------------------------------------------------
# v4: categories as first-class entities
# ---------------------------------------------------------------------------

_TOP_LEVEL_SEED: list[tuple[str, str, str]] = [
    ("person", "Person", "人物"),
    ("animal", "Animal", "动物"),
]

_PERSON_LEAVES: list[tuple[str, str, str]] = [
    ("philosophy", "Philosophy", "哲学"),
    ("art", "Art", "艺术"),
    ("science", "Science", "科学"),
    ("economics", "Economics", "经济学"),
    ("literature", "Literature", "文学"),
    ("music", "Music", "音乐"),
    ("politics", "Politics", "政治"),
    ("medicine", "Medicine", "医学"),
    ("mathematics", "Mathematics", "数学"),
    ("engineering", "Engineering", "工程"),
]

_ANIMAL_LEAVES: list[tuple[str, str, str]] = [
    ("raptor", "Raptor", "猛禽"),
    ("marine", "Marine", "海洋"),
    ("mammal", "Mammal", "哺乳动物"),
]


def _gen_cat_id(conn: sqlite3.Connection) -> str:
    """Generate a unique CAT-xxxxxxxx id with collision retry."""
    for _ in range(5):
        random_part = "".join(secrets.choice(_ID_ALPHABET) for _ in range(_ID_LENGTH))
        new_id = f"CAT-{random_part}"
        exists = conn.execute(
            "SELECT 1 FROM categories WHERE category_id = ?", (new_id,)
        ).fetchone()
        if not exists:
            return new_id
    raise RuntimeError("Failed to generate unique CAT- id after 5 attempts")


def _seed_default_categories(
    conn: sqlite3.Connection,
) -> dict[tuple[str, Optional[str]], int]:
    """Seed default categories idempotently. Returns mapping used by inventory rebuild.

    Mapping keys:
      ("person", slug)  → person leaf pk (e.g. ("person", "science") → pk)
      ("animal", slug)  → animal leaf pk
      ("person", None)  → person top-level pk (fallback for odd rows)
      ("animal", None)  → animal top-level pk (existing data without sub_theme)
    """
    # Pre-flight lookup-then-insert avoids relying on the partial unique index
    # `idx_categories_top_slug`, which is only created after migrations run on
    # a fresh DB. `UNIQUE(parent_id, slug)` alone doesn't deduplicate NULL
    # parent_id rows in SQLite.
    mapping: dict[tuple[str, Optional[str]], int] = {}

    top_pks: dict[str, int] = {}
    for slug, name_en, name_zh in _TOP_LEVEL_SEED:
        existing = conn.execute(
            "SELECT id FROM categories WHERE slug = ? AND parent_id IS NULL",
            (slug,),
        ).fetchone()
        if existing:
            top_pks[slug] = existing["id"]
        else:
            cat_id = _gen_cat_id(conn)
            cur = conn.execute(
                """INSERT INTO categories (category_id, slug, name_en, name_zh, parent_id)
                   VALUES (?, ?, ?, ?, NULL)""",
                (cat_id, slug, name_en, name_zh),
            )
            top_pks[slug] = cur.lastrowid  # type: ignore[assignment]

    def _seed_leaves(
        top_slug: str, leaves: list[tuple[str, str, str]]
    ) -> None:
        top_pk = top_pks[top_slug]
        for slug, name_en, name_zh in leaves:
            existing = conn.execute(
                "SELECT id FROM categories WHERE slug = ? AND parent_id = ?",
                (slug, top_pk),
            ).fetchone()
            if existing:
                pk = existing["id"]
            else:
                cat_id = _gen_cat_id(conn)
                cur = conn.execute(
                    """INSERT INTO categories
                       (category_id, slug, name_en, name_zh, parent_id)
                       VALUES (?, ?, ?, ?, ?)""",
                    (cat_id, slug, name_en, name_zh, top_pk),
                )
                pk = cur.lastrowid  # type: ignore[assignment]
            mapping[(top_slug, slug)] = pk

    _seed_leaves("person", _PERSON_LEAVES)
    _seed_leaves("animal", _ANIMAL_LEAVES)

    mapping[("person", None)] = top_pks["person"]
    mapping[("animal", None)] = top_pks["animal"]
    return mapping


def _migrate_v4_categories(conn: sqlite3.Connection) -> None:
    """Promote categories to first-class entities. Idempotent.

    1. Seed 2 top-level + 13 leaf default categories.
    2. Rebuild codename_inventory to replace theme/sub_theme with category_id.
    3. Extend logs.action CHECK to include category_* actions.
    """
    seed_mapping = _seed_default_categories(conn)
    conn.commit()

    inv_cols = [
        row[1]
        for row in conn.execute("PRAGMA table_info(codename_inventory)").fetchall()
    ]
    if inv_cols and "theme" in inv_cols and "category_id" not in inv_cols:
        _rebuild_inventory_with_category_id(conn, seed_mapping)

    _extend_logs_action_check(conn)


def _rebuild_inventory_with_category_id(
    conn: sqlite3.Connection,
    seed_mapping: dict[tuple[str, Optional[str]], int],
) -> None:
    """Rename old codename_inventory, recreate with category_id FK, migrate rows."""
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("BEGIN")
    try:
        conn.execute("ALTER TABLE codename_inventory RENAME TO _inventory_v3_old")
        conn.execute("""
            CREATE TABLE codename_inventory (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                codename_id TEXT NOT NULL UNIQUE,
                name        TEXT NOT NULL,
                name_en     TEXT NOT NULL,
                name_zh     TEXT NOT NULL,
                category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                brief       TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'available'
                            CHECK (status IN ('available', 'assigned')),
                added_at    TEXT NOT NULL
                            DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
            )
        """)
        rows = conn.execute("SELECT * FROM _inventory_v3_old").fetchall()
        for row in rows:
            theme = row["theme"]
            sub_theme = row["sub_theme"]
            # Preferred: exact (theme, sub_theme) → leaf. Fallback: theme top-level.
            pk = seed_mapping.get((theme, sub_theme))
            if pk is None:
                pk = seed_mapping.get((theme, None))
            if pk is None:
                top = conn.execute(
                    "SELECT id FROM categories WHERE parent_id IS NULL LIMIT 1"
                ).fetchone()
                if not top:
                    raise RuntimeError(
                        f"No category found to migrate codename {row['codename_id']} "
                        f"(theme={theme}, sub_theme={sub_theme})"
                    )
                pk = top["id"]
            conn.execute(
                """INSERT INTO codename_inventory
                   (id, codename_id, name, name_en, name_zh, category_id,
                    brief, status, added_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["id"],
                    row["codename_id"],
                    row["name"],
                    row["name_en"],
                    row["name_zh"],
                    pk,
                    row["brief"],
                    row["status"],
                    row["added_at"],
                ),
            )
        conn.execute("DROP TABLE _inventory_v3_old")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.execute("PRAGMA foreign_keys=ON")


def _extend_logs_action_check(conn: sqlite3.Connection) -> None:
    """Extend logs.action CHECK to include category_* actions. Idempotent."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='logs'"
    ).fetchone()
    if not row:
        return
    if "'category_added'" in row[0]:
        return

    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("BEGIN")
    try:
        conn.execute("ALTER TABLE logs RENAME TO _logs_v3_old")
        conn.execute("""
            CREATE TABLE logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
                action      TEXT NOT NULL CHECK (action IN (
                    'added', 'assigned', 'updated',
                    'category_added', 'category_updated',
                    'category_archived', 'category_deleted'
                )),
                codename_id TEXT NOT NULL,
                operator    TEXT NOT NULL DEFAULT 'system',
                details     TEXT
            )
        """)
        conn.execute("INSERT INTO logs SELECT * FROM _logs_v3_old")
        conn.execute("DROP TABLE _logs_v3_old")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.execute("PRAGMA foreign_keys=ON")


def run_all_migrations(conn: sqlite3.Connection) -> None:
    """Run all migrations in order. Each is idempotent."""
    _migrate_logs_action_constraint(conn)
    _migrate_inventory_codename_id(conn)
    _migrate_v3_schema(conn)
    _migrate_v4_categories(conn)
