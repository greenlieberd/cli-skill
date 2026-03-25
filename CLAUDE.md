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
  cli-new/SKILL.md      — /cli:cli-new: plan + scaffold + verify
    assets/             — reference files: hud.ts, theme.ts, models.ts, configure.ts, App.tsx, Frame.tsx
  cli-plan/SKILL.md     — /cli:cli-plan: thin wrapper → cli-planner agent → .cli/plan/ folder
  cli-explore/SKILL.md  — /cli:cli-explore: read-only analysis of existing CLIs
  cli-audit/SKILL.md    — /cli:cli-audit: load context → explore → plan → execute tasks with commits
  cli-learn/SKILL.md    — /cli:cli-learn: session logs → project memory (.cli/learnings/)

agents/
  cli-planner.md        — goal-driven planning interview → .cli/plan/ (used by cli-new + cli-plan + cli-audit)
  cli-explorer.md       — read-only codebase analysis → .cli/audit/EXPLORE.md (used by cli-explore + cli-audit)
  cli-architect.md      — architecture blueprint for complex features (used by cli-audit feat tasks)
  cli-reviewer.md       — correctness + convention review (used by cli-new Phase 5, parallel instances)
  cli-learner.md        — session log compression → .cli/learnings/ (used by cli-learn)

rules/                  — 42 subject-named rules, loaded on-demand by interface type (not all at once)
  (see full list below)

hooks/
  hooks.json            — PreToolUse + PostToolUse:Bash + Stop + SessionStart (inline bash for SessionStart)
  check_conventions.py  — warns on model IDs, throwing sources, DB imports (PreToolUse:Write/Edit)
  error_capture.py      — buffers bash errors to .cli/sessions/.errors_buffer.jsonl (PostToolUse:Bash)
  session_logger.py     — writes session summary + token cost to .cli/sessions/YYYY-MM-DD.jsonl (Stop)

tests/
  run.sh                — test runner: ./tests/run.sh [--teardown] [--unit-only]
  unit/                 — Python unit tests for all 3 hook scripts (140 tests, no Claude required)
  fixtures/             — has-violations/ and clean-project/ for convention checker tests
```

## The .cli/ folder convention

Every project gets a `.cli/` folder Claude Code reads as context:
```
.cli/
  plan/               — committed, travels with repo
    CONTEXT.md        — what the project is, architecture, what not to do
    DECISIONS.md      — why each architecture choice was made
    PLAN.md           — living task list, checked off by /cli:audit
  audit/              — committed, travels with repo
    EXPLORE.md        — cli:explore findings (architecture map, gaps)
    GAPS.md           — what's missing vs conventions
    FIXES.md          — prioritized improvement list
  learnings/          — committed, travels with repo
    SUMMARY.md        — extracted patterns, watch-outs (injected at session start)
    patterns.md       — what worked
    watch-out.md      — known gotchas
    decisions.md      — choices already made, don't re-open
  sessions/           — gitignored, personal only
    YYYY-MM-DD.jsonl  — session logs written by Stop hook
    .errors_buffer.jsonl — bash error buffer
```

## Working here

No build step. Edit markdown and JSON files directly. When adding a rule, use a subject name (`topic.md`) — never `how-to-` prefix or numbers. Every rule must have frontmatter (`name`, `description`, `metadata.tags`) and a Prerequisites block.

## Required workflow — use these tools, not manual review

| When | Tool |
|------|------|
| After editing any SKILL.md | `/plugin-dev:skill-reviewer` |
| After any structural change | `/plugin-dev:plugin-validator` |
| Creating a new agent | `/plugin-dev:agent-creator` |

These are mandatory. Don't commit plugin changes without running them. They enforce conventions that are invisible in a text editor.

## Key conventions enforced

- `src/models.ts` — model IDs only here, `{ id, maxTokens }` shape
- `src/theme.ts` — all ANSI color constants, generated from 5 presets at planning time
- `SourceResult` — sources return, never throw; `tokens?` field optional
- No databases — flat files + Claude as query layer
- `bun hud` — always the entry command
- ANSI HUDs must handle terminal resize via `process.stdout.on('resize', redraw)`
- `.cli/plan/` — plan files live in the `plan/` subfolder, not `.cli/` root

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
