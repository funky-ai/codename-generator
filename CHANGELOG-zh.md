# 更新日志

本项目的所有重要变更都会记录在此文件中。

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
