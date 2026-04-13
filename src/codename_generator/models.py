"""Pydantic data models for the codename generator."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class CodenameInput(BaseModel):
    """Input for adding a codename to the inventory."""

    name: str = Field(description="Canonical display name")
    name_en: str = Field(description="English name, 1-2 words")
    name_zh: str = Field(description="Chinese name, 2-4 characters")
    theme: Literal["person", "animal"]
    sub_theme: Optional[str] = Field(
        default=None,
        description=(
            "Required for 'person' theme: philosophy/art/science/economics/"
            "literature/music/politics/medicine/mathematics/engineering"
        ),
    )
    brief: str = Field(description="1-2 sentence description")


class CodenameUpdate(BaseModel):
    """Input for updating an existing codename. Only provided fields are changed."""

    codename_id: str = Field(description="The codename ID to update (e.g. CN-xxxxxxxx)")
    name: Optional[str] = Field(default=None, description="New canonical display name")
    name_en: Optional[str] = Field(default=None, description="New English name")
    name_zh: Optional[str] = Field(default=None, description="New Chinese name")
    theme: Optional[Literal["person", "animal"]] = Field(default=None, description="New theme")
    sub_theme: Optional[str] = Field(
        default=None, description="New sub_theme (required for person theme)"
    )
    brief: Optional[str] = Field(default=None, description="New brief description")


class Codename(BaseModel):
    """A codename record from the inventory."""

    codename_id: str
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

    assignment_id: str
    codename_id: str
    codename_name: str
    description: Optional[str]
    assigned_by: str
    assigned_at: str


class LogEntry(BaseModel):
    """An audit log entry."""

    timestamp: str
    action: Literal["added", "assigned", "updated"]
    codename_id: str
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
