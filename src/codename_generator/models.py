"""Pydantic data models for the codename generator."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class CodenameInput(BaseModel):
    """Input for adding a codename to the inventory."""

    name: str = Field(description="Canonical display name (used as unique key)")
    name_en: str = Field(description="English name, 1-2 words")
    name_zh: str = Field(description="Chinese name, 2-4 characters")
    theme: Literal["person", "animal"]
    sub_theme: Optional[str] = Field(
        default=None,
        description="Required for 'person' theme: philosophy/art/science/economics/literature/music/politics/medicine/mathematics/engineering",
    )
    brief: str = Field(description="1-2 sentence description")


class Codename(BaseModel):
    """A codename record from the inventory."""

    id: int
    name: str
    name_en: str
    name_zh: str
    theme: Literal["person", "animal"]
    sub_theme: Optional[str]
    brief: str
    status: Literal["available", "assigned"]
    added_at: str


class Assignment(BaseModel):
    """A codename-to-project assignment record."""

    id: int
    codename_id: int
    codename_name: str
    project_name: str
    assigned_by: str
    assigned_at: str


class LogEntry(BaseModel):
    """An audit log entry."""

    id: int
    timestamp: str
    action: Literal["added", "assigned"]
    codename: str
    operator: str
    details: Optional[str]


class InventoryStats(BaseModel):
    """Statistics about the codename inventory."""

    total: int
    available: int
    assigned: int
    by_theme: dict[str, int]
    available_by_theme: dict[str, int]
    low_stock_warning: bool
    warning_message: Optional[str]
