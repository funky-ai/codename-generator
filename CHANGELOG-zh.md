# 更新日志

本项目的所有重要变更都会记录在此文件中。

## [Unreleased]

### 新增
- **前后台双客户端独立部署。** 原先的单一管理界面拆成两个独立的 pnpm 包与独立进程/端口，后端 SQLite 与 REST 接口完全共享。
  - 新增 `web-user/` 包 —— 面向终端用户的只读客户端。页面：首页（精简版概览，展示 当前可用 / 代号总数 / 已分配 三张卡 + 两个 CTA）、浏览（只读代号库，含搜索 / 主题 / 状态筛选）、随机抽取（仅建议，不含分配按钮）、分配记录（只读）。
  - `web-user/src/lib/user-i18n.ts` —— 更友好的面向公众的中英文案，覆盖在 `@shared/lib/i18n-base` 之上。
  - `web-user` 只从 `@shared/lib/api` 引用 GET 方法（不引用 `addCodenames` / `updateCodename` / `assignCodename`）。
- **新增 CLI 子命令 `admin`。** `python -m codename_generator admin` 在 `8001` 端口启动后台 HTTP 服务器（挂载 `static_admin/`），与 `python -m codename_generator web` 在 `8000` 端口的前台服务器（挂载 `static_user/`）并行运行。
- 新增环境变量 `CODENAME_WEB_PORT` / `CODENAME_ADMIN_PORT` / `CODENAME_HOST`，可覆盖默认绑定地址与端口，无需改代码。
- `api.py` 新增 `create_app(mode)` 工厂函数 —— 根据 `"user"` 或 `"admin"` 返回挂好对应静态目录的 FastAPI 实例。模块顶层 `app` 现在为 `create_app("user")`，因此 `uvicorn codename_generator.api:app` 默认启动前台 bundle。

### 变更
- **破坏性变更（仅影响部署）：** `python -m codename_generator web` 现在启动的是前台客户端，而非后台。要访问后台请使用 `python -m codename_generator admin`。
- 静态产物路径：原 `src/codename_generator/static/` 替换为 `src/codename_generator/static_admin/`（由 `web-admin` 构建）和 `src/codename_generator/static_user/`（由 `web-user` 构建）。`.gitignore` 同步更新。
- `web-admin/vite.config.ts` 构建输出至 `../src/codename_generator/static_admin/`，dev server 代理 `/api` 至 `http://127.0.0.1:8001`（后台进程）。
- FastAPI 应用的 `title` 加上模式后缀（`Codename Generator (user)` / `Codename Generator (admin)`），便于通过 `/openapi.json` 识别进程来源。
- `tests/test_api.py` 静态目录引用更新为 `static_user/`（与模块顶层 `app` 的 user 模式一致）。

### 验证
- `pytest tests/ -v`：77/77 通过。
- `ruff check src/ tests/`：无错误。
- `cd web-admin && pnpm build` 与 `cd web-user && pnpm build` 均成功，分别输出到 `static_admin/` 与 `static_user/`。
- 冒烟测试：两个进程各自服务自己的 bundle（`http://127.0.0.1:8000` → 前台 UI，`http://127.0.0.1:8001` → 后台 UI），两端 `/openapi.json` 版本均为 `0.1.0`，`/api/stats` 返回一致；后台 Draw 有「分配」按钮，前台 Draw 无。

## [0.0.7] - 2026-04-17

### 变更
- **内部重构 —— 无功能或视觉变更。** 为规划中的 0.1.0 前后台客户端拆分做准备，把前端可复用代码抽成 pnpm workspace 下的独立包。
  - `web/` 重命名为 `web-admin/`（后台 SPA）。
  - 新增 `web-shared/` 包，承载 API client（`lib/api.ts`）、`cn` 工具、shadcn UI 基础组件、`useLang` hook 工厂、以及 i18n 的 base 翻译表。
  - 仓库根目录新增 `pnpm-workspace.yaml`，`pnpm-lock.yaml` 移动到根目录。
  - 后台代码通过 `@shared/*` alias 引用共享模块（配置在 `web-admin/vite.config.ts` 与 `tsconfig.json`）。
  - 后台独有的翻译键集中在 `web-admin/src/lib/admin-i18n.ts`，运行时与 `baseTranslations` 合并。
- `uv.lock` 与 FastAPI 应用的 `version=` 字段同步至 0.0.7。
- `CLAUDE.md`、`README.md`、`README-zh.md`、`CONTRIBUTING.md`、`CONTRIBUTING-zh.md`：同步前端命令与架构描述。

### 验证
- `pnpm build` 产出 CSS 与 0.0.6 字节一致（hash 未变）；JS 因 i18n 工厂引入约 240 字节脚手架开销，行为完全一致。
- `pytest tests/ -v`：77/77 通过。

## [0.0.6] - 2026-04-16

