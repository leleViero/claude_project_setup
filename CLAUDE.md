# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository demonstrates Claude Code project setup patterns and hook configurations. It contains multiple Claude settings directories showcasing different hook implementations.
This repo will be used in all future projects allowing the distribution and version control of agents and hooks without having to modify the users one every time and create duplicates.

## Architecture

### Claude Settings Structure

The repository contains multiple `.claude` directories with different configurations:

- `src/.claude/` - Root-level Claude settings with bash command logging hook


### Hook Configuration

The hooks capture Bash tool usage and log command + description pairs:
- `src/.claude/settings.json` - Logs to `/logger/bash-command-log.txt`
- `src/.claude/settings.local.json` - Controls hook enablement via `disableAllHooks` flag

## Development Commands

This repository does not contain application code requiring build, test, or lint commands. It serves as a configuration reference for Claude Code setups.

## Working with Hooks

When modifying hook configurations:
- Hooks use JSON input piped to `jq` for processing
- The `matcher` field determines which tool triggers the hook (case-sensitive: "Bash" vs "bash")
- Hook output paths differ between configurations (absolute `/logger/` vs home-relative `~/logger/`)
- Local settings can override hook behavior using `disableAllHooks`
