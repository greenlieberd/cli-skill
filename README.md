# cli-skill

A Claude Code plugin for building production-quality CLI tools with Bun, Ink, and ANSI patterns.

Three skills:
- **`/new-cli`** — plan and scaffold a new CLI from scratch, including dependency setup
- **`/audit-cli`** — review an existing CLI and produce a prioritized `PLAN.md`
- **`/fix-cli`** — execute tasks from a `PLAN.md` one by one, with verification

---

## Prerequisites

- [Claude Code](https://claude.ai/code) installed and running
- [Bun](https://bun.sh) — the skill will offer to install it if missing

---

## Install

### Option A — Install directly from GitHub

```bash
claude plugin install git@github.com:greenlieberd/cli-skill.git
```

### Option B — Clone and install locally

```bash
git clone git@github.com:greenlieberd/cli-skill.git
claude plugin install ./cli-skill
```

### Option C — Install from a local path (for development)

```bash
claude plugin install /path/to/cli-skill
```

After installing, verify the skills are available:

```
/new-cli
```

You should see the planning interview start.

---

## Usage

### Build a new CLI

Go to the folder where you want to create the project, then:

```
/new-cli
```

Or pass a name to skip the first question:

```
/new-cli my-tool
```

The skill will:
1. Check your environment (Bun, Git, existing files)
2. Ask 8 planning questions — interface style, AI usage, APIs, output, distribution
3. Offer to install dependencies before writing any code
4. Scaffold the full project and run a quality review

### Audit an existing CLI

```
/audit-cli /path/to/your/cli
```

Or run it from the project folder:

```
/audit-cli
```

The skill will:
1. Explore the project structure using the `cli-explorer` agent
2. Check against Propane CLI conventions
3. Write a `PLAN.md` with prioritized tasks

### Execute the plan

After an audit, run:

```
/fix-cli /path/to/your/cli
```

Or from the project folder:

```
/fix-cli
```

The skill reads `PLAN.md`, implements one task at a time, runs verification checks, and marks items complete.

---

## What gets scaffolded

Depending on your answers, the project includes:

| Feature | Files generated |
|---------|----------------|
| Always | `src/cli.ts`, `src/models.ts`, `src/configure.ts`, `PLAN.md`, `CLAUDE.md`, `.gitignore`, `.env.example` |
| Dashboard UI | `src/hud.ts` — ANSI screen loop with ASCII art, spinner, arrow-key navigation |
| Wizard UI | `cli/App.tsx`, `cli/components/Frame.tsx`, `SelectList.tsx`, `TextInput.tsx` |
| External APIs | `src/sources/types.ts` + one stub per API — all return `SourceResult`, never throw |
| Browser view | `src/server.ts` + `ui/index.html` — Bun.serve with SSE, dark theme, monospace |
| MCP server | `src/mcp.ts` — queryable from Claude Desktop |
| Tests | `tests/cli.test.ts` — bun:test suite for configure, models, sources |

---

## Conventions enforced

This plugin encodes patterns from real Propane CLIs (animations, images, pulse, byline, battlecards):

- **`src/models.ts`** — all model IDs in one place. Never hardcoded anywhere else.
- **`SourceResult`** — every external data fetch returns this type. Never throws.
- **No databases** — flat files only. Claude is the query layer.
- **`bun hud`** — always the entry command, regardless of interface style.
- **`.propane/`** — runtime state (gitignored). `output/` — generated files (gitignored).

A pre-tool-use hook warns when generated code violates these conventions.

---

## Project structure

```
.claude-plugin/plugin.json

skills/
  new-cli/SKILL.md          — /new-cli: plan + scaffold
    examples/               — copy-paste reference files
      hud.ts                  complete ANSI HUD with spinner, resize handling
      App.tsx                 Ink wizard state machine
      Frame.tsx               progress dots + border
      SelectList.tsx          single + multi-select
      sources/types.ts        SourceResult interface + helpers
      models.ts               model tier setup
      configure.ts            loadEnv + maskValue (copy verbatim)
      package.json            annotated deps
  audit-cli/SKILL.md        — /audit-cli: review → .cli/PLAN.md
  fix-cli/SKILL.md          — /fix-cli: execute plan items with commits

agents/
  cli-planner.md            — goal-driven planning interview → .cli/ folder
  cli-explorer.md           — read-only analysis of existing CLIs
  cli-architect.md          — architecture blueprint (minimal vs modular)
  cli-reviewer.md           — code review (correctness / completeness / conventions)

guides/
  folder-structure.md       — canonical layout including .cli/ folder
  ui-patterns.md            — HTML template, dark palette, SSE bridge
  file-browser-bridge.md    — Bun fs.watch → SSE → browser → POST
  data-philosophy.md        — no databases, flat files, Claude as query layer
  mcp-patterns.md           — MCP server template, Claude Desktop setup
  plugin-ecosystem.md       — external plugins worth composing
  claude-code-patterns.md   — streaming, multi-agent, hooks, status bar
  cli-ux.md                 — navigation, resize handling, feedback, error messages

hooks/
  hooks.json                — convention check (scoped to CLI projects)
  check_conventions.py      — warns on model IDs, throwing sources, DB imports
  load_context.sh           — scoped session reminder
```

---

## Uninstall

```bash
claude plugin uninstall propane-cli-skill
```

---

## Source

[github.com/greenlieberd/cli-skill](https://github.com/greenlieberd/cli-skill)
