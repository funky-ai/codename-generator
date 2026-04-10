# Codename Generator Best Practices

## 1. Introduction

Codename Generator is a project codename management tool that integrates with Claude Desktop via MCP (Model Context Protocol), allowing you to manage project codenames directly through conversation.

**What problem does it solve?** Chaotic naming when starting projects -- duplicate names, names that leak product information, inconsistent naming styles.

**Core concepts:**

- **Inventory**: A database storing all codenames, each with a status of "available" or "assigned"
- **Theme**: The source category for codenames. v1 supports two themes:
  - **Person**: Notable deceased individuals (died 20+ years ago)
  - **Animal**: Real, commonly recognizable animal species
- **Assignment**: Binding a codename to a specific project. **Once assigned, it cannot be revoked.**

## 2. Prerequisites

- macOS or Linux
- Ability to run terminal commands (only needed during installation, not for daily use)
- [Claude Desktop](https://claude.ai/download) installed

## 3. Installation

Open your terminal and run the following commands:

```bash
# 1. Install uv (Python package manager that auto-manages Python versions)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Reload terminal config (or open a new terminal window)
source ~/.zshrc   # zsh users
# source ~/.bashrc  # bash users

# 3. Download the project (replace with actual path)
git clone <repository-url> ~/codename-generator
cd ~/codename-generator

# 4. Install dependencies (uv auto-downloads Python 3.12 and all packages)
uv sync
```

The entire process takes about 1-2 minutes, depending on network speed.

## 4. Configure Claude Desktop

### 4.1 Locate the config file

macOS path:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

Open it with any text editor, or run in terminal:
```bash
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### 4.2 Add MCP Server configuration

Add the `mcpServers` field to the config file (keep existing content):

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

**Replace:**
- `<uv-absolute-path>`: Absolute path to uv, run `which uv` to find it (typically `~/.local/bin/uv`)
- `<project-absolute-path>`: Absolute path to the project (e.g., `/Users/yourname/codename-generator`)

> **Important**: You must use absolute paths because Claude Desktop does not inherit your terminal's PATH environment variable.

### 4.3 Restart Claude Desktop

Fully quit Claude Desktop (not just close the window), then reopen it.

### 4.4 Verify the connection

Start a new conversation in Claude Desktop and type:

> "Show me the codename inventory stats"

If you see a result like `total: 0, available: 0`, the connection is working.

## 5. Quick Start (3 Minutes)

### Step 1: Generate your first batch of codenames

> "Generate 5 animal-themed codenames and 5 scientist-themed codenames, then add them to the inventory"

Claude will generate 10 bilingual codenames (with descriptions) and automatically add them to the inventory.

### Step 2: Check inventory

> "Show me what's in the codename inventory"

You'll see a list of all codenames including names (English and Chinese), theme, description, and status.

### Step 3: Assign a codename to a project

> "I have a new project called Smart Campus, draw a few codenames for me to choose from"

Claude will randomly draw several candidates and present them. After you choose one, Claude will confirm before executing the assignment.

## 6. Daily Usage Scenarios

### New project needs a codename

```
You: I need a codename for the Data Pipeline project
Claude: [draws 3-5 candidates and presents them]
You: Let's go with Falcon
Claude: [confirms, then executes the assignment and logs it]
```

### Replenish inventory

When available codenames drop below 5, Claude will warn you in the stats. You can replenish anytime:

```
You: Add 10 more codenames, half animals and half notable people from philosophy and art
```

### Search and query

```
You: Search for codenames related to "eagle"
You: Show me all available animal-themed codenames
You: What's the codename for Project Alpha?
```

### View assignment history

```
You: Show me all project codename assignments
You: View recent operation logs
```

## 7. Best Practices

### Inventory management

- **Keep 20+ codenames available** to avoid generating on-the-spot when needed
- The system warns when available codenames drop below 5
- Add 10-20 at a time -- reviewing in small batches is more manageable than bulk-importing 100

### Theme balance

- Keep a mix of person and animal themes to give more choice when assigning
- For person themes, cover multiple sub-fields (science, philosophy, art, etc.) to avoid a monotone style

### Assignment discipline

- **Assignment is irreversible** -- this is by design, not a bug. Once a codename is bound to a project, it cannot be changed
- Claude will always confirm before executing an assignment -- double-check the project name and codename
- One project gets one codename; one codename goes to one project

### Codename quality

- Review generated codenames after creation; remove unsuitable ones if needed (currently requires direct database access)
- For person-themed codenames, be mindful of cultural sensitivity -- controversial historical figures are not suitable as project codenames

## 8. Codename Generation Rules Reference

### Person theme

| Rule | Description |
|---|---|
| Time of death | 20+ years ago (dynamically calculated from current year) |
| Contribution | Positive contribution to humanity, documented and verifiable |
| Diversity | Global scope, all races, genders, and ages |
| Sub-fields | Philosophy, art, science, economics, literature, music, politics, medicine, mathematics, engineering |
| Name format | English: 1-2 words; Chinese: 2-4 characters |

### Animal theme

| Rule | Description |
|---|---|
| Species | Real species only, no mythical creatures |
| Recognition | Commonly known, most people have heard of or can picture it |
| Associations | Avoid species with strong negative associations (cockroaches, maggots, leeches, etc.) |
| Name format | English: 1-2 words; Chinese: 2-4 characters |
