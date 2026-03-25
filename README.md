# cli-skill

> A Claude Code plugin for building CLI tools that feel like real software — and get better every time you work on them.

---

## Why this exists

There's something honest about a CLI tool. No design system, no component library, no browser abstraction layer. Just you, the terminal, and a blinking cursor. If it feels good, you built it right.

Claude Code is proof of this. It's a CLI — but navigating it feels like using software that cares about the experience. The spinner timing. The way output breathes. The keyboard shortcuts that just work. The layout that adapts when you resize the window. That's not an accident. That's the result of hundreds of intentional decisions about layout, color, feedback, and flow.

Most CLIs skip all of that. Especially AI-generated ones.

When you ask an AI to build a CLI today, you usually get a pile of `console.log()` calls dressed up as a tool. It runs. It doesn't feel like anything. You ship it a little embarrassed.

**This plugin closes that gap.**

---

## What makes a great CLI

The tools that feel right share a set of patterns. None of them are magic:

**Visual identity** — An ASCII art logo on the home screen. Not decoration — signal. It tells the user they're inside something real, something built with intention.

**Persistent layout** — A HUD (heads-up display) that holds its shape, updates in place, and responds to the terminal resizing around it. You run it and leave it running.

**Guided flows** — A wizard that walks you through one decision at a time, tracks where you are, and never leaves you without a way forward or back.

**Honest feedback** — A spinner that pauses while printing results, resumes when there's more work to do. Output that's readable at any terminal width. Colors that mean something — green is done, red is broken, dim is detail.

**Resilient data** — Every external fetch returns a result object, never throws. The tool degrades gracefully. One broken API doesn't take down the run.

**Clean AI integration** — Model IDs in one file. Two tiers: fast for decisions, smart for output. Streaming to terminal when the user is waiting. Cached prompts when calling repeatedly.

These aren't opinions. They're patterns extracted from real production tools — a daily intelligence dashboard, a video production system, an ad image generator, a content pipeline. The things that kept coming up as the difference between a tool that got used and one that got abandoned.

---

## The system

`cli-skill` is a Claude Code plugin. It adds five `/cli:*` skills that work as a complete development system — from the first idea to a tool you can actually ship, and from there into ongoing improvement.

### It starts with a plan

Before any code gets written, `/cli:plan` interviews you. Not a form — a conversation. It asks what you're building, who uses it, what "done" looks like for v0.1. It asks whether this is a tool you run and leave, or a tool you run and walk away from. It asks about APIs, output formats, how people will install it.

From that conversation it makes architecture recommendations and shows them back to you in a table before touching anything. You confirm, you change what's wrong, and only then does it write the plan.

The plan lives in `.cli/plan/` — three files:

- `CONTEXT.md` — what the project is, what it shouldn't do, what conventions it follows
- `DECISIONS.md` — why each architecture choice was made, what was considered and rejected
- `PLAN.md` — a living task list, split between v0.1 (ship this) and v0.2+ (park for later)

These files aren't docs you write once and forget. They're the project's memory. Every future session starts by reading them.

### It scaffolds exactly what the plan says

`/cli:new` takes the plan and builds from it. Nothing gets added that isn't in the v0.1 scope. Every file gets announced before it's written. The ASCII logo gets drawn from the tool's name. The theme is set from the five color presets you chose during planning. The menu items are real — no placeholders, no "coming soon."

Tests are part of v0.1, not a later task. The scaffold doesn't finish until `bun test` passes.

### It audits and improves

`/cli:audit` is how you work on an existing CLI. It loads all the context from `.cli/` first — the plan, the decisions, the learnings from past sessions — so it knows what was already decided and why. Then it maps what's actually in the code against what the plan said should be there.

It can fix convention violations (hardcoded model IDs, sources that throw instead of returning), add a feature from the v0.2+ list, manage the feature set (move things in, move things out, scope down), or run a full audit and let the findings decide what to do.

Every task runs with a confirm step, a commit, and a check-off in the plan before moving to the next one.

### It keeps learning

This is the part that compounds.

Every session gets logged to `.cli/sessions/` — what ran, what broke, what changed. After a few sessions, `/cli:learn` reads those logs and distills them into project memory: patterns that work for this specific project, things to watch out for, decisions that were already made and shouldn't be reopened.

That memory lives in `.cli/learnings/SUMMARY.md`. Every future session starts by reading it. Claude comes in knowing the project's history — the gotchas, the preferences, the choices that were already debated. You don't re-explain the same things. The tool gets better at understanding your project the longer you work on it.

---

## The `.cli/` folder

Every project gets a `.cli/` folder that travels with the repo. It's the project's brain — everything Claude needs to work on this tool without starting from scratch.

