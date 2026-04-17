"""Tests for the v4 categories migration (idempotency + theme→category mapping)."""

from __future__ import annotations

import sqlite3

from codename_generator.core import CodenameManager
from codename_generator.db import (
    SCHEMA_DDL_INDEXES,
    SCHEMA_DDL_TABLES,
    get_connection,
)
from codename_generator.migrations import run_all_migrations


def _count(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    return conn.execute(sql, params).fetchone()[0]


def _v3_like_schema(conn: sqlite3.Connection) -> None:
    """Bootstrap a database into pre-v4 shape (0.0.7): theme / sub_theme present,
    no categories table, logs CHECK only includes 'added'/'assigned'/'updated'.
    """
    conn.executescript("""
        CREATE TABLE codename_inventory (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            codename_id TEXT NOT NULL UNIQUE,
            name        TEXT NOT NULL,
            name_en     TEXT NOT NULL,
            name_zh     TEXT NOT NULL,
            theme       TEXT NOT NULL CHECK (theme IN ('person', 'animal')),
            sub_theme   TEXT,
            brief       TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'available'
                        CHECK (status IN ('available', 'assigned')),
            added_at    TEXT NOT NULL
                        DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
        );
        CREATE TABLE assignments (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id TEXT NOT NULL UNIQUE,
            codename_id   INTEGER NOT NULL REFERENCES codename_inventory(id),
            description   TEXT,
            assigned_by   TEXT NOT NULL DEFAULT 'system',
            assigned_at   TEXT NOT NULL
                          DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
            UNIQUE(codename_id)
        );
        CREATE TABLE logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL
                        DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
            action      TEXT NOT NULL CHECK (action IN ('added', 'assigned', 'updated')),
            codename_id TEXT NOT NULL,
            operator    TEXT NOT NULL DEFAULT 'system',
            details     TEXT
        );
        CREATE INDEX idx_inventory_status ON codename_inventory(status);
        CREATE INDEX idx_inventory_theme ON codename_inventory(theme);
        CREATE INDEX idx_logs_action ON logs(action);
    """)
    conn.commit()


# ------------------------------------------------------------------
# Fresh DB (empty) migration
# ------------------------------------------------------------------


class TestFreshDB:
    def test_seeds_fifteen_categories(self, tmp_path):
        """Bring up a fresh DB exactly as init_db() does and count seeded rows."""
        db = tmp_path / "fresh.db"
        conn = get_connection(db)
        conn.executescript(SCHEMA_DDL_TABLES)
        run_all_migrations(conn)
        conn.executescript(SCHEMA_DDL_INDEXES)
        try:
            assert _count(conn, "SELECT COUNT(*) FROM categories") == 15
            # 2 top-level
            assert _count(
                conn, "SELECT COUNT(*) FROM categories WHERE parent_id IS NULL"
            ) == 2
            # 10 person leaves + 3 animal leaves = 13 children
            assert _count(
                conn, "SELECT COUNT(*) FROM categories WHERE parent_id IS NOT NULL"
            ) == 13
        finally:
            conn.close()

    def test_seeded_ids_are_cat_format(self, tmp_path):
        db = tmp_path / "fresh.db"
        m = CodenameManager(db)
        cats = m.list_categories()
        for c in cats:
            assert c.category_id.startswith("CAT-")
            assert len(c.category_id) == 12  # CAT- + 8 alphanumeric

    def test_seeded_slugs_match_defaults(self, tmp_path):
        m = CodenameManager(tmp_path / "fresh.db")
        cats = m.list_categories()
        all_slugs = {c.slug for c in cats}
        expected = {
            "person", "animal",
            "philosophy", "art", "science", "economics", "literature",
            "music", "politics", "medicine", "mathematics", "engineering",
            "raptor", "marine", "mammal",
        }
        assert expected <= all_slugs


# ------------------------------------------------------------------
# Upgrade from pre-v4 (0.0.7 shape) with existing data
# ------------------------------------------------------------------


class TestUpgradeFromV3:
    def test_migrates_person_with_sub_theme(self, tmp_path):
        db = tmp_path / "v3.db"
        conn = get_connection(db)
        _v3_like_schema(conn)
        conn.execute(
            """INSERT INTO codename_inventory
               (codename_id, name, name_en, name_zh, theme, sub_theme, brief)
               VALUES ('CN-oldperson', 'Einstein', 'Einstein', '爱因斯坦',
                       'person', 'science', 'Physicist')"""
        )
        conn.commit()
        conn.close()

        m = CodenameManager(db)
        inv = m.list_inventory()
        assert len(inv) == 1
        assert inv[0].codename_id == "CN-oldperson"
        assert inv[0].category_path == ["person", "science"]

    def test_migrates_animal_with_null_sub_theme_to_top_level(self, tmp_path):
        """Pre-v4 animals had sub_theme=NULL. Migrate to animal TOP-LEVEL
        (which is a non-leaf) — this is the documented migration exception;
        new writes will still require leaf targeting.
        """
        db = tmp_path / "v3animal.db"
        conn = get_connection(db)
        _v3_like_schema(conn)
        conn.execute(
            """INSERT INTO codename_inventory
               (codename_id, name, name_en, name_zh, theme, sub_theme, brief)
               VALUES ('CN-oldanimal', 'Falcon', 'Falcon', '隼',
                       'animal', NULL, 'Fast raptor')"""
        )
        conn.commit()
        conn.close()

        m = CodenameManager(db)
        inv = m.list_inventory()
        assert len(inv) == 1
        # category_path lands on the animal top-level (exception, documented).
        assert inv[0].category_path == ["animal"]

    def test_migration_preserves_all_rows_and_ids(self, tmp_path):
        db = tmp_path / "v3many.db"
        conn = get_connection(db)
        _v3_like_schema(conn)
        seed = [
            ("CN-aaaaaaaa", "E", "E", "E", "person", "science", "x"),
            ("CN-bbbbbbbb", "M", "M", "M", "person", "art", "y"),
            ("CN-cccccccc", "P", "P", "P", "person", "medicine", "z"),
            ("CN-dddddddd", "F", "F", "F", "animal", None, "q"),
        ]
        for row in seed:
            conn.execute(
                """INSERT INTO codename_inventory
                   (codename_id, name, name_en, name_zh, theme, sub_theme, brief)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                row,
            )
        conn.commit()
        conn.close()

        m = CodenameManager(db)
        inv = m.list_inventory()
        assert len(inv) == 4
        by_cid = {c.codename_id: c for c in inv}
        assert by_cid["CN-aaaaaaaa"].category_path == ["person", "science"]
        assert by_cid["CN-bbbbbbbb"].category_path == ["person", "art"]
        assert by_cid["CN-cccccccc"].category_path == ["person", "medicine"]
        assert by_cid["CN-dddddddd"].category_path == ["animal"]

    def test_migration_extends_logs_action_check(self, tmp_path):
        """After migration, logs.action CHECK must accept category_* values."""
        db = tmp_path / "v3logs.db"
        conn = get_connection(db)
        _v3_like_schema(conn)
        conn.close()

        m = CodenameManager(db)
        # Trigger a category_added log via create_category
        from codename_generator.models import CategoryInput
        m.create_category(
            CategoryInput(slug="mythic", name_en="Mythic", name_zh="神话")
        )
        logs = m.get_logs(action="category_added")
        assert len(logs) == 1

    def test_post_migration_new_write_requires_leaf(self, tmp_path):
        """Migrated `(animal, NULL)` rows stay valid, but NEW inserts under the
        `animal` top-level must still be rejected."""
        db = tmp_path / "v3leafcheck.db"
        conn = get_connection(db)
        _v3_like_schema(conn)
        conn.execute(
            """INSERT INTO codename_inventory
               (codename_id, name, name_en, name_zh, theme, sub_theme, brief)
               VALUES ('CN-legacy', 'L', 'L', 'L', 'animal', NULL, 'x')"""
        )
        conn.commit()
        conn.close()

        m = CodenameManager(db)
        # Find the animal top-level id
        cats = m.list_categories()
        animal_top = next(c for c in cats if c.slug == "animal" and c.parent_category_id is None)
        from codename_generator.models import CodenameInput
        result = m.add_codenames([
            CodenameInput(
                name="NewAnimal", name_en="New", name_zh="新",
                category_id=animal_top.category_id, brief="x",
            )
        ])
        assert result["added"] == 0
        assert "not a leaf" in result["errors"][0]


# ------------------------------------------------------------------
# Idempotency: running migration twice is a no-op
# ------------------------------------------------------------------


class TestIdempotency:
    def test_fresh_db_second_init_is_noop(self, tmp_path):
        db = tmp_path / "repeat.db"
        m1 = CodenameManager(db)
        n1 = len(m1.list_categories())
        del m1
        m2 = CodenameManager(db)
        n2 = len(m2.list_categories())
        assert n1 == n2 == 15

    def test_migrated_db_second_init_is_noop(self, tmp_path):
        db = tmp_path / "v3_twice.db"
        conn = get_connection(db)
        _v3_like_schema(conn)
        conn.execute(
            """INSERT INTO codename_inventory
               (codename_id, name, name_en, name_zh, theme, sub_theme, brief)
               VALUES ('CN-one', 'E', 'E', 'E', 'person', 'science', 'x')"""
        )
        conn.commit()
        conn.close()

        m1 = CodenameManager(db)
        n_cats = len(m1.list_categories())
        n_inv = len(m1.list_inventory())
        del m1
        m2 = CodenameManager(db)
        assert len(m2.list_categories()) == n_cats
        assert len(m2.list_inventory()) == n_inv

    def test_user_categories_preserved_on_second_init(self, tmp_path):
        db = tmp_path / "user_added.db"
        m1 = CodenameManager(db)
        from codename_generator.models import CategoryInput
        custom = m1.create_category(
            CategoryInput(slug="mythic", name_en="Mythic", name_zh="神话")
        )
        del m1
        m2 = CodenameManager(db)
        slugs = {c.slug for c in m2.list_categories()}
        assert "mythic" in slugs
        # Same CAT- id preserved
        matches = [c for c in m2.list_categories() if c.slug == "mythic"]
        assert matches[0].category_id == custom.category_id

    def test_user_modified_seed_name_preserved(self, tmp_path):
        """If a user renames a seeded category, re-running migrations doesn't
        overwrite their name (INSERT OR IGNORE semantics via pre-flight lookup).
        """
        db = tmp_path / "renamed.db"
        m1 = CodenameManager(db)
        # Find science leaf and rename it
        cats = m1.list_categories()
        sci = next(c for c in cats if c.slug == "science" and c.parent_category_id is not None)
        from codename_generator.models import CategoryUpdate
        m1.update_category(sci.category_id, CategoryUpdate(name_en="Natural Science"))
        del m1
        m2 = CodenameManager(db)
        cats2 = m2.list_categories()
        sci2 = next(c for c in cats2 if c.slug == "science" and c.parent_category_id is not None)
        assert sci2.name_en == "Natural Science"
