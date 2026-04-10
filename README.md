# Codename Generator

A local MCP server for managing project codenames with bilingual (English/Chinese) support.

一个本地 MCP Server，用于管理项目代号，支持中英双语。

## Features / 功能

- **Codename Inventory** — Maintain a pool of available codenames with SQLite storage
  代号库管理 — 基于 SQLite 的代号库存管理
- **Two Themes** — Notable deceased persons and real animal species
  两大主题 — 已故杰出人物和真实动物
- **Irreversible Assignment** — One codename per project, permanently bound
  不可撤销的领用 — 一个代号绑定一个项目，永久生效
- **Bilingual** — Every codename has both English and Chinese names
  中英双语 — 每个代号同时有英文和中文名称
- **Audit Trail** — Full logging of all additions and assignments
  审计日志 — 完整记录所有入库和领用操作
- **Low-stock Warning** — Alerts when available codenames drop below threshold
  库存预警 — 可用代号低于阈值时自动提醒

## Quick Start / 快速开始

### Prerequisites / 前置要求

- macOS or Linux
- [Claude Desktop](https://claude.ai/download)

### Install / 安装

```bash
# Install uv (Python package manager)
# 安装 uv（Python 包管理器）
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install dependencies
# 克隆并安装依赖
git clone https://github.com/funky-ai/codename-generator.git ~/codename-generator
cd ~/codename-generator
uv sync
```

### Configure Claude Desktop / 配置 Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

将以下内容添加到配置文件：

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

将 `<uv-path>` 替换为 `which uv` 的输出，`<project-path>` 替换为项目目录的绝对路径。

Restart Claude Desktop, then try: / 重启 Claude Desktop，然后试试：

> "Show me the codename inventory stats" / "查看代号库存统计"

## Available Tools / 可用工具

| Tool | Description / 描述 |
|---|---|
| `add_codenames` | Add codenames to inventory / 批量添加代号入库 |
| `draw_random` | Draw random suggestions (no assignment) / 随机抽取候选（不分配） |
| `assign_codename` | Permanently assign to a project / 领用代号（不可撤销） |
| `list_inventory` | List codenames with filters / 查询代号库 |
| `inventory_stats` | Inventory statistics + warnings / 库存统计 + 预警 |
| `list_assignments` | View all assignments / 查看所有领用记录 |
| `search_codenames` | Search by name or description / 搜索代号 |
| `view_logs` | View audit logs / 查看审计日志 |

## Themes / 主题

### Person / 人名

Notable deceased individuals who died 20+ years ago with documented positive contributions. All races, genders, ages. Sub-fields: philosophy, art, science, economics, literature, music, etc.

去世≥20年的杰出人物，对人类有可查证的正面贡献。不限种族、性别、年龄。

### Animal / 动物

Real, commonly recognizable animal species. No mythical creatures or species with strong negative associations.

真实存在的常见动物。排除神话生物和负面联想强烈的物种。

## Documentation / 文档

Detailed guides covering installation, daily usage, and best practices:

详细的安装、使用和最佳实践指南：

- [中文最佳实践](docs/best-practices-zh.md)
- [English Best Practices](docs/best-practices-en.md)

## Development / 开发

```bash
# Run tests / 运行测试
uv run pytest tests/ -v

# Launch MCP Inspector / 启动 MCP Inspector
uv run fastmcp dev src/codename_generator/server.py
```

## License

MIT
