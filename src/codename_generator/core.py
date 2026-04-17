"""Business logic for codename inventory management."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from . import db
from .db import DEFAULT_LOG_LIMIT, MAX_CATEGORY_DEPTH
from .models import (
    Assignment,
    Category,
    CategoryInput,
    CategoryStat,
    CategoryUpdate,
    Codename,
    CodenameInput,
    CodenameUpdate,
    InventoryStats,
    LogEntry,
)

LOW_STOCK_THRESHOLD = 5


class CodenameManager:
    """Manages the codename inventory. Each method opens/closes its own connection."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the manager with a database path."""
        self.db_path = db_path
        db.init_db(db_path)

    # ------------------------------------------------------------------
    # Category CRUD
    # ------------------------------------------------------------------

    def create_category(
        self, category: CategoryInput, operator: str = "system"
    ) -> Category:
        """Create a new category. Validates depth (≤ 3) and sibling-slug uniqueness."""
        conn = db.get_connection(self.db_path)
        try:
            parent_pk: Optional[int] = None
            parent_depth = 0
            if category.parent_category_id:
                parent = db.get_category_by_public_id(conn, category.parent_category_id)
                if not parent:
                    raise ValueError(
                        f"Parent category '{category.parent_category_id}' not found"
                    )
                if parent["is_archived"]:
                    raise ValueError(
                        "Cannot create a child under archived parent "
                        f"'{category.parent_category_id}'"
                    )
                parent_pk = parent["id"]
                depths = db.get_category_depths(conn)
                parent_depth = depths.get(parent_pk, 1)
                if parent_depth + 1 > MAX_CATEGORY_DEPTH:
                    raise ValueError(
                        f"Category depth would exceed maximum {MAX_CATEGORY_DEPTH}"
                    )

            # Sibling-slug uniqueness pre-check (DB constraints also enforce this,
            # but checking here yields a friendlier error).
            if parent_pk is None:
                existing = conn.execute(
                    "SELECT 1 FROM categories WHERE slug = ? AND parent_id IS NULL",
                    (category.slug,),
                ).fetchone()
            else:
                existing = conn.execute(
                    "SELECT 1 FROM categories WHERE slug = ? AND parent_id = ?",
                    (category.slug, parent_pk),
                ).fetchone()
            if existing:
                raise ValueError(
                    f"Slug '{category.slug}' already exists under the same parent"
                )

            cat_id = db.generate_category_id(conn)
            pk = db.insert_category(
                conn,
                category_id=cat_id,
                slug=category.slug,
                name_en=category.name_en,
                name_zh=category.name_zh,
                parent_id=parent_pk,
                sort_order=category.sort_order,
            )
            db.insert_log(
                conn,
                action="category_added",
                codename_id=cat_id,
                operator=operator,
                details=json.dumps(
                    {
                        "slug": category.slug,
                        "name_en": category.name_en,
                        "name_zh": category.name_zh,
                        "parent_category_id": category.parent_category_id,
                    },
                    ensure_ascii=False,
                ),
            )
            conn.commit()
            return self._build_category(conn, pk)
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ValueError(str(e)) from e
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def list_categories(
        self,
        include_archived: bool = False,
        parent_category_id: Optional[str] = None,
    ) -> list[Category]:
        """List categories (flat), optionally filtered by direct parent.

        parent_category_id="" means top-level only; None means no filter.
        """
        conn = db.get_connection(self.db_path)
        try:
            parent_pk: Optional[int] = None
            parent_filter_active = False
            if parent_category_id is not None:
                parent_filter_active = True
                if parent_category_id == "":
                    parent_pk = None
                else:
                    parent = db.get_category_by_public_id(conn, parent_category_id)
                    if not parent:
                        raise ValueError(
                            f"Parent category '{parent_category_id}' not found"
                        )
                    parent_pk = parent["id"]
            rows = db.list_categories_flat(
                conn,
                include_archived=include_archived,
                parent_pk=parent_pk,
                parent_filter_active=parent_filter_active,
            )
            depths = db.get_category_depths(conn)
            pk_to_public = {r["id"]: r["category_id"] for r in rows}
            if parent_filter_active and parent_pk is not None:
                parent_row = db.get_category_by_pk(conn, parent_pk)
                if parent_row:
                    pk_to_public[parent_pk] = parent_row["category_id"]
            return [self._row_to_category(r, depths, pk_to_public) for r in rows]
        finally:
            conn.close()

    def get_category_tree(self, include_archived: bool = False) -> list[Category]:
        """Return a nested category tree (top-level nodes with `children` populated)."""
        conn = db.get_connection(self.db_path)
        try:
            rows = db.list_categories_flat(
                conn, include_archived=include_archived
            )
            depths = db.get_category_depths(conn)
            pk_to_public = {r["id"]: r["category_id"] for r in rows}
            nodes: dict[int, Category] = {}
            for r in rows:
                nodes[r["id"]] = self._row_to_category(
                    r, depths, pk_to_public, with_children=True
                )
            roots: list[Category] = []
            for r in rows:
                pk = r["id"]
                parent_pk = r["parent_id"]
                node = nodes[pk]
                if parent_pk is None or parent_pk not in nodes:
                    roots.append(node)
                else:
                    parent_node = nodes[parent_pk]
                    assert parent_node.children is not None
                    parent_node.children.append(node)
            return roots
        finally:
            conn.close()

    def update_category(
        self,
        category_id: str,
        update: CategoryUpdate,
        operator: str = "system",
    ) -> Category:
        """Update a category. Handles re-parent (depth + cycle), slug change
        (with sibling uniqueness), archive toggle, and renames."""
        conn = db.get_connection(self.db_path)
        try:
            existing = db.get_category_by_public_id(conn, category_id)
            if not existing:
                raise ValueError(f"Category '{category_id}' not found")
            pk = existing["id"]

            fields: dict = {}
            old_values: dict = {}
            archive_action: Optional[str] = None

            # Rename / sort_order
            for field in ("slug", "name_en", "name_zh", "sort_order"):
                new_val = getattr(update, field)
                if new_val is not None and new_val != existing[field]:
                    old_values[field] = existing[field]
                    fields[field] = new_val

            # Archive toggle
            if update.is_archived is not None:
                new_archived = 1 if update.is_archived else 0
                if new_archived != existing["is_archived"]:
                    if new_archived == 1:
                        if db.count_codenames_in_category(conn, pk) > 0:
                            raise ValueError(
                                "Cannot archive: codenames are still bound to this category"
                            )
                    old_values["is_archived"] = bool(existing["is_archived"])
                    fields["is_archived"] = new_archived
                    archive_action = "archived" if new_archived == 1 else "unarchived"

            # Re-parent
            if update.parent_category_id is not None:
                new_parent_pk: Optional[int] = None
                if update.parent_category_id != "":
                    new_parent = db.get_category_by_public_id(
                        conn, update.parent_category_id
                    )
                    if not new_parent:
                        raise ValueError(
                            f"New parent '{update.parent_category_id}' not found"
                        )
                    if new_parent["is_archived"]:
                        raise ValueError(
                            "Cannot re-parent under an archived category"
                        )
                    new_parent_pk = new_parent["id"]
                if new_parent_pk != existing["parent_id"]:
                    self._check_reparent_valid(conn, pk, new_parent_pk)
                    old_values["parent_category_id"] = existing["parent_id"]
                    fields["parent_id"] = new_parent_pk

            # Sibling slug uniqueness (if slug or parent changed)
            if "slug" in fields or "parent_id" in fields:
                effective_slug = fields.get("slug", existing["slug"])
                effective_parent = fields.get("parent_id", existing["parent_id"])
                if effective_parent is None:
                    clash = conn.execute(
                        """SELECT 1 FROM categories
                             WHERE slug = ? AND parent_id IS NULL AND id != ?""",
                        (effective_slug, pk),
                    ).fetchone()
                else:
                    clash = conn.execute(
                        """SELECT 1 FROM categories
                             WHERE slug = ? AND parent_id = ? AND id != ?""",
                        (effective_slug, effective_parent, pk),
                    ).fetchone()
                if clash:
                    raise ValueError(
                        f"Slug '{effective_slug}' already exists under the same parent"
                    )

            if not fields:
                raise ValueError("No fields to update")

            conn.execute("BEGIN")
            db.update_category_fields(conn, pk, fields)
            action = (
                "category_archived" if archive_action else "category_updated"
            )
            db.insert_log(
                conn,
                action=action,
                codename_id=category_id,
                operator=operator,
                details=json.dumps(
                    {
                        "slug": existing["slug"],
                        "changed_fields": list(fields.keys()),
                        "old_values": old_values,
                        "archive_action": archive_action,
                    },
                    ensure_ascii=False,
                    default=str,
                ),
            )
            conn.commit()
            return self._build_category(conn, pk)
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ValueError(str(e)) from e
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_category(self, category_id: str, operator: str = "system") -> None:
        """Delete a category. Refused if codenames reference it or non-archived
        subcategories exist underneath."""
        conn = db.get_connection(self.db_path)
        try:
            existing = db.get_category_by_public_id(conn, category_id)
            if not existing:
                raise ValueError(f"Category '{category_id}' not found")
            pk = existing["id"]
            if db.count_codenames_in_category(conn, pk) > 0:
                raise ValueError(
                    "Cannot delete: codenames are still bound to this category"
                )
            if db.count_children(conn, pk, include_archived=False) > 0:
                raise ValueError(
                    "Cannot delete: non-archived subcategories exist under this category"
                )
            conn.execute("BEGIN")
            db.delete_category_row(conn, pk)
            db.insert_log(
                conn,
                action="category_deleted",
                codename_id=category_id,
                operator=operator,
                details=json.dumps(
                    {"slug": existing["slug"]}, ensure_ascii=False
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ValueError(str(e)) from e
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Category helpers
    # ------------------------------------------------------------------

    def _check_reparent_valid(
        self,
        conn: sqlite3.Connection,
        moving_pk: int,
        new_parent_pk: Optional[int],
    ) -> None:
        """Validate re-parent: cycle + max depth."""
        if new_parent_pk is None:
            subtree_height = db.get_subtree_max_relative_depth(conn, moving_pk)
            if subtree_height > MAX_CATEGORY_DEPTH:
                raise ValueError(
                    f"Re-parenting would exceed max depth {MAX_CATEGORY_DEPTH}"
                )
            return

        descendants = set(db.get_descendant_ids(conn, moving_pk))
        if new_parent_pk in descendants:
            raise ValueError(
                "Re-parenting would create a cycle: target parent is a descendant"
            )

        depths = db.get_category_depths(conn)
        new_parent_depth = depths.get(new_parent_pk, 1)
        subtree_height = db.get_subtree_max_relative_depth(conn, moving_pk)
        # New absolute max depth of the subtree = new_parent_depth + subtree_height.
        if new_parent_depth + subtree_height > MAX_CATEGORY_DEPTH:
            raise ValueError(
                f"Re-parenting would exceed max depth {MAX_CATEGORY_DEPTH}"
            )

    def _build_category(self, conn: sqlite3.Connection, pk: int) -> Category:
        """Load a single category by pk into a Category model (no children)."""
        row = db.get_category_by_pk(conn, pk)
        if not row:
            raise ValueError(f"Category pk={pk} disappeared")
        depths = db.get_category_depths(conn)
        pk_to_public = {row["id"]: row["category_id"]}
        if row["parent_id"] is not None:
            parent_row = db.get_category_by_pk(conn, row["parent_id"])
            if parent_row:
                pk_to_public[row["parent_id"]] = parent_row["category_id"]
        return self._row_to_category(row, depths, pk_to_public)

    def _row_to_category(
        self,
        row: dict,
        depths: dict[int, int],
        pk_to_public: dict[int, str],
        with_children: bool = False,
    ) -> Category:
        """Assemble a Category model from a raw DB row."""
        parent_pk = row["parent_id"]
        parent_public = pk_to_public.get(parent_pk) if parent_pk is not None else None
        return Category(
            category_id=row["category_id"],
            slug=row["slug"],
            name_en=row["name_en"],
            name_zh=row["name_zh"],
            parent_category_id=parent_public,
            sort_order=row["sort_order"],
            is_archived=bool(row["is_archived"]),
            created_at=row["created_at"],
            depth=depths.get(row["id"], 1),
            children=[] if with_children else None,
        )

    def _resolve_category_for_write(
        self, conn: sqlite3.Connection, public_id: str
    ) -> dict:
        """Look up a category by public id and ensure it's a non-archived leaf."""
        cat = db.get_category_by_public_id(conn, public_id)
        if not cat:
            raise ValueError(f"Category '{public_id}' not found")
        if cat["is_archived"]:
            raise ValueError(f"Category '{public_id}' is archived")
        has_child = conn.execute(
            "SELECT 1 FROM categories WHERE parent_id = ? LIMIT 1", (cat["id"],)
        ).fetchone()
        if has_child:
            raise ValueError(
                f"Category '{public_id}' is not a leaf; pick a sub-category"
            )
        return cat

    def _resolve_category_filter(
        self,
        conn: sqlite3.Connection,
        category_id: Optional[str],
        include_descendants: bool,
    ) -> Optional[list[int]]:
        """Translate a public category filter into a list of integer pks.

        None  → "no filter"
        []    → "this category exists but has no matches" (short-circuits queries)
        """
        if category_id is None:
            return None
        cat = db.get_category_by_public_id(conn, category_id)
        if not cat:
            raise ValueError(f"Category '{category_id}' not found")
        if include_descendants:
            return db.get_descendant_ids(conn, cat["id"])
        return [cat["id"]]

    # ------------------------------------------------------------------
    # Add codenames
    # ------------------------------------------------------------------

    def add_codenames(
        self, items: list[CodenameInput], operator: str = "system"
    ) -> dict:
        """Add codenames to the inventory in batch.

        Each codename must target a non-archived leaf category.
        Returns: {"added": int, "codename_ids": list[str], "errors": list[str]}
        """
        added = 0
        codename_ids: list[str] = []
        errors: list[str] = []

        conn = db.get_connection(self.db_path)
        try:
            for item in items:
                try:
                    cat = self._resolve_category_for_write(conn, item.category_id)
                    codename_id = db.generate_codename_id(conn)
                    data = {
                        "codename_id": codename_id,
                        "name": item.name,
                        "name_en": item.name_en,
                        "name_zh": item.name_zh,
                        "category_id": cat["id"],
                        "brief": item.brief,
                    }
                    db.insert_codename(conn, data)
                    db.insert_log(
                        conn,
                        action="added",
                        codename_id=codename_id,
                        operator=operator,
                        details=json.dumps(
                            {
                                "name": item.name,
                                "category_id": item.category_id,
                                "category_slug": cat["slug"],
                            },
                            ensure_ascii=False,
                        ),
                    )
                    conn.commit()
                    added += 1
                    codename_ids.append(codename_id)
                except Exception as e:
                    conn.rollback()
                    errors.append(f"{item.name}: {e}")
        finally:
            conn.close()

        return {"added": added, "codename_ids": codename_ids, "errors": errors}

    # ------------------------------------------------------------------
    # Update codename
    # ------------------------------------------------------------------

    def update_codename(
        self, update: CodenameUpdate, operator: str = "system"
    ) -> Codename:
        """Update fields of an existing codename. Returns the updated record.

        If `category_id` is provided it must resolve to a non-archived leaf.
        """
        conn = db.get_connection(self.db_path)
        try:
            existing = db.get_codename_by_codename_id(conn, update.codename_id)
            if not existing:
                raise ValueError(f"Codename '{update.codename_id}' not found")

            fields_to_update: dict = {}
            old_values: dict = {}

            for field in ("name", "name_en", "name_zh", "brief"):
                new_val = getattr(update, field)
                if new_val is not None:
                    old_values[field] = existing[field]
                    fields_to_update[field] = new_val

            if update.category_id is not None:
                new_cat = self._resolve_category_for_write(conn, update.category_id)
                if new_cat["id"] != existing["category_id"]:
                    old_cat_row = db.get_category_by_pk(conn, existing["category_id"])
                    old_values["category_id"] = (
                        old_cat_row["category_id"] if old_cat_row else None
                    )
                    fields_to_update["category_id"] = new_cat["id"]

            if not fields_to_update:
                raise ValueError("No fields to update")

            conn.execute("BEGIN")
            db.update_codename_fields(conn, existing["id"], fields_to_update)
            new_values: dict = {}
            for k in old_values:
                if k == "category_id":
                    new_values[k] = update.category_id
                else:
                    new_values[k] = fields_to_update.get(k)
            db.insert_log(
                conn,
                action="updated",
                codename_id=update.codename_id,
                operator=operator,
                details=json.dumps(
                    {
                        "name": existing["name"],
                        "changed_fields": list(fields_to_update.keys()),
                        "old_values": old_values,
                        "new_values": new_values,
                    },
                    ensure_ascii=False,
                ),
            )
            conn.commit()

            updated = db.get_codename_hydrated(conn, update.codename_id)
            assert updated is not None
            return Codename(**updated)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Draw random
    # ------------------------------------------------------------------

    def draw_random(
        self,
        category_id: Optional[str] = None,
        include_descendants: bool = True,
        count: int = 3,
    ) -> list[Codename]:
        """Draw random available codenames without assigning them.

        category_id: restrict to a category subtree (by default) or direct only.
        """
        conn = db.get_connection(self.db_path)
        try:
            category_pks = self._resolve_category_filter(
                conn, category_id, include_descendants
            )
            rows = db.get_random_available(
                conn, count=count, category_pks=category_pks
            )
            return [Codename(**r) for r in rows]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Assign codename (irreversible)
    # ------------------------------------------------------------------

    def assign_codename(
        self,
        codename_id: str,
        description: Optional[str] = None,
        assigned_by: str = "system",
    ) -> Assignment:
        """Permanently assign a codename. Irreversible."""
        conn = db.get_connection(self.db_path)
        try:
            codename = db.get_codename_by_codename_id(conn, codename_id)
            if not codename:
                raise ValueError(f"Codename '{codename_id}' not found")
            if codename["status"] != "available":
                raise ValueError(f"Codename '{codename_id}' is already assigned")

            assignment_id = db.generate_assignment_id(conn)

            conn.execute("BEGIN")
            db.update_codename_status(conn, codename["id"], "assigned")
            db.insert_assignment(
                conn, assignment_id, codename["id"], description, assigned_by
            )
            db.insert_log(
                conn,
                action="assigned",
                codename_id=codename_id,
                operator=assigned_by,
                details=json.dumps(
                    {"name": codename["name"], "description": description},
                    ensure_ascii=False,
                ),
            )
            conn.commit()

            assignment = db.get_assignment_by_codename(conn, codename["id"])
            assert assignment is not None
            return Assignment(**assignment)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def list_inventory(
        self,
        category_id: Optional[str] = None,
        include_descendants: bool = True,
        status: Optional[str] = None,
    ) -> list[Codename]:
        """List codenames with optional filters by category subtree and status."""
        conn = db.get_connection(self.db_path)
        try:
            category_pks = self._resolve_category_filter(
                conn, category_id, include_descendants
            )
            rows = db.list_codenames(
                conn, category_pks=category_pks, status=status
            )
            return [Codename(**r) for r in rows]
        finally:
            conn.close()

    def list_assignments(self) -> list[Assignment]:
        """List all assignments."""
        conn = db.get_connection(self.db_path)
        try:
            rows = db.get_all_assignments(conn)
            return [Assignment(**r) for r in rows]
        finally:
            conn.close()

    def search(self, query: str) -> list[Codename]:
        """Search codenames by name or description."""
        conn = db.get_connection(self.db_path)
        try:
            rows = db.search_codenames(conn, query)
            return [Codename(**r) for r in rows]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_inventory_stats(self) -> InventoryStats:
        """Return inventory statistics with low-stock warning."""
        conn = db.get_connection(self.db_path)
        try:
            stats = db.get_inventory_stats(conn)
            low_stock = stats["available"] < LOW_STOCK_THRESHOLD
            warning = None
            if low_stock:
                warning = (
                    f"Low stock warning: only {stats['available']} codenames available "
                    f"(threshold: {LOW_STOCK_THRESHOLD}). Consider adding more."
                )
            return InventoryStats(
                total=stats["total"],
                available=stats["available"],
                assigned=stats["assigned"],
                by_category=[CategoryStat(**c) for c in stats["by_category"]],
                low_stock_warning=low_stock,
                warning_message=warning,
            )
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------

    def get_logs(
        self, limit: int = DEFAULT_LOG_LIMIT, action: Optional[str] = None
    ) -> list[LogEntry]:
        """View audit logs."""
        conn = db.get_connection(self.db_path)
        try:
            rows = db.get_logs(conn, limit=limit, action=action)
            return [LogEntry(**r) for r in rows]
        finally:
            conn.close()
