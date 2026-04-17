# 更新日志

本项目的所有重要变更都会记录在此文件中。

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
