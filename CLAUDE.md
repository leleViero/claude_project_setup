# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository demonstrates Claude Code project setup patterns and hook configurations. It serves as a reusable template for distributing and version controlling Claude Code agents, hooks, and settings across multiple projects.

## Directory Structure

```
.claude/                    # Root-level Claude settings
├── agents/                 # Custom agent definitions
│   └── git-flow-manager.md
├── settings.json          # Hook configurations
└── settings.local.json    # Local overrides and permissions

src/
├── agents/                # Source versions of agent definitions
├── commands/              # Custom slash command definitions (empty placeholder)
├── skills/                # Custom skill definitions (empty placeholder)
└── project_agents/
    └── logger/            # Hook output directory

project_agents/logger/     # Alternative hook output location
```

## Hook System

### Pre-Tool Use Hook

The `.claude/settings.json` contains a `PreToolUse` hook that captures Bash tool invocations:

- **Matcher**: `"Bash"` (case-sensitive)
- **Type**: PowerShell command hook
- **Function**: Dumps stdin (tool invocation JSON) to `project_agents/logger/stdin-dump.txt`
- **Creates**: The logger directory automatically if it doesn't exist

### Permission Configuration

`.claude/settings.local.json` grants automatic approval for Git operations:
- `Bash(git config:*)` - Git configuration commands
- `Bash(git flow:*)` - Git Flow workflow commands

## Custom Agents

### git-flow-manager

A specialized agent for Git Flow workflow management, located at:
- `.claude/agents/git-flow-manager.md` (active configuration)
- `src/agents/git-flow-manager.md` (source/template)

**Capabilities**:
- Branch creation and validation (feature/*, release/*, hotfix/*)
- Conventional commit message formatting
- Release management with semantic versioning
- Pull request generation with gh CLI
- Merge conflict resolution guidance

**Tools Available**: Read, Bash, Grep, Glob, Edit, Write
**Model**: Sonnet

## Usage for New Projects

To use this setup in a new project:

1. Copy `.claude/` directory to the new project root
2. Adjust hook output paths in `settings.json` if needed
3. Customize `settings.local.json` permissions for project-specific commands
4. Add custom agents to `.claude/agents/` as needed
5. Keep source versions in `src/` for version control and distribution

## Development Commands

This repository does not contain application code requiring build, test, or lint commands. It serves as a configuration template for Claude Code setups.
