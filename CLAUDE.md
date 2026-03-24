# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`cli-skill/` is a distributable Claude Code plugin — pure markdown and JSON, no runnable code. It teaches Claude how to build production-quality Propane CLIs using Bun, Ink, and ANSI patterns extracted from `animations/`, `images/`, `pulse/`, `byline/`, and `battlecards/`.

## Structure

```
.claude-plugin/plugin.json        — registers this as a Claude Code plugin

skills/
  new-cli/SKILL.md                — /new-cli: scaffold a new CLI from scratch
  audit-cli/SKILL.md              — /audit-cli: review an existing CLI, output PLAN.md

agents/
  cli-explorer.md                 — read-only agent: analyzes existing CLI structure
  cli-architect.md                — designs architecture (minimal vs modular)
  cli-reviewer.md                 — reviews generated code (correctness / completeness / plan)

hooks/
  hooks.json                      — PreToolUse convention check + SessionStart context
  check_conventions.py            — warns on hardcoded model IDs, throwing sources, database imports
  load_context.sh                 — reminds Claude of CLI rules at session start

guides/
  01-folder-structure.md          — canonical layout, naming rules, file size limits
  02-ui-patterns.md               — HUD vs Wizard, HTML template, dark palette
  03-file-browser-bridge.md       — Bun fs.watch → SSE → browser → POST back
  04-data-philosophy.md           — no databases, flat files, Claude as query layer
  05-mcp-patterns.md              — MCP server template, path safety, Claude Desktop setup
  06-plugin-ecosystem.md          — curated external plugins, how to compose them
  07-claude-code-patterns.md      — streaming, multi-agent, hooks, status bar, image input
```

## How to work here

No build step. Edit markdown and JSON files directly. When updating a guide:
- Check if either SKILL.md references it and update the reference if the filename changed
- Keep guide numbers sequential; add new guides as `08-`, `09-`, etc.

## Key conventions encoded in the skills

- `src/models.ts` — single source of truth for all model IDs (never hardcode strings)
- `src/configure.ts` — identical across all projects (loadEnv + maskValue)
- `src/sources/types.ts` — SourceResult interface; sources return, never throw
- `.propane/` — runtime state, gitignored; `output/` — generated files, gitignored
- Two menu styles: ANSI HUD (persistent dashboard) or Ink Wizard (step-by-step flow)
- `bun hud` is always the entry command
