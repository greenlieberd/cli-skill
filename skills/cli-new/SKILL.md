---
name: cli-new
description: This skill should be used when building a new CLI tool from scratch. Triggers on "build a new CLI", "create a CLI", "I need a terminal tool for X", "scaffold a new Bun tool", "start a new project that runs in the terminal", or any request to build something that does not exist yet. Runs a planning interview, then scaffolds the full project in one session.
argument-hint: "[project-name]"
model: sonnet
effort: high
context: fork
allowed-tools: Read, Write, Edit, Glob, Grep, LS, Bash
---

# cli:new — Plan, scaffold, verify

Three phases: plan with the user, scaffold exactly what the plan says, verify it runs. Never write code before the plan is confirmed.

## Context loaded at runtime

Directory: !`pwd`
Bun: !`bun --version 2>/dev/null || echo "NOT INSTALLED"`
Git: !`git rev-parse --is-inside-work-tree 2>/dev/null && echo "repo" || echo "no repo"`
Existing package.json: !`[ -f package.json ] && python3 -c 'import json; d=json.load(open("package.json")); print(d.get("name","?"))' 2>/dev/null || echo "none"`
Project memory: !`cat "${ARGUMENTS:-.}/.cli/learnings/SUMMARY.md" 2>/dev/null || echo "none"`

---

## Phase 1 — Environment check

Check before anything else:

- **Bun not installed** → "Bun is required. Should I install it? (runs `curl -fsSL https://bun.sh/install | bash`)" — wait for yes.
- **`$ARGUMENTS` is a path to an existing project** → run `cli-explorer` on it first, use findings to skip questions already answered by the code.
- **`$ARGUMENTS` is a project name** → use it, skip the name question.
- **Existing package.json** → "There's already a project here (`[name]`). Are we extending it or starting in a new subfolder?"

---

## Phase 2 — Plan

**If `.cli/plan/PLAN.md` already exists** (user ran `/cli:plan` first):
```
A plan already exists at .cli/plan/PLAN.md.

  A) Use this plan — skip the interview, go straight to scaffold
  B) Re-plan from scratch

Which would you like?
```
On A: read PLAN_COMPLETE fields from the existing plan files and jump to Phase 3.

**If no plan exists:** launch `cli-planner` agent. Pass:
- The goal or name from `$ARGUMENTS`
- Any `cli-explorer` findings (if extending)
- Current directory

The planner interviews the user (goal, v0.1 scope, interface, AI, sources, output, distribution, theme) then writes:
- `.cli/plan/CONTEXT.md`
- `.cli/plan/DECISIONS.md`
- `.cli/plan/PLAN.md`

**Wait for `PLAN_COMPLETE` before continuing.**

---

## Phase 3 — Dependency setup

After `PLAN_COMPLETE`, show what will be installed before touching the filesystem:

```
Based on your plan, here's what [name] needs:

  bun (runtime)                      [installed ✓ / needs install]
  @anthropic-ai/sdk                  [if ai ≠ none and ≠ piped]
  ink ^5 + react ^19                 [if interface = wizard or hybrid]
  ink-text-input ^6                  [if interface = wizard or hybrid]
  @modelcontextprotocol/sdk          [if distribution includes mcp]

Create [name]/ and run bun install? (yes / no)
```

On yes:
```bash
mkdir -p [name] && cd [name]
# write package.json first, then:
bun install
git init
git add package.json bun.lockb
git commit -m "chore: init [name]"
```

---

## Phase 4 — Scaffold

Read `PLAN_COMPLETE` fields. Use this mapping:

