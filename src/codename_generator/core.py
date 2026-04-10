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

        Returns: {"added": int, "duplicates": list[str], "errors": list[str]}
        """
        added = 0
        duplicates: list[str] = []
        errors: list[str] = []

        conn = db.get_connection(self.db_path)
        try:
            for item in items:
                if item.theme == "person" and not item.sub_theme:
                    errors.append(f"{item.name}: person theme requires sub_theme")
                    continue
                try:
                    db.insert_codename(conn, item.model_dump())
                    db.insert_log(
                        conn,
                        action="added",
                        codename=item.name,
                        operator=operator,
                        details=json.dumps(
                            {"theme": item.theme, "sub_theme": item.sub_theme},
                            ensure_ascii=False,
                        ),
                    )
                    conn.commit()
                    added += 1
                except Exception as e:
                    conn.rollback()
                    if "UNIQUE constraint" in str(e):
                        duplicates.append(item.name)
                    else:
                        errors.append(f"{item.name}: {e}")
        finally:
            conn.close()

        return {"added": added, "duplicates": duplicates, "errors": errors}

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
        codename_name: str,
        project_name: str,
        assigned_by: str = "system",
    ) -> Assignment:
        """Permanently assign a codename to a project. Irreversible."""
        conn = db.get_connection(self.db_path)
        try:
            codename = db.get_codename_by_name(conn, codename_name)
            if not codename:
                raise ValueError(f"Codename '{codename_name}' not found")
            if codename["status"] != "available":
                raise ValueError(f"Codename '{codename_name}' is already assigned")

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
                codename=codename_name,
                operator=assigned_by,
                details=json.dumps({"project": project_name}, ensure_ascii=False),
            )
            conn.commit()

            return Assignment(
                id=assignment_id,
                codename_id=codename["id"],
                codename_name=codename_name,
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
