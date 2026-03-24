# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`cli-skill/` is a distributable Claude Code plugin — pure markdown and JSON, no runnable code. It teaches Claude how to plan, scaffold, audit, and fix production-quality CLI tools using Bun, Ink, and ANSI patterns.

## Structure

```
.claude-plugin/plugin.json

skills/
  new-cli/SKILL.md          — /new-cli: plan then scaffold a new CLI
    examples/               — copy-paste reference files (hud.ts, App.tsx, Frame.tsx, etc.)
  audit-cli/SKILL.md        — /audit-cli: review existing CLI → .cli/PLAN.md
  fix-cli/SKILL.md          — /fix-cli: execute .cli/PLAN.md one task at a time with commits

agents/
  cli-planner.md            — goal-driven planning interview → .cli/ folder
  cli-explorer.md           — read-only analysis of existing CLIs
  cli-architect.md          — architecture design (minimal vs modular)
  cli-reviewer.md           — code review (correctness / completeness / conventions)

rules/
  folder-structure.md       — canonical layout, .cli/ folder, naming, file size rules
  ui-patterns.md            — HTML template, dark palette, SSE bridge
  file-browser-bridge.md    — Bun fs.watch → SSE → browser → POST back
  data-philosophy.md        — no databases, flat files, Claude as query layer
  mcp-patterns.md           — MCP server template, path safety, Claude Desktop setup
  plugin-ecosystem.md       — external plugins worth composing
  claude-code-patterns.md   — streaming, multi-agent, hooks, status bar, image input
  cli-ux.md                 — navigation, feedback, resize handling, error messages, UX checklist

hooks/
  hooks.json                — convention check (scoped to CLI projects) + session reminder
  check_conventions.py      — warns on hardcoded model IDs, throwing sources, DB imports
  load_context.sh           — session reminder, only fires in CLI projects
```

## The .cli/ folder convention

Every generated project gets a `.cli/` folder that Claude Code reads as context:
- `CONTEXT.md` — what the project is, its architecture, and what not to do
- `DECISIONS.md` — why each architecture choice was made
- `PLAN.md` — living task list that `/fix-cli` reads and checks off

## Working here

No build step. Edit markdown and JSON files directly. When adding a guide, use a task-based name (`feature-name.md`) not a numbered prefix. Update references in both SKILL.md files and this CLAUDE.md.

## Key conventions enforced

- `src/models.ts` — model IDs only here
- `SourceResult` — sources return, never throw
- No databases — flat files + Claude as query layer
- `bun hud` — always the entry command
- ANSI HUDs must handle terminal resize via `process.stdout.on('resize', redraw)`
