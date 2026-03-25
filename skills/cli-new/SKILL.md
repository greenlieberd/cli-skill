---
name: new
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
Rules: !`ls "${CLAUDE_SKILL_DIR}/../../rules/" 2>/dev/null`
Assets: !`ls "${CLAUDE_SKILL_DIR}/../cli-new/assets/" 2>/dev/null || ls "${CLAUDE_SKILL_DIR}/assets/" 2>/dev/null`
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

**Write in this order. Announce each file before writing it. No `// TODO` stubs. Only build what's in the v0.1 scope.**

1. `CLAUDE.md` — references `.cli/plan/CONTEXT.md`, lists `bun hud`, summarizes architecture
2. `.gitignore` — node_modules, .env, output/, .propane/, .cache/, .fonts/, .cli/sessions/
   (note: `.cli/plan/`, `.cli/audit/`, `.cli/learnings/` are committed — only `sessions/` is gitignored)
3. `.env.example` — one line per key, `# description` above each
4. `package.json` — scripts: hud, test, and optionally mcp/serve/run
5. `src/theme.ts` — set ACTIVE_THEME to the value from PLAN_COMPLETE `theme` field (read assets/theme.ts)
6. `src/models.ts` — only the tiers from PLAN_COMPLETE (read assets/models.ts)
7. `src/configure.ts` — copy verbatim from assets/configure.ts
8. `src/cli.ts` — routes to hud/wizard/run, under 80 lines
9. Interface files — read assets/ for reference, adapt for this project; import THEME from src/theme.ts
10. Source files — only sources in v0.1 scope
11. Server + UI (if browser, and in v0.1)
12. MCP server (if mcp, and in v0.1)
13. `tests/cli.test.ts` — **required, not optional** (see testing rules below)

**HUD rules** (read `${CLAUDE_SKILL_DIR}/../../rules/hud-screens.md` and `${CLAUDE_SKILL_DIR}/../../rules/ascii-art.md`):

Every HUD gets ASCII art. No exceptions — it's what makes it feel like a real tool.

- Read `${CLAUDE_SKILL_DIR}/../../rules/ascii-art.md` — use the 6-line block letter pattern
- Draw the tool name as a logo at the top of the home screen
- Skip the logo if terminal < 48 cols, show the plain name instead
- Menu items must reflect v0.1 features only — no placeholder items like "Feature coming soon"
  - Each menu item does something real in this version
  - If a feature is v0.2+, it is not in the menu yet
- `process.stdout.on('resize', redraw)` — required, always
- `Math.min(process.stdout.columns ?? 80, 66)` for all widths
- If terminal < 50 cols, show a readable message instead of a broken layout

**Wizard rules** (read `${CLAUDE_SKILL_DIR}/../../rules/wizard-steps.md`):
- Extend assets/App.tsx with this project's actual steps
- NEXT and PREV maps must cover every step — no dead ends
- Every step gets exactly `onNext(value)` and `onBack()` props
- `cli/index.tsx` (entry point — no asset, write from scratch):
  ```tsx
  #!/usr/bin/env bun
  import React from 'react'
  import { render } from 'ink'
  import App from './App.tsx'
  render(React.createElement(App))
  ```

**Testing rules** (read `${CLAUDE_SKILL_DIR}/../../rules/testing.md`):

Tests are part of v0.1, not a later task. Write them now, before the quality review.

`tests/cli.test.ts` must cover:
- `configure.ts` — `loadEnv()` loads keys, `maskValue()` masks correctly
- `src/models.ts` — model IDs are strings, tiers exist, no hardcoded values
- At least one source or command — test the happy path and one error path
- Use `global.fetch = mock(...)` in `beforeEach`, restore in `afterEach`
- Run after scaffold: `bun test` must pass before moving to quality review

Commit:
```bash
git add -A && git commit -m "feat: scaffold [name] ([interface] / [ai] / [sources or no sources])"
```

---

## Phase 5 — Quality review

Launch in parallel:
- `cli-reviewer correctness` — broken imports, wrong paths, missing types, env loaded late
- `cli-reviewer conventions` — models.ts, SourceResult, gitignore, no DB patterns

Read all rules referenced in the Rules section below before reviewing. Apply every fix.

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

## Rules reference

Read when generating the corresponding files:

- HUD screen loop, resize, navigation: `${CLAUDE_SKILL_DIR}/../../rules/hud-screens.md`
- ASCII art logo, block letters, width guard: `${CLAUDE_SKILL_DIR}/../../rules/ascii-art.md`
- Wizard steps, Frame, progress dots: `${CLAUDE_SKILL_DIR}/../../rules/wizard-steps.md`
- Colors and ANSI palette: `${CLAUDE_SKILL_DIR}/../../rules/colors.md`
- Display system (spinner, done/skip/fail): `${CLAUDE_SKILL_DIR}/../../rules/display-system.md`
- Gentle terminal, streaming, piping: `${CLAUDE_SKILL_DIR}/../../rules/gentle-terminal.md`
- SourceResult, error handling: `${CLAUDE_SKILL_DIR}/../../rules/source-results.md`
- Model tiers, streaming, caching: `${CLAUDE_SKILL_DIR}/../../rules/models.md`
- Browser view, SSE: `${CLAUDE_SKILL_DIR}/../../rules/browser-views.md`
- MCP server: `${CLAUDE_SKILL_DIR}/../../rules/mcp-servers.md`
- Flat file storage: `${CLAUDE_SKILL_DIR}/../../rules/flat-files.md`
- Error recovery, crash handling: `${CLAUDE_SKILL_DIR}/../../rules/error-recovery.md`
- Environment setup, .env loading: `${CLAUDE_SKILL_DIR}/../../rules/environment-setup.md`
- Configuration wizard: `${CLAUDE_SKILL_DIR}/../../rules/configuration.md`
- Retry + backoff: `${CLAUDE_SKILL_DIR}/../../rules/retry.md`
- Testing, mock fetch: `${CLAUDE_SKILL_DIR}/../../rules/testing.md`
- Conventions: `${CLAUDE_SKILL_DIR}/../../rules/conventions.md`
