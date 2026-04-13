"""MCP Server for the codename generator."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from .core import CodenameManager
from .db import DEFAULT_LOG_LIMIT
from .models import CodenameInput, CodenameUpdate

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
You help manage an inventory of codenames drawn from two themes:

1. **Person** — Notable deceased persons (died on or before {DEATH_CUTOFF_YEAR})
   who made positive contributions to humanity. All races, genders, ages, and fields
   (philosophy, art, science, economics, literature, music, politics, medicine,
   mathematics, engineering, etc.). Contributions must be documented and verifiable.

2. **Animal** — Real animal species that are commonly recognizable.
   No mythical creatures. Avoid species with strong negative associations
   (cockroaches, maggots, leeches, etc.). Chinese name 2-4 characters,
   English name 1-2 words.

When generating codename candidates, always provide both English and Chinese names
plus a brief description. Use the tools to add them to the inventory, draw random
suggestions, assign them to projects, and monitor stock levels.""",
)

_manager: CodenameManager | None = None


def get_manager() -> CodenameManager:
    """Lazy-initialize the CodenameManager singleton."""
    global _manager
    if _manager is None:
        _manager = CodenameManager(DB_PATH)
    return _manager


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="add_codenames",
    description="Add one or more codenames to the inventory. For 'person' theme, sub_theme is required (e.g., philosophy/art/science). For 'animal' theme, sub_theme should be omitted.",
)
def add_codenames(
    codenames: list[dict],
    operator: str = "system",
) -> dict:
    """Add codenames to the available inventory.

    Args:
        codenames: List of codename objects. Each must have: name, name_en, name_zh,
                   theme ('person'|'animal'), brief. Person theme also requires sub_theme.
        operator: Who is adding these codenames.

    Returns:
        Summary with counts of added, codename_ids, and errors.
    """
    items = [CodenameInput(**c) for c in codenames]
    return get_manager().add_codenames(items, operator)


@mcp.tool(
    name="draw_random",
    description="Draw random available codenames from the inventory as suggestions. Does NOT assign them — use assign_codename to actually assign one.",
)
def draw_random(
    count: int = 3,
    theme: Optional[str] = None,
) -> list[dict]:
    """Draw random codename suggestions from the available inventory.

    Args:
        count: Number of codenames to draw (default 3).
        theme: Filter by theme ('person' or 'animal'). None for any.

    Returns:
        List of available codename objects.
    """
    results = get_manager().draw_random(theme=theme, count=count)
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
    assignment = get_manager().assign_codename(codename_id, description=description, assigned_by=assigned_by)
    return assignment.model_dump()


@mcp.tool(
    name="update_codename",
    description="Update fields of an existing codename. Partial updates supported — only provided fields are changed. If changing theme to 'person', sub_theme must be provided. If changing to 'animal', sub_theme is automatically cleared.",
)
def update_codename(
    codename_id: str,
    name: Optional[str] = None,
    name_en: Optional[str] = None,
    name_zh: Optional[str] = None,
    theme: Optional[str] = None,
    sub_theme: Optional[str] = None,
    brief: Optional[str] = None,
    operator: str = "system",
) -> dict:
    """Update an existing codename's fields.

    Args:
        codename_id: The codename ID to update (e.g. CN-xxxxxxxx).
        name: New canonical display name.
        name_en: New English name.
        name_zh: New Chinese name.
        theme: New theme ('person' or 'animal').
        sub_theme: New sub-theme. Required when theme is 'person'.
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
        theme=theme,
        sub_theme=sub_theme,
        brief=brief,
    )
    result = get_manager().update_codename(update, operator)
    return result.model_dump()


@mcp.tool(
    name="list_inventory",
    description="List codenames in the inventory with optional filters by theme, status, and sub_theme.",
)
def list_inventory(
    theme: Optional[str] = None,
    status: Optional[str] = None,
    sub_theme: Optional[str] = None,
) -> list[dict]:
    """List codenames with optional filters.

    Args:
        theme: Filter by 'person' or 'animal'.
        status: Filter by 'available' or 'assigned'.
        sub_theme: Filter by sub-theme (e.g., 'philosophy', 'science').

    Returns:
        List of matching codenames.
    """
    results = get_manager().list_inventory(theme=theme, status=status, sub_theme=sub_theme)
    return [r.model_dump() for r in results]


@mcp.tool(
    name="inventory_stats",
    description="Get statistics about the codename inventory including total, available, assigned counts by theme, and low-stock warnings.",
)
def inventory_stats() -> dict:
    """Get inventory statistics and stock level status.

    Returns:
        Statistics with total, available, assigned counts, theme breakdowns, and warnings.
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
    description="View the audit log of codename additions and assignments.",
)
def view_logs(
    limit: int = DEFAULT_LOG_LIMIT,
    action: Optional[str] = None,
) -> list[dict]:
    """View audit logs.

    Args:
        limit: Maximum number of log entries.
        action: Filter by action type ('added', 'assigned', or 'updated').

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
def prompt_generate_persons(count: int = 5, sub_theme: str = "science") -> str:
    return f"""Generate {count} codename candidates for the 'person' theme with sub_theme '{sub_theme}'.

Requirements:
- The person must have died on or before {DEATH_CUTOFF_YEAR} (at least 20 years ago)
- They must have made a positive, documented contribution to humanity
- Include diverse representation across races, genders, ages, and cultures
- English name: 1-2 words (typically surname or recognizable name)
- Chinese name: 2-4 characters

For each candidate, provide this JSON:
{{
  "name": "Einstein",
  "name_en": "Einstein",
  "name_zh": "爱因斯坦",
  "theme": "person",
  "sub_theme": "{sub_theme}",
  "brief": "Theoretical physicist who developed the theory of relativity"
}}

After generating, use the add_codenames tool to add them to the inventory."""


@mcp.prompt(
    name="generate_animal_codenames",
    description="Generate a batch of animal-themed codename candidates for the inventory.",
)
def prompt_generate_animals(count: int = 5) -> str:
    return f"""Generate {count} codename candidates for the 'animal' theme.

Requirements:
- Must be real animal species (no mythical creatures)
- Commonly recognizable (most people would know the animal)
- No strong negative associations (avoid pests, parasites, feared animals)
- Chinese name: 2-4 characters
- English name: 1-2 words

For each, provide:
{{
  "name": "Dolphin",
  "name_en": "Dolphin",
  "name_zh": "海豚",
  "theme": "animal",
  "sub_theme": null,
  "brief": "Intelligent marine mammal known for playful behavior and social bonds"
}}

After generating, use the add_codenames tool to add them to the inventory."""


@mcp.prompt(
    name="assign_codename_workflow",
    description="Walk through the process of assigning a codename.",
)
def prompt_assign_workflow() -> str:
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
