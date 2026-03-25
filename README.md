# cli-skill

> A Claude Code plugin for building CLI tools that feel like real software — not like AI spit them out.

---

## Why this exists

There's something honest about a CLI tool. No design system, no component library, no browser abstraction layer. Just you, the terminal, and a blinking cursor. If it feels good, you built it right.

Claude Code is proof of this. It's a CLI — but navigating it feels like using a piece of software that cares about the experience. The spinner timing, the way output breathes, the keyboard shortcuts that just work. That's not an accident. It's the result of intentional decisions about layout, color, feedback, and flow. Most CLIs skip all of that.

When AI helps you build a CLI today, you usually get a pile of `console.log()` calls dressed up as a tool. It works. It doesn't feel like anything. You ship it embarrassed.

This plugin changes that.

---

## What it is

`cli-skill` is a Claude Code plugin that teaches Claude how to design and build **HUDs, wizards, and command interfaces** that feel intentional — the way tools like Claude Code, Warp, and Charm's Bubbletea apps feel intentional.

It encodes real patterns from production Propane CLIs — a daily intelligence dashboard, a video production system, a static ad generator, a content pipeline — distilled into 42 rules, 5 agents, and a scaffold system that generates the right architecture for your specific tool.

**What "right" means:**

- A **HUD** (heads-up display) for tools you leave running — dashboards, monitors, data browsers. Arrow-key navigation, persistent screen, resize handling, live state.
- A **Wizard** for tools that walk you through a flow — generators, setup screens, multi-step forms. Progress dots, step navigation, clean exits.
- A **Command interface** for tools you pipe and script — clean stdout, predictable flags, CI-friendly.

The plugin interviews you, recommends the right pattern for your tool, scaffolds the full stack, and reviews the output before you run it.

---

## The patterns it enforces

Good CLI UX is learnable. These are the rules that matter:

- **ASCII art logo** on every HUD home screen — not decoration, signal. It tells the user they're inside a real tool.
- **Resize handling** — `process.stdout.on('resize', redraw)` in every ANSI screen. The terminal changes shape; your layout should too.
- **Width guard** — `Math.min(process.stdout.columns ?? 80, 66)` — content that stays readable on any terminal.
- **Narrow terminal fallback** — if it's under 50 columns, show a clear message instead of a broken layout.
- **Color themes** — one accent color per tool, semantic meaning for success/warn/error, all in one `src/theme.ts`. Never inline ANSI strings.
- **SourceResult pattern** — every external fetch returns a result object, never throws. The caller decides what to do with failures.
- **Model tiers in one file** — `src/models.ts` only. Haiku for decisions, Sonnet for output. Never a hardcoded model string anywhere else.
- **Spinner discipline** — the spinner pauses while printing completion lines, resumes after. No interleaved output.

A pre-tool-use hook watches for violations as Claude writes code and warns before they get committed.

---

## Five skills

| Skill | What it does |
|-------|-------------|
| **`/cli:new`** | Full build: interview → plan → scaffold → review → verify. The main one. |
| **`/cli:plan`** | Just the planning phase. Use this when you want to think before building. |
| **`/cli:explore`** | Read-only analysis of an existing CLI. Maps architecture, flags gaps. |
| **`/cli:audit`** | Improve what exists — explores, plans, executes task by task with commits. |
| **`/cli:learn`** | After a few sessions, extracts patterns into project memory for future runs. |

Skills compose: `/cli:new` runs the planner internally. `/cli:audit` runs the explorer and planner. Run any skill standalone when you want just that phase.

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

The planning interview starts. It asks what you're building, what the smallest shippable version is, which interface pattern fits, whether you need AI, where the data comes from. Takes 2 minutes. Then it builds.

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

## What gets built

`/cli:new` scaffolds exactly what your plan requires:

| Piece | Files |
|-------|-------|
| Always | `src/cli.ts` · `src/configure.ts` · `src/theme.ts` · `CLAUDE.md` · `.gitignore` · `.env.example` |
| HUD interface | `src/hud.ts` — ANSI screen loop, ASCII logo, spinner, resize, arrow-key nav |
| Wizard interface | `cli/App.tsx` · `cli/components/Frame.tsx` · `SelectList.tsx` · `TextInput.tsx` |
| AI | `src/models.ts` — tiers you chose, never hardcoded elsewhere |
| APIs | `src/sources/types.ts` + one stub per source — all return `SourceResult`, never throw |
| Browser view | `src/server.ts` + `ui/index.html` — Bun.serve with SSE |
| MCP server | `src/mcp.ts` — queryable from Claude Desktop |
| Tests | `tests/cli.test.ts` — bun:test, mocked fetch, configure + models + sources |

v0.2+ features get parked in the plan, not built. Ship something working first.

---

## The `.cli/` folder

Every project gets a `.cli/` folder that travels with the repo and gives every future session full context:

```
.cli/
  plan/
    CONTEXT.md      — what the project is, architecture, what not to do
    DECISIONS.md    — why each choice was made
    PLAN.md         — living task list with v0.1 and v0.2+ sections
  audit/
    EXPLORE.md      — architecture map, patterns, gaps
    GAPS.md         — convention violations
    FIXES.md        — prioritized improvement list
  learnings/
    SUMMARY.md      — extracted patterns, watch-outs (loaded at session start)
    patterns.md     — what worked
    watch-out.md    — known gotchas
  sessions/         — gitignored, personal
    YYYY-MM-DD.jsonl
```

---

## Works with CLI-Anything

[CLI-Anything](https://github.com/HKUDS/CLI-Anything) turns any API or GUI into a CLI harness. This plugin makes that harness look and feel right.

```
CLI-Anything → generates the wrapper
/cli:audit   → designs the UX on top
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
  cli-plan/SKILL.md     — /cli:plan: planning interview → .cli/plan/
  cli-explore/SKILL.md  — /cli:explore: read-only analysis
  cli-audit/SKILL.md    — /cli:audit: explore + plan + execute
  cli-learn/SKILL.md    — /cli:learn: session logs → project memory

agents/
  cli-planner.md        — goal-driven planning interview
  cli-explorer.md       — read-only codebase analysis
  cli-architect.md      — architecture blueprint
  cli-reviewer.md       — correctness + conventions review
  cli-learner.md        — session log → project memory distillation

rules/                  — 42 subject-named rules (hud-screens, ascii-art, colors,
                          source-results, models, display-system, error-recovery,
                          testing, retry, and 33 more)

hooks/
  hooks.json            — PreToolUse conventions + PostToolUse error capture
                          + Stop session logger + SessionStart context
  check_conventions.py  — warns on model IDs, throwing sources, DB imports
  error_capture.py      — buffers bash errors for session learning
  session_logger.py     — writes session summary to .cli/sessions/
```

---

## Built by

[Propane](https://usepropane.ai) — created by [Dennis Green-Lieber](https://github.com/greenlieberd).

MIT licensed. Open source. Built from real tools, for real tools.
