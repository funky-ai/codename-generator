"""MCP Server for the codename generator."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from .core import CodenameManager
from .db import DEFAULT_LOG_LIMIT
from .models import CategoryInput, CategoryUpdate, CodenameInput, CodenameUpdate

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = Path(
    os.environ.get(
        "CODENAME_DB_PATH",
        Path(__file__).resolve().parent.parent.parent / "data" / "codenames.db",
    )
)

CURRENT_YEAR = datetime.now().year
DEATH_CUTOFF_YEAR = CURRENT_YEAR - 20

mcp = FastMCP(
    name="Codename Generator",
    instructions=f"""You are a project codename management assistant.

Codenames are organized in a **category tree** (max 3 levels deep). Every codename
must be bound to a **leaf** (non-archived) category via its public `category_id`
(format `CAT-xxxxxxxx`). Two top-level defaults seed on first run: `person` and
`animal`. `person` has ten leaf sub-categories (philosophy / art / science /
economics / literature / music / politics / medicine / mathematics / engineering).
`animal` has three leaf sub-categories (raptor / marine / mammal).

Category guidance:

1. **Person** — Notable deceased persons (died on or before {DEATH_CUTOFF_YEAR})
   who made positive contributions to humanity. All races, genders, ages, and
   fields. Contributions must be documented and verifiable.

2. **Animal** — Real animal species that are commonly recognizable. No mythical
   creatures. Avoid species with strong negative associations (cockroaches,
   maggots, leeches, etc.). Chinese name 2-4 characters, English name 1-2 words.

