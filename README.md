# Codename Generator

[中文文档](README-zh.md)

A local MCP server for managing project codenames with bilingual (English/Chinese) support.

## Features

- **Codename Inventory** — Maintain a pool of available codenames with SQLite storage
- **Two Themes** — Notable deceased persons and real animal species
- **Irreversible Assignment** — One codename per project, permanently bound
- **Bilingual** — Every codename has both English and Chinese names
- **Audit Trail** — Full logging of all additions and assignments
- **Low-stock Warning** — Alerts when available codenames drop below threshold

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

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Launch MCP Inspector
uv run fastmcp dev src/codename_generator/server.py
```

## License

MIT
