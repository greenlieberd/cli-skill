# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`cli-skill/` is a distributable Claude Code plugin — pure markdown and JSON, no runnable code. It teaches Claude how to plan, scaffold, audit, and fix production-quality CLI tools using Bun, Ink, and ANSI patterns.

## Structure

```
.claude-plugin/
  plugin.json           — plugin registration (name: cli → /cli:* commands)
  marketplace.json      — marketplace entry

skills/
  cli-explore/SKILL.md  — /cli:explore: read-only analysis of existing CLIs
  cli-plan/SKILL.md     — /cli:plan: planning interview → .cli/plan/ folder
  cli-new/SKILL.md      — /cli:new: plan + scaffold + verify
    assets/             — copy-paste reference files (hud.ts, App.tsx, Frame.tsx, etc.)
  cli-audit/SKILL.md    — /cli:audit: explore + plan + execute (replaces audit-cli + fix-cli)

agents/
  cli-planner.md        — goal-driven planning interview → .cli/plan/ folder
  cli-explorer.md       — read-only analysis of existing CLIs
  cli-architect.md      — architecture design (minimal vs modular)
  cli-reviewer.md       — code review (correctness / completeness / conventions)

rules/                  — 42 subject-named rules with frontmatter + prerequisites
  (see full list below)

hooks/
  hooks.json            — PreToolUse conventions + PostToolUse error capture + Stop session logger + SessionStart context
  check_conventions.py  — warns on model IDs, throwing sources, DB imports (PreToolUse)
  error_capture.py      — buffers bash errors to .cli/sessions/.errors_buffer.jsonl (PostToolUse:Bash)
  session_logger.py     — writes session summary to .cli/sessions/YYYY-MM-DD.jsonl (Stop)
  load_context.sh       — session start reminder, scoped to CLI projects
```

## The .cli/ folder convention

Every project gets a `.cli/` folder Claude Code reads as context:
```
.cli/
  plan/
    CONTEXT.md      — what the project is, architecture, what not to do
    DECISIONS.md    — why each architecture choice was made
    PLAN.md         — living task list, checked off by /cli:audit
  audit/
    EXPLORE.md      — cli:explore findings (architecture map, gaps)
    GAPS.md         — what's missing vs Propane conventions
    FIXES.md        — prioritized improvement list
  tech/
    STACK.md        — deps, versions, entry points, bun scripts
```

## Working here

No build step. Edit markdown and JSON files directly. When adding a rule, use a subject name (`topic.md`) — never `how-to-` prefix or numbers. Every rule must have frontmatter (`name`, `description`, `metadata.tags`) and a Prerequisites block.

## Key conventions enforced

- `src/models.ts` — model IDs only here
- `SourceResult` — sources return, never throw
- No databases — flat files + Claude as query layer
- `bun hud` — always the entry command
- ANSI HUDs must handle terminal resize via `process.stdout.on('resize', redraw)`

## Rules index

**Foundation:** `folder-structure` · `conventions` · `environment-setup` · `configuration`

**UI Structure:** `hud-screens` · `wizard-steps` · `layouts` · `alternate-screen` · `hybrid-interface`

**UI Components:** `colors` · `ascii-art` · `spinners` · `display-system` · `tables` · `tabs` · `keyboard-shortcuts` · `confirmation`

**UI Behavior:** `gentle-terminal` · `rich-input` · `parallelization` · `clipboard` · `notifications`

**Data & Sources:** `source-results` · `flat-files` · `output-files` · `caching` · `limits` · `retry`

**AI:** `models` · `token-spend` · `stream-to-agents`

**Infrastructure:** `logging` · `error-recovery` · `testing` · `update-checker` · `global-install`

**Integration:** `browser-views` · `file-watch` · `mcp-servers` · `workspace-settings` · `plugin-ecosystem`

**Output:** `diff-output`