Workflow: use `get_category_tree` to discover categories, resolve the right
leaf's `category_id`, then call `add_codenames` / `draw_random` / etc. with
that id. Use `create_category` / `update_category` / `delete_category` to
manage the tree itself (keep each codename layer a leaf).""",
)

_manager: CodenameManager | None = None


def get_manager() -> CodenameManager:
    """Lazy-initialize the CodenameManager singleton."""
    global _manager
    if _manager is None:
        _manager = CodenameManager(DB_PATH)
    return _manager


# ---------------------------------------------------------------------------
# Category tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="create_category",
    description="Create a new category. Depth is capped at 3; sibling slugs must be unique. Pass parent_category_id to create a child, or omit for a top-level category.",
)
def create_category(
    slug: str,
    name_en: str,
    name_zh: str,
    parent_category_id: Optional[str] = None,
    sort_order: int = 0,
    operator: str = "system",
) -> dict:
    """Create a category.

    Args:
        slug: Stable machine-readable name, unique under the parent.
        name_en: English display name.
        name_zh: Chinese display name.
        parent_category_id: Parent CAT-xxxxxxxx id; None for top-level.
        sort_order: Display order among siblings (default 0).
        operator: Who is creating this category.

    Returns:
        The created category record (without `children`).
    """
    category = CategoryInput(
        slug=slug,
        name_en=name_en,
        name_zh=name_zh,
        parent_category_id=parent_category_id,
        sort_order=sort_order,
    )
    result = get_manager().create_category(category, operator)
    return result.model_dump()


@mcp.tool(
    name="list_categories",
    description="List categories as a flat list, optionally filtered to direct children of a given parent. Archived categories excluded by default.",
)
def list_categories(
    include_archived: bool = False,
    parent_category_id: Optional[str] = None,
) -> list[dict]:
    """List categories flat.

    Args:
        include_archived: Include archived categories (default False).
        parent_category_id: Filter by direct parent. Use empty string "" for
            top-level only; omit (None) for no parent filter.

    Returns:
        Flat list of category records ordered by (parent_id, sort_order, id).
    """
    results = get_manager().list_categories(
        include_archived=include_archived,
        parent_category_id=parent_category_id,
    )
    return [r.model_dump() for r in results]


@mcp.tool(
    name="get_category_tree",
    description="Return the full category tree as nested Category nodes with children populated. Preferred when building UI selectors.",
)
def get_category_tree(include_archived: bool = False) -> list[dict]:
    """Return categories as a nested tree (top-level nodes with children).

    Args:
        include_archived: Include archived categories (default False).

    Returns:
        Nested list of Category objects; top-level roots each have a `children` array.
    """
    results = get_manager().get_category_tree(include_archived=include_archived)
    return [r.model_dump() for r in results]


@mcp.tool(
    name="update_category",
    description="Update fields of a category (rename, re-sort, re-parent, archive). Pass an empty string for parent_category_id to move to top-level. Depth > 3 and cycles are rejected.",
)
def update_category(
    category_id: str,
    slug: Optional[str] = None,
    name_en: Optional[str] = None,
    name_zh: Optional[str] = None,
    parent_category_id: Optional[str] = None,
    sort_order: Optional[int] = None,
    is_archived: Optional[bool] = None,
    operator: str = "system",
) -> dict:
    """Update a category.

    Args:
        category_id: The CAT-xxxxxxxx id to update.
        slug / name_en / name_zh: New values (optional).
        parent_category_id: CAT id to re-parent; empty string to move to
            top-level; None to leave unchanged.
        sort_order: New sort order.
        is_archived: True to archive (rejected if codenames still reference it),
            False to unarchive.
        operator: Who is making the change.

    Returns:
        The updated category record.
    """
    update = CategoryUpdate(
        slug=slug,
        name_en=name_en,
        name_zh=name_zh,
        parent_category_id=parent_category_id,
        sort_order=sort_order,
        is_archived=is_archived,
    )
    result = get_manager().update_category(category_id, update, operator)
    return result.model_dump()


@mcp.tool(
    name="delete_category",
    description="Delete a category. Refused if any codenames still reference it or any non-archived subcategories exist underneath.",
)
def delete_category(category_id: str, operator: str = "system") -> dict:
    """Delete a category.

    Args:
        category_id: The CAT-xxxxxxxx id to delete.
        operator: Who is performing the deletion.

    Returns:
        {"deleted": category_id} on success.
    """
    get_manager().delete_category(category_id, operator)
    return {"deleted": category_id}


# ---------------------------------------------------------------------------
# Codename tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="add_codenames",
    description="Add one or more codenames to the inventory. Each codename must target a non-archived leaf category via `category_id` (CAT-xxxxxxxx).",
)
def add_codenames(
    codenames: list[dict],
    operator: str = "system",
) -> dict:
    """Add codenames to the available inventory.

    Args:
        codenames: List of codename objects. Each must have: name, name_en,
            name_zh, category_id (CAT-xxxxxxxx, leaf), brief.
        operator: Who is adding these codenames.

    Returns:
        Summary with counts of added, codename_ids, and errors.
    """
    items = [CodenameInput(**c) for c in codenames]
    return get_manager().add_codenames(items, operator)


@mcp.tool(
    name="draw_random",
    description="Draw random available codenames from the inventory as suggestions. Does NOT assign them — use assign_codename to actually assign one. Filter by category_id (defaults to whole subtree).",
)
def draw_random(
    count: int = 3,
    category_id: Optional[str] = None,
    include_descendants: bool = True,
) -> list[dict]:
    """Draw random codename suggestions.

    Args:
        count: Number of codenames to draw (default 3).
        category_id: Restrict to a category subtree (default) or single category.
        include_descendants: If True (default), include descendants of category_id.

    Returns:
        List of available codename objects (each with category_id + category_path).
    """
    results = get_manager().draw_random(
        category_id=category_id,
        include_descendants=include_descendants,
        count=count,
    )
    return [r.model_dump() for r in results]


@mcp.tool(
    name="assign_codename",
    description="Permanently assign a codename. This is IRREVERSIBLE — the codename cannot be unassigned or reused. Confirm with the user before calling.",
)
def assign_codename(
    codename_id: str,
    description: Optional[str] = None,
    assigned_by: str = "system",
) -> dict:
    """Assign a codename. One-way, irreversible.

    Args:
        codename_id: The codename ID to assign (e.g. CN-xxxxxxxx).
        description: Optional brief description of what this codename is for.
        assigned_by: Who is making the assignment.

    Returns:
        The assignment record.
    """
    assignment = get_manager().assign_codename(
        codename_id, description=description, assigned_by=assigned_by
    )
    return assignment.model_dump()


@mcp.tool(
    name="update_codename",
    description="Update fields of an existing codename. Partial updates supported. Pass `category_id` to move the codename to another leaf category (must be non-archived leaf).",
)
def update_codename(
    codename_id: str,
    name: Optional[str] = None,
    name_en: Optional[str] = None,
    name_zh: Optional[str] = None,
    category_id: Optional[str] = None,
    brief: Optional[str] = None,
    operator: str = "system",
) -> dict:
    """Update an existing codename's fields.

    Args:
        codename_id: The codename ID to update (e.g. CN-xxxxxxxx).
        name / name_en / name_zh: New name fields.
        category_id: New category (CAT-xxxxxxxx, leaf).
        brief: New brief description.
        operator: Who is making this update.

    Returns:
        The updated codename record.
    """
    update = CodenameUpdate(
        codename_id=codename_id,
        name=name,
        name_en=name_en,
        name_zh=name_zh,
        category_id=category_id,
        brief=brief,
    )
    result = get_manager().update_codename(update, operator)
    return result.model_dump()


@mcp.tool(
    name="list_inventory",
    description="List codenames in the inventory with optional filters by category and status. By default the category filter includes all descendants.",
)
def list_inventory(
    category_id: Optional[str] = None,
    include_descendants: bool = True,
    status: Optional[str] = None,
) -> list[dict]:
    """List codenames with optional filters.

    Args:
        category_id: Filter by category (CAT-xxxxxxxx); applies to subtree unless
            include_descendants=False.
        include_descendants: Include codenames bound to descendant categories (default).
        status: Filter by 'available' or 'assigned'.

    Returns:
        List of matching codenames.
    """
    results = get_manager().list_inventory(
        category_id=category_id,
        include_descendants=include_descendants,
        status=status,
    )
    return [r.model_dump() for r in results]


@mcp.tool(
    name="inventory_stats",
    description="Get statistics about the codename inventory: total / available / assigned and per-category direct counts (not rolled up to descendants).",
)
def inventory_stats() -> dict:
    """Get inventory statistics and stock level status.

    Returns:
        Stats with total, available, assigned counts, `by_category` list,
        and low-stock warning.
    """
    stats = get_manager().get_inventory_stats()
    return stats.model_dump()


@mcp.tool(
    name="list_assignments",
    description="List all codename assignments.",
)
def list_assignments() -> list[dict]:
    """List all existing assignments.

    Returns:
        List of assignment records with codename and project details.
    """
    results = get_manager().list_assignments()
    return [r.model_dump() for r in results]


@mcp.tool(
    name="search_codenames",
    description="Search codenames by name (English or Chinese) or description. Supports partial matching.",
)
def search_codenames(query: str) -> list[dict]:
    """Search the codename inventory.

    Args:
        query: Search term to match against names and descriptions.

    Returns:
        List of matching codenames.
    """
    results = get_manager().search(query)
    return [r.model_dump() for r in results]


@mcp.tool(
    name="view_logs",
    description="View the audit log of codename and category operations. Filter by action: added / assigned / updated / category_added / category_updated / category_archived / category_deleted.",
)
def view_logs(
    limit: int = DEFAULT_LOG_LIMIT,
    action: Optional[str] = None,
) -> list[dict]:
    """View audit logs.

    Args:
        limit: Maximum number of log entries.
        action: Filter by action type (see description).

    Returns:
        List of log entries, most recent first.
    """
    results = get_manager().get_logs(limit=limit, action=action)
    return [r.model_dump() for r in results]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


@mcp.prompt(
    name="generate_person_codenames",
    description="Generate a batch of person-themed codename candidates for the inventory.",
)
def prompt_generate_persons(count: int = 5, category_slug: str = "science") -> str:
    """Generate a prompt for creating person-themed codename candidates."""
    return f"""Generate {count} codename candidates for the person > {category_slug} leaf category.

