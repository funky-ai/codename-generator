# Codename Generator 最佳实践

## 1. 简介

Codename Generator 是一个项目代号管理工具，通过 MCP（Model Context Protocol）与 Claude Desktop 集成，让你在对话中直接管理项目代号。

**它解决什么问题？** 项目启动时临时起名混乱——名字重复、含义泄露产品信息、命名风格不统一。

**核心概念：**

- **代号库（Inventory）**：存储所有代号的数据库，每个代号有"可用"或"已领用"两种状态
- **主题（Theme）**：代号的来源类别，v1 支持两种：
  - **人名主题（person）**：已故的杰出人物（去世≥20年）
  - **动物主题（animal）**：真实存在的常见动物
- **领用（Assign）**：将一个代号绑定到具体项目，**一旦领用不可撤销**

## 2. 前置要求

- macOS 或 Linux
- 能打开终端执行命令（安装阶段需要，日常使用不需要）
- 已安装 [Claude Desktop](https://claude.ai/download)

## 3. 安装

打开终端，依次执行：

```bash
# 1. 安装 uv（Python 包管理器，会自动管理 Python 版本）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 重新加载终端配置（或重开一个终端窗口）
source ~/.zshrc   # zsh 用户
# source ~/.bashrc  # bash 用户

# 3. 下载项目
git clone https://github.com/funky-ai/codename-generator.git ~/codename-generator
cd ~/codename-generator

# 4. 安装依赖（uv 会自动下载 Python 3.12 和所有依赖包）
uv sync
```

整个过程大约 1-2 分钟，取决于网络速度。

## 4. 配置 Claude Desktop

### 4.1 找到配置文件

macOS 路径：
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

可以用任意文本编辑器打开，也可以在终端执行：
```bash
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### 4.2 添加 MCP Server 配置

在配置文件中添加 `mcpServers` 字段（注意保留已有内容）：

```json
{
  "mcpServers": {
    "codename-generator": {
      "command": "<uv-absolute-path>",
      "args": [
        "run",
        "--directory", "<project-absolute-path>",
        "python", "-m", "codename_generator"
      ]
    }
  }
}
```

**替换说明：**
- `<uv-absolute-path>`：uv 的绝对路径，运行 `which uv` 查看（通常是 `~/.local/bin/uv`）
- `<project-absolute-path>`：项目的绝对路径（如 `/Users/yourname/codename-generator`）

> **重要**：必须使用绝对路径，因为 Claude Desktop 不会继承终端的 PATH 环境变量。

### 4.3 重启 Claude Desktop

完全退出 Claude Desktop（不是仅关闭窗口），然后重新打开。

### 4.4 验证连接

在 Claude Desktop 中新建对话，输入：

> "查看代号库存统计"

如果返回类似 `total: 0, available: 0` 的结果，说明连接成功。

## 5. 快速上手（3 分钟）

### 第一步：生成首批代号入库

> "帮我生成 5 个动物主题的代号和 5 个科学家主题的代号，然后添加到库里"

Claude 会生成 10 个中英双语代号（含简介），并自动调用工具入库。

### 第二步：查看库存

> "看看现在库里有什么代号"

你会看到所有代号的列表，包括名称（中英文）、主题、简介和状态。

### 第三步：给项目领用代号

> "我有个新项目叫 Smart Campus，帮我抽几个代号选一个"

Claude 会随机抽取几个候选，展示给你选择。你选定后，Claude 会确认一次再执行领用。

## 6. 日常使用场景

### 新项目需要代号

```
你：新项目 Data Pipeline 需要一个代号
Claude：[抽取 3-5 个候选展示]
你：用 Falcon 吧
Claude：[确认后执行领用，记录到审计日志]
```

### 补充库存

当可用代号少于 5 个时，Claude 会在统计中给出提醒。你可以随时补充：

```
你：再补 10 个代号，动物和人名各一半，人名从哲学和艺术领域选
```

### 查询和搜索

```
你：搜一下和"鹰"有关的代号
你：看看所有动物主题的可用代号
你：Project Alpha 的代号是什么？
```

### 查看领用历史

```
你：看看所有项目的代号分配情况
你：查看最近的操作日志
```

## 7. 最佳实践

### 库存管理

- **保持 20 个以上可用代号**，避免需要时临时生成
- 系统会在可用代号 < 5 时发出库存预警
- 建议每次补充 10-20 个，分批审阅比一次性灌入 100 个更可控

### 主题平衡

- 人名和动物主题各保留一些，给领用者更多选择空间
- 人名主题建议覆盖多个子领域（科学、哲学、艺术等），避免风格单一

### 领用纪律

- **领用不可撤销**——这是设计原则，不是 bug。一旦代号绑定项目就不能更换
- Claude 在执行领用前会主动确认，请认真核对代号再确认

### 代号质量

- 生成后可以浏览检查，如果有不合适的可以提前移除（目前需要直接操作数据库）
- 人名代号要注意文化敏感性——有争议的历史人物不宜作为项目代号

## 8. 代号生成规则速查

### 人名主题（person）

| 规则 | 说明 |
|---|---|
| 去世时间 | ≥20 年（基于当前年份动态计算） |
| 贡献 | 对人类有正面贡献，贡献有据可查 |
| 多样性 | 全球范围，不限种族、性别、年龄 |
| 子领域 | 哲学、艺术、科学、经济、文学、音乐、政治、医学、数学、工程 |
| 名称格式 | 英文 1-2 词，中文 2-4 字 |

### 动物主题（animal）

| 规则 | 说明 |
|---|---|
| 物种 | 真实存在，非神话生物 |
| 辨识度 | 常见、大多数人听过或能想象 |
| 联想 | 排除负面联想强烈的（蟑螂、蛆、水蛭等） |
| 名称格式 | 英文 1-2 词，中文 2-4 字 |
