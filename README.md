# cli-skill

A Claude Code plugin for building production-quality CLI tools with Bun, Ink, and ANSI patterns.

Five skills under the `/cli:` namespace:

| Skill | Job |
|-------|-----|
| **`/cli:explore`** | Understand what's in an existing CLI — read-only analysis, no changes |
| **`/cli:plan`** | Define what to build — interview, architecture recommendation, plan files |
| **`/cli:new`** | Build from scratch — plan → scaffold → review → verify |
| **`/cli:audit`** | Improve what exists — explore → plan → execute → commit |
| **`/cli:learn`** | Extract session patterns into project memory — runs after a few sessions |

Skills compose: `cli:new` runs the planner internally. `cli:audit` runs the explorer and planner internally. Run `cli:explore` or `cli:plan` standalone when you want just that phase.

---

## Install

```bash
claude plugin marketplace add https://github.com/greenlieberd/cli-skill
claude plugin install cli@cli
```

Restart Claude Code, then:
```
/cli:new
```

You should see the planning interview start.

### Update

```bash
claude plugin update cli
```

### Uninstall

```bash
claude plugin uninstall cli
claude plugin marketplace remove cli
```

---

## Usage

### Build a new CLI

```
/cli:new
```

Or pass a name to skip the first question:

```
/cli:new my-tool
```

### Understand an existing CLI

```
/cli:explore /path/to/your/cli
```

Read-only. Writes findings to `.cli/audit/EXPLORE.md`. Good first step before auditing or planning changes.

### Plan changes or a new feature

```
/cli:plan /path/to/your/cli
```

Runs a planning interview. If `.cli/audit/EXPLORE.md` exists from a prior explore, skips questions already answered by the code. Writes `.cli/plan/CONTEXT.md`, `DECISIONS.md`, `PLAN.md`.

### Improve an existing CLI

```
/cli:audit /path/to/your/cli
```

Full cycle: explores what's there → asks what you want to change → writes a plan → executes task by task with commits. Skips phases that are already done.

---

## The `.cli/` folder

Every project gets a `.cli/` folder Claude Code reads as context:

```
.cli/
  plan/
    CONTEXT.md      — what the project is, its architecture, what not to do
    DECISIONS.md    — why each architecture choice was made
    PLAN.md         — living task list, checked off by cli:audit
  audit/
    EXPLORE.md      — cli:explore findings (architecture map, patterns, gaps)
    GAPS.md         — what's missing vs Propane conventions
    FIXES.md        — prioritized improvement list
  tech/
    STACK.md        — deps, versions, entry points, bun scripts
```

---

## What gets scaffolded

`/cli:new` generates files based on your planning answers:

| Feature | Files |
|---------|-------|
| Always | `src/cli.ts`, `src/configure.ts`, `CLAUDE.md`, `.gitignore`, `.env.example` |
| Dashboard UI | `src/hud.ts` — ANSI screen loop with spinner, resize handling, arrow-key nav |
| Wizard UI | `cli/App.tsx`, `cli/components/Frame.tsx`, `SelectList.tsx`, `TextInput.tsx` |
| AI usage | `src/models.ts` — model tiers, never hardcoded elsewhere |
| External APIs | `src/sources/types.ts` + one stub per API — all return `SourceResult`, never throw |
| Browser view | `src/server.ts` + `ui/index.html` — Bun.serve with SSE, dark theme, monospace |
| MCP server | `src/mcp.ts` — queryable from Claude Desktop |
| Tests | `tests/cli.test.ts` — bun:test suite for configure, models, sources |

---

## Conventions enforced

Patterns from real Propane CLIs (animations, images, pulse, byline, battlecards):

- **`src/models.ts`** — all model IDs here. Never hardcoded anywhere else.
- **`SourceResult`** — every external fetch returns this type. Never throws.
- **No databases** — flat files only. Claude is the query layer.
- **`bun hud`** — always the entry command.
- **`process.stdout.on('resize', redraw)`** — required in every ANSI HUD.
- **`.propane/`** — runtime state (gitignored). `output/` — generated files (gitignored).

A pre-tool-use hook warns when generated code violates these conventions.

---

## Works with CLI-Anything

[CLI-Anything](https://github.com/HKUDS/CLI-Anything) wraps any GUI or API in a CLI harness (Python Click, JSON output, REPL). This plugin makes that CLI look and feel right — ANSI HUD, Ink wizard, source patterns, model tiers.

Typical flow:
1. `CLI-Anything` — generate the API wrapper
2. `/cli:new` or `/cli:audit` — design the UX layer on top

---

## Project structure

```
.claude-plugin/
  plugin.json           — plugin registration (name: cli)
  marketplace.json      — marketplace entry

skills/
  cli-explore/SKILL.md  — /cli:explore: read-only analysis
  cli-plan/SKILL.md     — /cli:plan: planning interview
  cli-new/SKILL.md      — /cli:new: plan + scaffold + verify
    assets/             — reference files (hud.ts, App.tsx, models.ts, etc.)
  cli-audit/SKILL.md    — /cli:audit: explore + plan + execute
  cli-learn/SKILL.md    — /cli:learn: extract session patterns → project memory

agents/
  cli-planner.md        — goal-driven planning interview
  cli-explorer.md       — read-only codebase analysis
  cli-architect.md      — architecture blueprint
  cli-reviewer.md       — correctness + conventions review
  cli-learner.md        — session log → project memory distillation

rules/                  — 42 subject-named rules (colors, retry, testing, tables, etc.)

hooks/
  hooks.json            — PreToolUse conventions + PostToolUse error capture + Stop logger + SessionStart context
  check_conventions.py  — warns on model IDs, throwing sources, DB imports
  error_capture.py      — buffers bash errors for session learning
  session_logger.py     — writes session summary to .cli/sessions/
```

---

## Source

[github.com/greenlieberd/cli-skill](https://github.com/greenlieberd/cli-skill)