Requirements:
- The person must have died on or before {DEATH_CUTOFF_YEAR} (at least 20 years ago)
- They must have made a positive, documented contribution to humanity
- Include diverse representation across races, genders, ages, and cultures
- English name: 1-2 words (typically surname or recognizable name)
- Chinese name: 2-4 characters

Use `get_category_tree` first to resolve the CAT-xxxxxxxx id for person > {category_slug}.

For each candidate, provide this JSON:
{{
  "name": "Einstein",
  "name_en": "Einstein",
  "name_zh": "爱因斯坦",
  "category_id": "CAT-xxxxxxxx",   // the leaf id you resolved
  "brief": "Theoretical physicist who developed the theory of relativity"
}}

After generating, use the add_codenames tool to add them to the inventory."""


@mcp.prompt(
    name="generate_animal_codenames",
    description="Generate a batch of animal-themed codename candidates for the inventory.",
)
def prompt_generate_animals(count: int = 5, category_slug: str = "mammal") -> str:
    """Generate a prompt for creating animal-themed codename candidates."""
    return f"""Generate {count} codename candidates for the animal > {category_slug} leaf category.

Requirements:
- Must be real animal species (no mythical creatures)
- Commonly recognizable (most people would know the animal)
- No strong negative associations (avoid pests, parasites, feared animals)
- Chinese name: 2-4 characters
- English name: 1-2 words

Use `get_category_tree` first to resolve the CAT-xxxxxxxx id for animal > {category_slug}.

For each, provide:
{{
  "name": "Dolphin",
  "name_en": "Dolphin",
  "name_zh": "海豚",
  "category_id": "CAT-xxxxxxxx",
  "brief": "Intelligent marine mammal known for playful behavior and social bonds"
}}

After generating, use the add_codenames tool to add them to the inventory."""


@mcp.prompt(
    name="assign_codename_workflow",
    description="Walk through the process of assigning a codename.",
)
def prompt_assign_workflow() -> str:
    """Generate a prompt for the codename assignment workflow."""
    return """I need to assign a codename.

Please follow these steps:
1. First, call inventory_stats to see what's available
2. Draw 3-5 random suggestions using draw_random
3. Present the options with their names (English + Chinese) and descriptions
4. Wait for me to choose one
5. Once I choose, use assign_codename to permanently assign it

Remember: assignment is IRREVERSIBLE, so confirm with me before proceeding."""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
