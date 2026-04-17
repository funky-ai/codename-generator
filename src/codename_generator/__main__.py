"""Allow running as ``python -m codename_generator``.

Three entry modes:

- ``python -m codename_generator``       → MCP server (stdio)
- ``python -m codename_generator web``   → user-facing HTTP server (static_user/)
- ``python -m codename_generator admin`` → admin HTTP server (static_admin/)

Default ports: 8000 for ``web``, 8001 for ``admin``. Override with
``--port``, or at deploy time via ``CODENAME_WEB_PORT`` / ``CODENAME_ADMIN_PORT``.
``--host`` defaults to ``127.0.0.1`` (override with ``CODENAME_HOST``).
"""

from __future__ import annotations

import argparse
import os
import sys

_MODE_DEFAULTS = {
    "web": {"port_env": "CODENAME_WEB_PORT", "default_port": 8000, "app_mode": "user"},
    "admin": {"port_env": "CODENAME_ADMIN_PORT", "default_port": 8001, "app_mode": "admin"},
}


def _run_http(subcommand: str, argv: list[str]) -> None:
    """Start a uvicorn HTTP server for the given subcommand (``web`` or ``admin``)."""
    config = _MODE_DEFAULTS[subcommand]
    default_port = int(os.environ.get(config["port_env"], config["default_port"]))
    default_host = os.environ.get("CODENAME_HOST", "127.0.0.1")

    parser = argparse.ArgumentParser(
        prog=f"python -m codename_generator {subcommand}",
        description=f"Codename Generator {subcommand} HTTP server",
    )
    parser.add_argument("--host", default=default_host)
    parser.add_argument("--port", type=int, default=default_port)
    args = parser.parse_args(argv)

    import uvicorn

    from .api import create_app

    uvicorn.run(create_app(config["app_mode"]), host=args.host, port=args.port)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in _MODE_DEFAULTS:
        _run_http(sys.argv[1], sys.argv[2:])
    else:
        from .server import mcp

        mcp.run()


main()