| Field | Value | Files |
|-------|-------|-------|
| `interface` | `hud` | `src/hud.ts` (from assets/hud.ts, adapted) |
| `interface` | `wizard` | `cli/index.tsx`, `cli/App.tsx`, `cli/components/Frame.tsx`, `cli/components/SelectList.tsx`, `cli/components/TextInput.tsx`, `tsconfig.json` |
| `interface` | `commands` | `src/cli.ts` only |
| `interface` | `hybrid` | Both `src/hud.ts` AND `cli/` folder |
| `ai` | `fast` | `src/models.ts` fast tier only |
| `ai` | `smart` | `src/models.ts` smart tier only |
| `ai` | `both` | `src/models.ts` fast + smart |
| `ai` | `piped` or `none` | No models.ts |
| `sources` | any list | `src/sources/types.ts` + one stub per source |
| `output` | includes `browser` | `src/server.ts` + `ui/index.html` |
| `distribution` | includes `mcp` | `src/mcp.ts` |
| `distribution` | includes `global` | `"bin": {"[name]": "src/cli.ts"}` in package.json |
| `theme` | any value | `src/theme.ts` — always generated, sets ACTIVE_THEME |

Read `${CLAUDE_SKILL_DIR}/../../rules/folder-structure.md` before writing any file — confirms canonical src/, cli/, output/, .propane/, .cli/ layout.

**Write in this order. Announce each file before writing it. No `// TODO` stubs. Only build what's in the v0.1 scope.**

1. `CLAUDE.md` — references `.cli/plan/CONTEXT.md`, lists `bun hud`, summarizes architecture
2. `.gitignore` — node_modules, .env, output/, .propane/, .cache/, .fonts/, .cli/sessions/
   (note: `.cli/plan/`, `.cli/audit/`, `.cli/learnings/` are committed — only `sessions/` is gitignored)
3. `.env.example` — one line per key, `# description` above each
4. `package.json` — scripts: hud, test, and optionally mcp/serve/run
5. `src/theme.ts` — set ACTIVE_THEME from PLAN_COMPLETE `theme` field
   → Read `${CLAUDE_SKILL_DIR}/assets/theme.ts` for structure
6. `src/models.ts` — include only the tiers from PLAN_COMPLETE `ai` field; skip if ai = none/piped
   → Read `${CLAUDE_SKILL_DIR}/assets/models.ts` for structure
7. `src/configure.ts` — copy verbatim from `${CLAUDE_SKILL_DIR}/assets/configure.ts`
8. `src/cli.ts` — routes to hud/wizard/run, under 80 lines

**If interface = hud or hybrid:**
Read before writing hud.ts: `rules/hud-screens.md`, `rules/ascii-art.md`, `rules/alternate-screen.md`, `rules/layouts.md`, `rules/spinners.md`, `rules/tables.md`, `rules/tabs.md`, `rules/keyboard-shortcuts.md`.
Read `${CLAUDE_SKILL_DIR}/assets/hud.ts` as the reference implementation — adapt menu items, logo, and screen names for this project.

Rules for hud.ts:
- ASCII art logo at the top of home screen — required (use the 6-line block letter pattern from ascii-art.md)
- Skip logo if terminal < 48 cols, show plain name instead
- Menu items = v0.1 features only — no placeholders, no "coming soon"
- `process.stdout.on('resize', redraw)` — required, no exceptions
- `Math.min(process.stdout.columns ?? 80, 66)` for all widths
- If terminal < 50 cols, show a readable fallback message
- Use `alternate-screen.md` pattern for fullscreen buffer entry/exit
- Apply `layouts.md` for sidebar, split-pane, or footer patterns as needed
- Use `spinners.md` for any multi-phase loading states
- Use `tables.md` for any tabular data rendering
- Use `tabs.md` for tab bar navigation with ◄ ► switching
- Use `keyboard-shortcuts.md` for shortcut design and help overlay

**If interface = wizard or hybrid:**
Read before writing cli/ files: `rules/wizard-steps.md`, `rules/confirmation.md`, `rules/rich-input.md`, `rules/spinners.md`.
Read `${CLAUDE_SKILL_DIR}/assets/App.tsx`, `Frame.tsx`, `SelectList.tsx` as reference — adapt steps for this project.

