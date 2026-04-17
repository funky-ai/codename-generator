"""Pydantic data models for the codename generator."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


class CategoryInput(BaseModel):
    """Input for creating a category."""

    slug: str = Field(description="Stable machine-readable name, unique under parent")
    name_en: str = Field(description="English display name")
    name_zh: str = Field(description="Chinese display name")
    parent_category_id: Optional[str] = Field(
        default=None,
        description="Public ID (CAT-xxxxxxxx) of the parent category; None for top-level",
    )
    sort_order: int = Field(default=0, description="Display order among siblings")


class CategoryUpdate(BaseModel):
    """Input for updating a category. Only provided fields are changed."""

    slug: Optional[str] = None
    name_en: Optional[str] = None
    name_zh: Optional[str] = None
    parent_category_id: Optional[str] = Field(
        default=None,
        description=(
            "Public ID of the new parent. Pass to re-parent; None means no change. "
            "Use empty string '' to move to top-level."
        ),
    )
    sort_order: Optional[int] = None
    is_archived: Optional[bool] = None


class Category(BaseModel):
    """A category record, optionally with its children."""

    category_id: str
    slug: str
    name_en: str
    name_zh: str
    parent_category_id: Optional[str]
    sort_order: int
    is_archived: bool
    created_at: str
    depth: int = Field(description="1-based depth from root (top-level=1)")
    children: Optional[list["Category"]] = None
    codename_count: Optional[int] = Field(
        default=None,
        description="Count of codenames bound directly to this category",
    )


class CategoryStat(BaseModel):
    """Per-category inventory stats (direct counts, not rolled up to descendants)."""

    category_id: str
    slug: str
    name_en: str
    name_zh: str
    depth: int
    total: int
    available: int
    assigned: int


# ---------------------------------------------------------------------------
# Codenames
# ---------------------------------------------------------------------------


class CodenameInput(BaseModel):
    """Input for adding a codename to the inventory."""

    name: str = Field(description="Canonical display name")
    name_en: str = Field(description="English name, 1-2 words")
    name_zh: str = Field(description="Chinese name, 2-4 characters")
    category_id: str = Field(
        description="Public category ID (CAT-xxxxxxxx); must be a non-archived leaf"
    )
    brief: str = Field(description="1-2 sentence description")


class CodenameUpdate(BaseModel):
    """Input for updating an existing codename. Only provided fields are changed."""

    codename_id: str = Field(description="The codename ID to update (e.g. CN-xxxxxxxx)")
    name: Optional[str] = None
    name_en: Optional[str] = None
    name_zh: Optional[str] = None
    category_id: Optional[str] = Field(
        default=None,
        description="New category (public CAT-xxxxxxxx). Must be a non-archived leaf.",
    )
    brief: Optional[str] = None


class Codename(BaseModel):
    """A codename record from the inventory."""

    codename_id: str
    name: str
    name_en: str
    name_zh: str
    category_id: str
    category_path: list[str] = Field(
        default_factory=list,
        description="Slug path from root to leaf, e.g. ['person', 'science']",
    )
    brief: str
    status: Literal["available", "assigned"]
    added_at: str


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------


class Assignment(BaseModel):
    """A codename-to-project assignment record."""

    assignment_id: str
    codename_id: str
    codename_name: str
    description: Optional[str]
    assigned_by: str
    assigned_at: str


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------


LogAction = Literal[
    "added",
    "assigned",
    "updated",
    "category_added",
    "category_updated",
    "category_archived",
    "category_deleted",
]


class LogEntry(BaseModel):
    """An audit log entry."""

    timestamp: str
    action: LogAction
    codename_id: str
    operator: str
    details: Optional[str]


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


class InventoryStats(BaseModel):
    """Statistics about the codename inventory."""

    total: int
    available: int
    assigned: int
    by_category: list[CategoryStat]
    low_stock_warning: bool
    warning_message: Optional[str]
