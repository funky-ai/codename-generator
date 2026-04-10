# Codename Generator

A local MCP server for managing project codenames with bilingual (English/Chinese) support.

\u4e00\u4e2a\u672c\u5730 MCP Server\uff0c\u7528\u4e8e\u7ba1\u7406\u9879\u76ee\u4ee3\u53f7\uff0c\u652f\u6301\u4e2d\u82f1\u53cc\u8bed\u3002

## Features / \u529f\u80fd

- **Codename Inventory** \u2014 Maintain a pool of available codenames with SQLite storage
  \u4ee3\u53f7\u5e93\u7ba1\u7406 \u2014 \u57fa\u4e8e SQLite \u7684\u4ee3\u53f7\u5e93\u5b58\u7ba1\u7406
- **Two Themes** \u2014 Notable deceased persons and real animal species
  \u4e24\u5927\u4e3b\u9898 \u2014 \u5df2\u6545\u6770\u51fa\u4eba\u7269\u548c\u771f\u5b9e\u52a8\u7269
- **Irreversible Assignment** \u2014 One codename per project, permanently bound
  \u4e0d\u53ef\u64a4\u9500\u7684\u9886\u7528 \u2014 \u4e00\u4e2a\u4ee3\u53f7\u7ed1\u5b9a\u4e00\u4e2a\u9879\u76ee\uff0c\u6c38\u4e45\u751f\u6548
- **Bilingual** \u2014 Every codename has both English and Chinese names
  \u4e2d\u82f1\u53cc\u8bed \u2014 \u6bcf\u4e2a\u4ee3\u53f7\u540c\u65f6\u6709\u82f1\u6587\u548c\u4e2d\u6587\u540d\u79f0
- **Audit Trail** \u2014 Full logging of all additions and assignments
  \u5ba1\u8ba1\u65e5\u5fd7 \u2014 \u5b8c\u6574\u8bb0\u5f55\u6240\u6709\u5165\u5e93\u548c\u9886\u7528\u64cd\u4f5c
- **Low-stock Warning** \u2014 Alerts when available codenames drop below threshold
  \u5e93\u5b58\u9884\u8b66 \u2014 \u53ef\u7528\u4ee3\u53f7\u4f4e\u4e8e\u9608\u503c\u65f6\u81ea\u52a8\u63d0\u9192

## Quick Start / \u5feb\u901f\u5f00\u59cb

### Prerequisites / \u524d\u7f6e\u8981\u6c42

- macOS or Linux
- [Claude Desktop](https://claude.ai/download)

### Install / \u5b89\u88c5

```bash
# Install uv (Python package manager)
# \u5b89\u88c5 uv\uff08Python \u5305\u7ba1\u7406\u5668\uff09
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install dependencies
# \u514b\u9686\u5e76\u5b89\u88c5\u4f9d\u8d56
git clone https://github.com/funky-ai/codename-generator.git ~/codename-generator
cd ~/codename-generator
uv sync
```

### Configure Claude Desktop / \u914d\u7f6e Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

\u5c06\u4ee5\u4e0b\u5185\u5bb9\u6dfb\u52a0\u5230\u914d\u7f6e\u6587\u4ef6\uff1a

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

Replace `<uv-path>` with output of `which uv`, and `<project-path>` with the project directory.

\u5c06 `<uv-path>` \u66ff\u6362\u4e3a `which uv` \u7684\u8f93\u51fa\uff0c`<project-path>` \u66ff\u6362\u4e3a\u9879\u76ee\u76ee\u5f55\u7684\u7edd\u5bf9\u8def\u5f84\u3002

Restart Claude Desktop, then try: / \u91cd\u542f Claude Desktop\uff0c\u7136\u540e\u8bd5\u8bd5\uff1a

> "Show me the codename inventory stats" / "\u67e5\u770b\u4ee3\u53f7\u5e93\u5b58\u7edf\u8ba1"

## Available Tools / \u53ef\u7528\u5de5\u5177

| Tool | Description / \u63cf\u8ff0 |
|---|---|
| `add_codenames` | Add codenames to inventory / \u6279\u91cf\u6dfb\u52a0\u4ee3\u53f7\u5165\u5e93 |
| `draw_random` | Draw random suggestions (no assignment) / \u968f\u673a\u62bd\u53d6\u5019\u9009\uff08\u4e0d\u5206\u914d\uff09 |
| `assign_codename` | Permanently assign to a project / \u9886\u7528\u4ee3\u53f7\uff08\u4e0d\u53ef\u64a4\u9500\uff09 |
| `list_inventory` | List codenames with filters / \u67e5\u8be2\u4ee3\u53f7\u5e93 |
| `inventory_stats` | Inventory statistics + warnings / \u5e93\u5b58\u7edf\u8ba1 + \u9884\u8b66 |
| `list_assignments` | View all assignments / \u67e5\u770b\u6240\u6709\u9886\u7528\u8bb0\u5f55 |
| `search_codenames` | Search by name or description / \u641c\u7d22\u4ee3\u53f7 |
| `view_logs` | View audit logs / \u67e5\u770b\u5ba1\u8ba1\u65e5\u5fd7 |

## Themes / \u4e3b\u9898

### Person / \u4eba\u540d

Notable deceased individuals who died 20+ years ago with documented positive contributions. All races, genders, ages. Sub-fields: philosophy, art, science, economics, literature, music, etc.

\u53bb\u4e16\u226520\u5e74\u7684\u6770\u51fa\u4eba\u7269\uff0c\u5bf9\u4eba\u7c7b\u6709\u53ef\u67e5\u8bc1\u7684\u6b63\u9762\u8d21\u732e\u3002\u4e0d\u9650\u79cd\u65cf\u3001\u6027\u522b\u3001\u5e74\u9f84\u3002

### Animal / \u52a8\u7269

Real, commonly recognizable animal species. No mythical creatures or species with strong negative associations.

\u771f\u5b9e\u5b58\u5728\u7684\u5e38\u89c1\u52a8\u7269\u3002\u6392\u9664\u795e\u8bdd\u751f\u7269\u548c\u8d1f\u9762\u8054\u60f3\u5f3a\u70c8\u7684\u7269\u79cd\u3002

## Documentation / \u6587\u6863

Detailed guides covering installation, daily usage, and best practices:

\u8be6\u7ec6\u7684\u5b89\u88c5\u3001\u4f7f\u7528\u548c\u6700\u4f73\u5b9e\u8df5\u6307\u5357\uff1a

- [\u4e2d\u6587\u6700\u4f73\u5b9e\u8df5](docs/best-practices-zh.md)
- [English Best Practices](docs/best-practices-en.md)

## Development / \u5f00\u53d1

```bash
# Run tests / \u8fd0\u884c\u6d4b\u8bd5
uv run pytest tests/ -v

# Launch MCP Inspector / \u542f\u52a8 MCP Inspector
uv run fastmcp dev src/codename_generator/server.py
```

## License

MIT