```
.cli/
  plan/                 ← committed, shared with the team
    CONTEXT.md          — what the project is, architecture, what not to do
    DECISIONS.md        — why each choice was made
    PLAN.md             — living task list: v0.1 done/pending, v0.2+ parked
  audit/                ← committed, shared with the team
    EXPLORE.md          — architecture map, patterns, gaps
    GAPS.md             — convention violations found
    FIXES.md            — prioritized improvement list
  learnings/            ← committed, shared with the team
    SUMMARY.md          — loaded at every session start
    patterns.md         — what works for this project
    watch-out.md        — known gotchas
    decisions.md        — choices already made, don't re-open
  sessions/             ← gitignored, personal
    YYYY-MM-DD.jsonl    — session logs written by the Stop hook
```

The split matters: plan, audit, and learnings travel with the repo — the whole team benefits from what was learned. Sessions stay local — they're raw material, not outputs.

---

## Five skills

| Skill | What it does |
|-------|-------------|
| **`/cli:new`** | Full build cycle: interview → plan → scaffold → review → verify → ship checklist |
| **`/cli:plan`** | Just the planning phase — use when you want to think before building |
| **`/cli:explore`** | Read-only analysis of an existing CLI — architecture map, gap report, 5 files to read first |
| **`/cli:audit`** | Improve what exists — loads all context, explores, plans, executes task by task with commits |
| **`/cli:learn`** | Reads session logs, distills patterns into project memory for future sessions |

Skills compose. `/cli:new` runs the planner internally. `/cli:audit` runs the explorer and planner. Run any skill standalone when you want just that phase.

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

## What gets scaffolded

`/cli:new` generates files based on your planning answers — only what's in v0.1 scope:

| Piece | Files |
|-------|-------|
| Always | `src/cli.ts` · `src/configure.ts` · `src/theme.ts` · `CLAUDE.md` · `.gitignore` · `.env.example` |
| HUD interface | `src/hud.ts` — ANSI screen loop, ASCII logo, spinner, resize handler, arrow-key nav |
| Wizard interface | `cli/App.tsx` · `cli/components/Frame.tsx` · `SelectList.tsx` · `TextInput.tsx` |
| AI | `src/models.ts` — only the tiers you chose, never hardcoded elsewhere |
| APIs | `src/sources/types.ts` + one stub per source — all return `SourceResult`, never throw |
| Browser view | `src/server.ts` + `ui/index.html` — Bun.serve with SSE |
| MCP server | `src/mcp.ts` — queryable from Claude Desktop |
| Tests | `tests/cli.test.ts` — bun:test, mocked fetch, configure + models + sources |

v0.2+ features get parked in the plan, not built. Ship something working first.

---

## The conventions it enforces

A pre-tool-use hook watches for violations as Claude writes code:

- **`src/models.ts`** — all model IDs here. Never a hardcoded string anywhere else.
- **`src/theme.ts`** — all color constants here. 5 presets. Never inline ANSI codes.
- **`SourceResult`** — every external fetch returns this type. Never throws. The caller decides what to do with failures.
- **No databases** — flat files only. Claude is the query layer.
- **`bun hud`** — always the entry command.
- **Resize handler** — `process.stdout.on('resize', redraw)` in every ANSI HUD. Required.
- **Width guard** — `Math.min(process.stdout.columns ?? 80, 66)`. Content readable at any size.

---

## Works with CLI-Anything

[CLI-Anything](https://github.com/HKUDS/CLI-Anything) turns any API or GUI into a CLI harness. This plugin makes that harness look and feel right.

```
CLI-Anything → generates the wrapper
/cli:audit   → designs the UX layer on top
```

---

## Project structure

```
.claude-plugin/
  plugin.json           — plugin registration (name: cli → /cli:* commands)
  marketplace.json      — marketplace entry

skills/
  cli-new/SKILL.md      — /cli:new: plan + scaffold + verify
    assets/             — reference files: hud.ts, theme.ts, models.ts, App.tsx, Frame.tsx
  cli-plan/SKILL.md     — /cli:plan: thin wrapper → cli-planner agent
  cli-explore/SKILL.md  — /cli:explore: read-only analysis
  cli-audit/SKILL.md    — /cli:audit: full improvement cycle
  cli-learn/SKILL.md    — /cli:learn: session logs → project memory

agents/
  cli-planner.md        — goal-driven planning interview → .cli/plan/
  cli-explorer.md       — read-only codebase analysis
  cli-architect.md      — architecture blueprint
  cli-reviewer.md       — correctness + conventions review
  cli-learner.md        — session logs → .cli/learnings/

rules/                  — 42 subject-named rules
                          (hud-screens · ascii-art · colors · source-results · models ·
                           display-system · error-recovery · testing · retry · and 33 more)

hooks/
  hooks.json            — PreToolUse conventions + PostToolUse error capture
                          + Stop session logger + SessionStart context inject
  check_conventions.py  — warns on model IDs, throwing sources, DB imports
  error_capture.py      — buffers bash errors for session learning
  session_logger.py     — writes session summary to .cli/sessions/
```

---

## Built by

[Propane](https://usepropane.ai) — created by [Dennis Green-Lieber](https://github.com/greenlieberd).

MIT licensed. Open source. Built from real tools, for real tools.