Rules for wizard:
- NEXT and PREV maps must cover every step — no dead ends
- Every step gets exactly `onNext(value)` and `onBack()` props
- Use `confirmation.md` pattern for any destructive action prompts
- Use `rich-input.md` for multi-line input, paste, or image input steps
- `cli/index.tsx` (no asset — write from scratch):
  ```tsx
  #!/usr/bin/env bun
  import React from 'react'
  import { render } from 'ink'
  import App from './App.tsx'
  render(React.createElement(App))
  ```

**If interface = hybrid:**
Read `${CLAUDE_SKILL_DIR}/../../rules/hybrid-interface.md` before wiring the HUD home screen to Ink wizard sub-flows.

**If sources ≠ none:**
Read before writing source files: `rules/source-results.md`, `rules/retry.md`, `rules/caching.md`, `rules/limits.md`, `rules/parallelization.md`.
Each source returns `SourceResult` — never throws.
- Use `caching.md` for `.cache/` TTL pattern if source data doesn't change every run
- Define all fetch limits in one `LIMITS` registry per `limits.md`
- Use `parallelization.md` pattern for concurrent `Promise.allSettled` source fetches

9. Source files — only sources in v0.1 scope, one file each
10. `src/server.ts` + `ui/index.html` — if output includes browser (read `rules/file-watch.md` for SSE/live-reload)
11. `src/mcp.ts` — if distribution includes mcp
12. Output file helpers — if output includes reports/exports (read `rules/output-files.md` for date-stamped naming; `rules/diff-output.md` if showing before/after diffs)

**Tests** (read `${CLAUDE_SKILL_DIR}/../../rules/testing.md` before writing):

`tests/cli.test.ts` is required — write it now, not later.
- `configure.ts` — `loadEnv()` loads keys, `maskValue()` masks correctly
- `src/models.ts` — model IDs are strings, tiers exist (skip if ai = none/piped)
- At least one source or command — happy path + one error path
- `global.fetch = mock(...)` in `beforeEach`, restore in `afterEach`
- Run `bun test` — must pass before quality review

Commit:
```bash
git add -A && git commit -m "feat: scaffold [name] ([interface] / [ai] / [sources or no sources])"
```

---

## Phase 5 — Quality review

Spawn two `cli-reviewer` agents in parallel (via Task tool), each with a different focus brief:

**Instance 1 brief:** "Review [project-path] for correctness: broken imports, wrong relative paths, missing types, env variables accessed before loadEnv(), missing return types on exported functions."

**Instance 2 brief:** "Review [project-path] for conventions: hardcoded model IDs outside models.ts, sources that throw instead of returning SourceResult, missing .gitignore entries for output/ and .propane/, database imports."

Apply every fix the reviewers find.

```bash
git add -A && git commit -m "fix: reviewer corrections"
```

---

## Phase 6 — Verify

```bash
cd [project-path] && bun hud
```

If it crashes, read the error and fix it. Do not finish with a broken entry point.

```bash
bun test
```

---

## Phase 7 — v0.1 ship checklist

This is v0.1. Every item here must pass. Nothing ships broken.

**Runs:**
- [ ] `bun hud` starts without errors, main screen renders
- [ ] Arrow keys navigate menus, `ctrl+c` exits cleanly and restores cursor
- [ ] Resize terminal — layout adapts, no corruption (ANSI HUD)
- [ ] Frame shows correct progress dots per step (Wizard)

**Looks right:**
- [ ] ASCII art logo renders on the home screen
- [ ] Every menu item does something real — no placeholders, no "coming soon"
- [ ] v0.2+ features are not in the menu yet

**Tests pass:**
- [ ] `bun test` passes with zero failures
- [ ] configure, models, and at least one source/command are covered
- [ ] Tests use mocked fetch — not hitting real APIs

**Ships clean:**
- [ ] `.env.example` documents every required key
- [ ] `output/` and `.propane/` are in `.gitignore`
- [ ] `.cli/plan/PLAN.md` shows v0.1 tasks and v0.2+ parked separately
- [ ] `CLAUDE.md` accurately describes what's built

