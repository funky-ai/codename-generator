# 更新日志

本项目的所有重要变更都会记录在此文件中。

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
