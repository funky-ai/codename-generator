# 代号生成器

[English](README.md)

一个本地 MCP Server + Web 界面，用于管理项目代号，支持中英双语。

## 功能

- **代号库管理** — 基于 SQLite 的代号库存管理
- **两大主题** — 已故杰出人物和真实动物
- **不可撤销的领用** — 一个代号绑定一个项目，永久生效
- **中英双语** — 每个代号同时有英文和中文名称
- **审计日志** — 完整记录所有入库和领用操作
- **库存预警** — 可用代号低于阈值时自动提醒
- **Web 界面** — 响应式网页界面（桌面 + 手机），支持中英文切换
- **双入口** — 通过 MCP 客户端（Claude Desktop）或浏览器使用

## 快速开始

### 前置要求

- macOS 或 Linux
- [Claude Desktop](https://claude.ai/download)

### 安装

```bash
# 安装 uv（Python 包管理器）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆并安装依赖
git clone https://github.com/funky-ai/codename-generator.git ~/codename-generator
cd ~/codename-generator
uv sync
```

### 配置 Claude Desktop

将以下内容添加到 `~/Library/Application Support/Claude/claude_desktop_config.json`：

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

将 `<uv-path>` 替换为 `which uv` 的输出，`<project-path>` 替换为项目目录的绝对路径。

重启 Claude Desktop，然后试试：

> "查看代号库存统计"

## 可用工具

| 工具 | 描述 |
|---|---|
| `add_codenames` | 批量添加代号入库 |
| `draw_random` | 随机抽取候选（不分配） |
| `assign_codename` | 领用代号（不可撤销） |
| `update_codename` | 修改已有代号的字段 |
| `list_inventory` | 查询代号库 |
| `inventory_stats` | 库存统计 + 预警 |
| `list_assignments` | 查看所有领用记录 |
| `search_codenames` | 搜索代号 |
| `view_logs` | 查看审计日志 |

## 主题

### 人名

去世≥20年的杰出人物，对人类有可查证的正面贡献。不限种族、性别、年龄。子领域：哲学、艺术、科学、经济、文学、音乐、政治、医学、数学、工程。

### 动物

真实存在的常见动物。排除神话生物和负面联想强烈的物种。

## 文档

- [最佳实践指南](docs/best-practices-zh.md)
- [Best Practices Guide](docs/best-practices-en.md)

## Web 界面

从 0.1.0 起，项目默认提供 **两个独立的 Web 客户端**。它们共享同一个 SQLite 数据库与 REST 接口，但以两个独立进程、独立端口运行：

| 客户端 | 启动命令 | 默认端口 | 面向谁 | 包含页面 |
|--------|---------|---------|-------|---------|
| 前台（User） | `uv run python -m codename_generator web` | `8000` | 项目团队浏览 / 挑选代号 | 首页、浏览（只读）、随机抽取（仅建议）、分配记录 |
| 后台（Admin） | `uv run python -m codename_generator admin` | `8001` | 运营 / 代号库维护者 | 仪表盘、代号库（含编辑 / 分配）、添加、随机抽取（含分配）、分配记录、操作日志 |

```bash
# 同时运行两个客户端（分别开两个终端）
uv run python -m codename_generator web     # http://127.0.0.1:8000  → 前台
uv run python -m codename_generator admin   # http://127.0.0.1:8001  → 后台

# 通过环境变量 / 参数覆盖主机 / 端口
CODENAME_HOST=0.0.0.0 CODENAME_WEB_PORT=8080 uv run python -m codename_generator web
uv run python -m codename_generator admin --port 9001
```

两个进程读写同一份 `CODENAME_DB_PATH`；SQLite WAL 模式可安全处理并发读写。两个客户端都支持中英文切换。

## 开发

```bash
# 运行测试
uv run pytest tests/ -v

# 启动 MCP Inspector
uv run fastmcp dev src/codename_generator/server.py

# 前端开发（pnpm workspace：web-admin + web-user + web-shared）
pnpm install                # 安装 workspace 依赖（在仓库根目录执行）
cd web-admin && pnpm dev    # Vite :5174，/api 代理到 http://127.0.0.1:8001（后台）
cd web-admin && pnpm build  # 构建到 src/codename_generator/static_admin/
cd web-user  && pnpm dev    # Vite :5173，/api 代理到 http://127.0.0.1:8000（前台）
cd web-user  && pnpm build  # 构建到 src/codename_generator/static_user/
```

## 许可证

Apache 2.0
