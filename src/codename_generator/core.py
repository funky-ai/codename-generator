"""Business logic for codename inventory management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from . import db
from .models import (
    Assignment,
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
        self.db_path = db_path
        db.init_db(db_path)

    # ------------------------------------------------------------------
    # Add codenames
    # ------------------------------------------------------------------

    def add_codenames(
        self, items: list[CodenameInput], operator: str = "system"
    ) -> dict:
        """Add codenames to the inventory in batch.

        Returns: {"added": int, "codename_ids": list[str], "errors": list[str]}
        """
        added = 0
        codename_ids: list[str] = []
        errors: list[str] = []

        conn = db.get_connection(self.db_path)
        try:
            for item in items:
                if item.theme == "person" and not item.sub_theme:
                    errors.append(f"{item.name}: person theme requires sub_theme")
                    continue
                try:
                    codename_id = db.generate_codename_id()
                    data = item.model_dump()
                    data["codename_id"] = codename_id
                    db.insert_codename(conn, data)
                    db.insert_log(
                        conn,
                        action="added",
                        codename=item.name,
                        operator=operator,
                        details=json.dumps(
                            {"codename_id": codename_id, "theme": item.theme, "sub_theme": item.sub_theme},
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
        """Update fields of an existing codename. Returns the updated record."""
        conn = db.get_connection(self.db_path)
        try:
            existing = db.get_codename_by_codename_id(conn, update.codename_id)
            if not existing:
                raise ValueError(f"Codename '{update.codename_id}' not found")

            fields_to_update: dict = {}
            old_values: dict = {}

            for field in ("name", "name_en", "name_zh", "theme", "sub_theme", "brief"):
                new_val = getattr(update, field)
                if new_val is not None:
                    old_values[field] = existing[field]
                    fields_to_update[field] = new_val

            # Theme/sub_theme cross-validation
            effective_theme = fields_to_update.get("theme", existing["theme"])
            if effective_theme == "person":
                effective_sub_theme = fields_to_update.get("sub_theme", existing["sub_theme"])
                if not effective_sub_theme:
                    raise ValueError("Person theme requires sub_theme")
            elif effective_theme == "animal":
                if existing["sub_theme"] and "sub_theme" not in fields_to_update:
                    old_values["sub_theme"] = existing["sub_theme"]
                    fields_to_update["sub_theme"] = None

            if not fields_to_update:
                raise ValueError("No fields to update")

            conn.execute("BEGIN")
            db.update_codename_fields(conn, existing["id"], fields_to_update)
            db.insert_log(
                conn,
                action="updated",
                codename=existing["name"],
                operator=operator,
                details=json.dumps(
                    {
                        "codename_id": update.codename_id,
                        "changed_fields": list(fields_to_update.keys()),
                        "old_values": old_values,
                        "new_values": {k: fields_to_update[k] for k in old_values},
                    },
                    ensure_ascii=False,
                ),
            )
            conn.commit()

            updated = db.get_codename_by_codename_id(conn, update.codename_id)
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
        self, theme: Optional[str] = None, count: int = 3
    ) -> list[Codename]:
        """Draw random available codenames without assigning them."""
        conn = db.get_connection(self.db_path)
        try:
            rows = db.get_random_available(conn, count=count, theme=theme)
            if not rows:
                return []
            return [Codename(**r) for r in rows]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Assign codename (irreversible)
    # ------------------------------------------------------------------

    def assign_codename(
        self,
        codename_id: str,
        project_name: str,
        assigned_by: str = "system",
    ) -> Assignment:
        """Permanently assign a codename to a project. Irreversible."""
        conn = db.get_connection(self.db_path)
        try:
            codename = db.get_codename_by_codename_id(conn, codename_id)
            if not codename:
                raise ValueError(f"Codename '{codename_id}' not found")
            if codename["status"] != "available":
                raise ValueError(f"Codename '{codename_id}' is already assigned")

            existing = db.get_assignment_by_project(conn, project_name)
            if existing:
                raise ValueError(
                    f"Project '{project_name}' already has codename '{existing['codename_name']}'"
                )

            # Atomic transaction
            conn.execute("BEGIN")
            db.update_codename_status(conn, codename["id"], "assigned")
            assignment_id = db.insert_assignment(
                conn, codename["id"], project_name, assigned_by
            )
            db.insert_log(
                conn,
                action="assigned",
                codename=codename["name"],
                operator=assigned_by,
                details=json.dumps(
                    {"codename_id": codename_id, "project": project_name},
                    ensure_ascii=False,
                ),
            )
            conn.commit()

            return Assignment(
                id=assignment_id,
                codename_id=codename_id,
                codename_name=codename["name"],
                project_name=project_name,
                assigned_by=assigned_by,
                assigned_at="",  # will be set by DB default
            )
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
        theme: Optional[str] = None,
        status: Optional[str] = None,
        sub_theme: Optional[str] = None,
    ) -> list[Codename]:
        """List codenames with optional filters."""
        conn = db.get_connection(self.db_path)
        try:
            rows = db.list_codenames(conn, theme=theme, status=status, sub_theme=sub_theme)
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
                **stats,
                low_stock_warning=low_stock,
                warning_message=warning,
            )
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------

    def get_logs(
        self, limit: int = 50, action: Optional[str] = None
    ) -> list[LogEntry]:
        """View audit logs."""
        conn = db.get_connection(self.db_path)
        try:
            rows = db.get_logs(conn, limit=limit, action=action)
            return [LogEntry(**r) for r in rows]
        finally:
            conn.close()