**If browser:** `bun serve` opens, status shows "connected"
**If MCP:** `src/mcp.ts` runs, `CLAUDE.md` has registration instructions

```bash
git add -A && git commit -m "chore: ready for first run — [name]"
```

Tell the user: "Run `git push` when you're ready to share this."

---

## Rules — read only what the plan requires

Do not load rules speculatively. Read each rule immediately before writing the files it covers.

**Always:**
- `${CLAUDE_SKILL_DIR}/../../rules/conventions.md` — before writing any file
- `${CLAUDE_SKILL_DIR}/../../rules/environment-setup.md` — before writing configure.ts / .env.example
- `${CLAUDE_SKILL_DIR}/../../rules/testing.md` — before writing tests/cli.test.ts

**If interface = hud or hybrid:**
- `${CLAUDE_SKILL_DIR}/../../rules/hud-screens.md`
- `${CLAUDE_SKILL_DIR}/../../rules/ascii-art.md`
- `${CLAUDE_SKILL_DIR}/../../rules/colors.md`
- `${CLAUDE_SKILL_DIR}/../../rules/display-system.md`

**If interface = wizard or hybrid:**
- `${CLAUDE_SKILL_DIR}/../../rules/wizard-steps.md`
- `${CLAUDE_SKILL_DIR}/../../rules/colors.md`

**If sources ≠ none:**
- `${CLAUDE_SKILL_DIR}/../../rules/source-results.md`
- `${CLAUDE_SKILL_DIR}/../../rules/retry.md`

**If ai ≠ none and ≠ piped:**
- `${CLAUDE_SKILL_DIR}/../../rules/models.md`
- `${CLAUDE_SKILL_DIR}/../../rules/token-spend.md` — track usage, estimate cost per call
- `${CLAUDE_SKILL_DIR}/../../rules/stream-to-agents.md` — if piping CLI output to Claude Code agents

**If output includes browser:**
- `${CLAUDE_SKILL_DIR}/../../rules/browser-views.md`
- `${CLAUDE_SKILL_DIR}/../../rules/file-watch.md` — Bun fs.watch → SSE → live reload

**If distribution includes mcp:**
- `${CLAUDE_SKILL_DIR}/../../rules/mcp-servers.md`

**If distribution includes global:**
- `${CLAUDE_SKILL_DIR}/../../rules/global-install.md` — bin config, global run from anywhere
- `${CLAUDE_SKILL_DIR}/../../rules/update-checker.md` — non-blocking startup version check

**If writing to .propane/ or output/ storage:**
- `${CLAUDE_SKILL_DIR}/../../rules/flat-files.md`
- `${CLAUDE_SKILL_DIR}/../../rules/output-files.md` — date-stamped naming, manifest, open from HUD
- `${CLAUDE_SKILL_DIR}/../../rules/logging.md` — JSONL usage logs, error logs, log rotation

**If output includes diffs or before/after comparison:**
- `${CLAUDE_SKILL_DIR}/../../rules/diff-output.md`

**Additional (read if working on the relevant area):**
- `${CLAUDE_SKILL_DIR}/../../rules/folder-structure.md` — canonical layout (always read before Phase 4)
- `${CLAUDE_SKILL_DIR}/../../rules/gentle-terminal.md` — streaming, piped output
- `${CLAUDE_SKILL_DIR}/../../rules/error-recovery.md` — crash handling, process.exit()
- `${CLAUDE_SKILL_DIR}/../../rules/configuration.md` — configure.ts patterns
- `${CLAUDE_SKILL_DIR}/../../rules/notifications.md` — macOS osascript alerts
- `${CLAUDE_SKILL_DIR}/../../rules/clipboard.md` — pbcopy/pbpaste integration in HUD
- `${CLAUDE_SKILL_DIR}/../../rules/plugin-ecosystem.md` — composing with other Claude Code plugins
- `${CLAUDE_SKILL_DIR}/../../rules/workspace-settings.md` — .claude/ config, skills, hooks setup
