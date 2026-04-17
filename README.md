# Codename Generator

[中文文档](README-zh.md)

A local MCP server + Web UI for managing project codenames with bilingual (English/Chinese) support.

## Features

- **Codename Inventory** — Maintain a pool of available codenames with SQLite storage
- **Two Themes** — Notable deceased persons and real animal species
- **Irreversible Assignment** — One codename per project, permanently bound
- **Bilingual** — Every codename has both English and Chinese names
- **Audit Trail** — Full logging of all additions and assignments
- **Low-stock Warning** — Alerts when available codenames drop below threshold
- **Web UI** — Responsive web interface (desktop + mobile) with Chinese/English switching
- **Dual Interface** — Use via MCP client (Claude Desktop) or web browser

## Quick Start

### Prerequisites

- macOS or Linux
- [Claude Desktop](https://claude.ai/download)

### Install

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install dependencies
git clone https://github.com/funky-ai/codename-generator.git ~/codename-generator
cd ~/codename-generator
uv sync
```

### Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "codename-generator": {
      "command": "<uv-path>",
      "args": [
        "run",
        "--directory", "<project-path>",
        "python", "-m", "codename_generator"
      ]
    }
  }
}
```

Replace `<uv-path>` with output of `which uv`, and `<project-path>` with the project directory. Both must be absolute paths.

Restart Claude Desktop, then try:

> "Show me the codename inventory stats"

## Available Tools

| Tool | Description |
|---|---|
| `add_codenames` | Add codenames to inventory in batch |
| `draw_random` | Draw random suggestions without assigning |
| `assign_codename` | Permanently assign a codename to a project |
| `update_codename` | Update fields of an existing codename |
| `list_inventory` | List codenames with filters |
| `inventory_stats` | Inventory statistics and low-stock warnings |
| `list_assignments` | View all assignments |
| `search_codenames` | Search by name or description |
| `view_logs` | View audit logs |

## Themes

### Person

Notable deceased individuals who died 20+ years ago with documented positive contributions to humanity. All races, genders, and ages. Sub-fields: philosophy, art, science, economics, literature, music, politics, medicine, mathematics, engineering.

### Animal

Real, commonly recognizable animal species. No mythical creatures or species with strong negative associations.

## Documentation

- [Best Practices Guide](docs/best-practices-en.md)
- [最佳实践指南](docs/best-practices-zh.md)

## Web UI

Starting with 0.1.0 the project ships **two independent web clients** that share the same SQLite database and REST surface but run as separate processes on separate ports:

| Client | Command | Default port | Who it's for | What's inside |
|--------|---------|--------------|--------------|---------------|
| User (public) | `uv run python -m codename_generator web` | `8000` | Project teams browsing / picking codenames | Home, Browse (read-only), Draw (suggestions only), Assignments |
| Admin | `uv run python -m codename_generator admin` | `8001` | Ops / librarians managing the library | Dashboard, Inventory (edit + assign), Add, Draw (with Assign), Assignments, Logs |

```bash
# Run both at once (from separate shells)
uv run python -m codename_generator web     # http://127.0.0.1:8000  → user client
uv run python -m codename_generator admin   # http://127.0.0.1:8001  → admin client

# Override host / ports
CODENAME_HOST=0.0.0.0 CODENAME_WEB_PORT=8080 uv run python -m codename_generator web
uv run python -m codename_generator admin --port 9001
```

Both processes read / write the same `CODENAME_DB_PATH` — SQLite WAL mode safely handles the concurrency. Language can be toggled between Chinese and English on both clients.

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Launch MCP Inspector
uv run fastmcp dev src/codename_generator/server.py

# Frontend development (pnpm workspace: web-admin + web-user + web-shared)
pnpm install                # Install all workspace dependencies (run from repo root)
cd web-admin && pnpm dev    # Vite :5174, proxies /api to http://127.0.0.1:8001 (admin)
cd web-admin && pnpm build  # Build to src/codename_generator/static_admin/
cd web-user  && pnpm dev    # Vite :5173, proxies /api to http://127.0.0.1:8000 (user)
cd web-user  && pnpm build  # Build to src/codename_generator/static_user/
```

## License

Apache 2.0
