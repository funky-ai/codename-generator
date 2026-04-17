# 贡献指南

[English](CONTRIBUTING.md)

## 环境搭建

```bash
git clone https://github.com/funky-ai/codename-generator.git
cd codename-generator
uv sync
```

## 开发

```bash
uv run pytest tests/ -v              # 运行测试
uv run ruff check src/ tests/        # 代码检查
uv run ruff format src/ tests/       # 代码格式化
uv run fastmcp dev src/codename_generator/server.py  # MCP Inspector
uv run python -m codename_generator web              # 前台（用户）HTTP 服务 (:8000)
uv run python -m codename_generator admin            # 后台（管理）HTTP 服务 (:8001)
```

### 前端开发

需要 Node.js 和 pnpm。

前端是一个 pnpm workspace，包含 `web-admin/`（后台 SPA）、`web-user/`（面向终端用户的只读 SPA）和 `web-shared/`（可复用的 API client、UI 组件、i18n 基线）。

```bash
pnpm install                    # 在仓库根目录执行，安装所有 workspace 依赖
cd web-admin && pnpm dev        # Vite :5174，/api 代理到 :8001（后台）
cd web-admin && pnpm build      # 构建到 src/codename_generator/static_admin/
cd web-user  && pnpm dev        # Vite :5173，/api 代理到 :8000（前台）
cd web-user  && pnpm build      # 构建到 src/codename_generator/static_user/
```

## 代码规范

- 使用 [ruff](https://docs.astral.sh/ruff/) 进行代码检查（规则：E, F, I）
- 所有函数签名必须有类型注解
- 所有输入/输出使用 Pydantic 模型

## 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
feat: add batch delete tool
fix: handle empty search query
docs: update README tool table
refactor: extract migrations to separate module
```

## 架构

参见 [CLAUDE.md](CLAUDE.md) 了解项目架构和开发约定。

## 测试

- 业务逻辑测试在 `tests/test_core.py`
- API 接口测试在 `tests/test_api.py`
- 使用 `tmp_path` fixture 实现数据库隔离
- 按功能组织测试类
- 覆盖成功路径和错误路径
