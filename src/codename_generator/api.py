"""FastAPI REST API for the codename generator.

The same REST surface is served by two independent processes:

- ``user`` mode — public-facing read-mostly UI, mounts ``static_user/``.
- ``admin`` mode — full management UI, mounts ``static_admin/``.

Business logic, database, and API routes are identical between modes; only the
bundled static frontend differs. This lets admins and end users run on separate
ports (and potentially separate hosts) without duplicating any Python code.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .core import CodenameManager
from .db import DEFAULT_LOG_LIMIT
from .models import CodenameInput, CodenameUpdate

AppMode = Literal["user", "admin"]

API_VERSION = "0.0.7"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_PACKAGE_DIR = Path(__file__).resolve().parent
_DEFAULT_DB_PATH = _PACKAGE_DIR.parent.parent / "data" / "codenames.db"

_STATIC_DIRS: dict[AppMode, Path] = {
    "user": _PACKAGE_DIR / "static_user",
    "admin": _PACKAGE_DIR / "static_admin",
}


def _get_db_path() -> Path:
    """Resolve database path at runtime so env var overrides work in tests."""
    return Path(os.environ.get("CODENAME_DB_PATH", str(_DEFAULT_DB_PATH)))


# ---------------------------------------------------------------------------
# Manager singleton (shared across app instances in the same process)
# ---------------------------------------------------------------------------

_manager: CodenameManager | None = None


def get_manager() -> CodenameManager:
    """Lazy-initialize the CodenameManager singleton."""
    global _manager
    if _manager is None:
        _manager = CodenameManager(_get_db_path())
    return _manager


# ---------------------------------------------------------------------------
# Request models (HTTP-specific, not in models.py)
# ---------------------------------------------------------------------------


class AddCodenamesRequest(BaseModel):
    codenames: list[CodenameInput]
    operator: str = "web"


class AssignRequest(BaseModel):
    description: Optional[str] = None
    assigned_by: str = "web"


class UpdateRequest(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    name_zh: Optional[str] = None
    theme: Optional[Literal["person", "animal"]] = None
    sub_theme: Optional[str] = None
    brief: Optional[str] = None
    operator: str = "web"


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app(mode: AppMode = "user") -> FastAPI:
    """Build a FastAPI instance wired up for the requested frontend mode.

    Both modes share identical REST routes; ``mode`` only selects which static
    bundle is mounted at ``/``. The same SQLite database (``CODENAME_DB_PATH``)
    backs every instance — SQLite's WAL mode safely handles concurrent readers
    and writers across processes.
    """
    if mode not in _STATIC_DIRS:
        raise ValueError(f"Unknown app mode: {mode!r}")

    static_dir = _STATIC_DIRS[mode]

    app = FastAPI(title=f"Codename Generator ({mode})", version=API_VERSION)

    cors_origins = os.environ.get("CODENAME_CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ValueError)
    async def _value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    # ---- API routes ----

    @app.get("/api/stats")
    def stats() -> dict:
        """Get inventory statistics with low-stock warnings."""
        return get_manager().get_inventory_stats().model_dump()

    @app.get("/api/codenames")
    def list_codenames(
        theme: Optional[str] = None,
        status: Optional[str] = None,
        sub_theme: Optional[str] = None,
    ) -> list[dict]:
        """List codenames with optional filters by theme, status, and sub_theme."""
        results = get_manager().list_inventory(theme=theme, status=status, sub_theme=sub_theme)
        return [r.model_dump() for r in results]

    @app.get("/api/codenames/search")
    def search_codenames(q: str) -> list[dict]:
        """Search codenames by name (English or Chinese) or description."""
        results = get_manager().search(q)
        return [r.model_dump() for r in results]

    @app.get("/api/codenames/random")
    def draw_random(
        count: int = Query(default=3, ge=1, le=50),
        theme: Optional[str] = None,
    ) -> list[dict]:
        """Draw random available codenames as suggestions (does not assign)."""
        results = get_manager().draw_random(theme=theme, count=count)
        return [r.model_dump() for r in results]

    @app.post("/api/codenames")
    def add_codenames(req: AddCodenamesRequest) -> dict:
        """Add codenames to the inventory in batch."""
        return get_manager().add_codenames(req.codenames, req.operator)

    @app.put("/api/codenames/{codename_id}")
    def update_codename(codename_id: str, req: UpdateRequest) -> dict:
        """Update fields of an existing codename. Partial updates supported."""
        update = CodenameUpdate(
            codename_id=codename_id,
            name=req.name,
            name_en=req.name_en,
            name_zh=req.name_zh,
            theme=req.theme,
            sub_theme=req.sub_theme,
            brief=req.brief,
        )
        result = get_manager().update_codename(update, req.operator)
        return result.model_dump()

    @app.post("/api/codenames/{codename_id}/assign")
    def assign_codename(codename_id: str, req: AssignRequest) -> dict:
        """Permanently assign a codename. This action is IRREVERSIBLE."""
        result = get_manager().assign_codename(
            codename_id, description=req.description, assigned_by=req.assigned_by
        )
        return result.model_dump()

    @app.get("/api/assignments")
    def list_assignments() -> list[dict]:
        """List all codename assignments."""
        results = get_manager().list_assignments()
        return [r.model_dump() for r in results]

    @app.get("/api/logs")
    def view_logs(
        limit: int = Query(default=DEFAULT_LOG_LIMIT, ge=1, le=500),
        action: Optional[str] = None,
    ) -> list[dict]:
        """View audit logs, most recent first."""
        results = get_manager().get_logs(limit=limit, action=action)
        return [r.model_dump() for r in results]

    # ---- Static frontend ----

    @app.get("/")
    def root() -> FileResponse:
        """Serve the bundled frontend for this app mode."""
        return FileResponse(static_dir / "index.html")

    @app.get("/{filename:path}.svg")
    def serve_svg(filename: str) -> FileResponse:
        """Serve SVG files from the static root (logo, icons, etc.)."""
        filepath = static_dir / f"{filename}.svg"
        if filepath.is_file():
            return FileResponse(filepath, media_type="image/svg+xml")
        raise HTTPException(status_code=404, detail="Not found")

    if static_dir.is_dir() and (static_dir / "assets").is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(static_dir / "assets")),
            name="static",
        )

    return app


# Module-level app for direct ASGI invocation (e.g. `uvicorn codename_generator.api:app`).
# Defaults to user mode; the admin frontend is served by constructing a second instance
# via ``create_app("admin")`` from the ``admin`` CLI subcommand.
app = create_app("user")