### 新增
- **项目 Logo**：CN 标签 logo 集成到 Web 界面头部和浏览器 favicon
- `api.py` 新增 SVG 静态文件路由，支持根路径访问 logo、icons 等资源
- 2 个 SVG 端点新测试（文件存在 + 404）
- 为 `core.py` 和 `server.py` 补充 4 个缺失的 docstring

### 变更
- CLAUDE.md：新增强制工作流规则 — 所有代码变更必须先调用对应工作流

### 修复
- 修正 FastAPI 应用版本号 `0.0.4` → `0.0.6`（v0.0.5 发版时遗漏）
- 用项目品牌 CN logo 替换默认 favicon

## [0.0.5] - 2026-04-13

### 新增
- **Web 界面**：基于 React + shadcn/ui 的响应式网页界面（桌面 + 手机）
- **REST API**：FastAPI 后端（`api.py`），9 个接口封装 CodenameManager
- Web 界面支持中英文切换（偏好存储在 localStorage）
- `python -m codename_generator web` 命令启动 Web 服务
- 24 个新的 API 测试 `tests/test_api.py`（总计 75 个）

### 变更
- `pyproject.toml`：显式添加 `fastapi` 和 `uvicorn` 依赖
- `CLAUDE.md`：架构文档更新，加入 REST 层

### 修复
- CORS 来源改为通过 `CODENAME_CORS_ORIGINS` 环境变量配置（原硬编码为 `*`）
- 移除前端未使用的 `react-router-dom` 依赖
- 为所有 API 路由函数添加 docstring
- 更新 README、CONTRIBUTING（中英双语）补充 Web 前端文档

### 基础设施
- 前端项目位于 `web/`（Vite + React + TypeScript + pnpm）
- 构建产物输出到 `src/codename_generator/static/`
- Vite 开发服务器代理 API 请求到 FastAPI 后端
- 强化 `/workflow-feature` 技能：全栈代码审查、强制文档清单、依赖审计

## [0.0.4] - 2026-04-13

### 新增
- GitHub Actions CI 工作流（push/PR 时自动运行 pytest + ruff）
- `ruff` 代码检查工具（E, F, I 规则）
- `CONTRIBUTING.md` 和 `CONTRIBUTING-zh.md` 贡献指南
- `CLAUDE.md` 项目开发规范和工作流路由
- `list_inventory`（5 条）、`list_assignments`（3 条）、边界输入（4 条）测试
- `update_codename_fields` 新增 SQL 列名白名单校验
- `DEFAULT_LOG_LIMIT` 常量，替代硬编码的 `50`

### 变更
- 迁移函数从 `db.py` 提取到独立的 `migrations.py`
- `get_inventory_stats` 查询优化：4 条合并为 3 条
- `CodenameManager` 初始化从模块级改为延迟初始化 `get_manager()`
- README 工具表补充遗漏的 `update_codename`

### 修复
- 删除 best-practices 中已过时的"一个项目一个代号"约束说明
- 移除未使用的 import（server.py 的 `json`、tests 的 `tempfile`/`Path`）

## [0.0.3] - 2026-04-13

### 安全
- 领用记录新增随机 `assignment_id`（格式：`ASN-xxxxxxxx`，CSPRNG），API 不再暴露内部自增 `id`
- 审计日志 API 不再暴露内部自增 `id`
- 审计日志列从可变的显示名称改为稳定的 `codename_id`（`CN-xxxxxxxx`），改名后审计链路不断裂
- ID 生成增加碰撞重试机制（最多 5 次），碰撞时返回明确错误

### 变更
- `assign_codename`：必填 `project_name` 改为可选 `description` — 代号本身就是项目标识
- 移除"一个项目只能有一个代号"的约束
- `assigned_at` 返回实际 DB 时间戳，不再是空字符串
- 日志 `details` JSON 存 `name`（人读）替代冗余的 `codename_id`（已有独立列）
- Prompt `assign_project_codename` 重命名为 `assign_codename_workflow`（不再需要项目名）

### 迁移
- v3 自动迁移：为已有领用记录生成 `assignment_id`，从日志 details JSON 提取 `codename_id`，`project_name` 重命名为 `description`

## [0.0.2] - 2026-04-12

### 新增
- `codename_id` 作为稳定唯一标识（格式：`CN-xxxxxxxx`，CSPRNG 生成，不可变）
- `update_codename` 工具，支持修正已有代号字段并记录修正日志
- 数据库自动迁移（为已有记录生成 `codename_id`）

### 变更
- 所有查找操作（分配、修正）改用 `codename_id` 替代 `name`
- `name` 降级为纯展示字段（移除 UNIQUE 约束）
- `add_codenames` 返回值：`duplicates` 替换为 `codename_ids`
- `LogEntry.action` 新增 `"updated"` 类型

## [0.0.1] - 2026-04-10

### 新增
- 代号库存管理（入库、搜索、列表）
- 从可用代号中随机抽取
- 代号永久分配到项目
- 人物和动物两种主题及验证规则
- 所有操作的审计日志
- 库存统计及低库存告警
- 双语 README（中文 & 英文）
