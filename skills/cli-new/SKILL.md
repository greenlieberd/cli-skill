---
name: new
description: Use this skill when the user wants to build a new CLI tool from scratch. Triggers on "build a new CLI", "create a CLI", "I need a terminal tool for X", "start a CLI project", "scaffold a new Bun tool", or any request to build something that doesn't exist yet. Pass a project name to skip the first question. Runs a planning interview first, then scaffolds the full project.
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

---

## Phase 1 — Environment check

Check before anything else:

- **Bun not installed** → "Bun is required. Should I install it? (runs `curl -fsSL https://bun.sh/install | bash`)" — wait for yes.
- **`$ARGUMENTS` is a path to an existing project** → run `cli-explorer` on it first, use findings to skip questions already answered by the code.
- **`$ARGUMENTS` is a project name** → use it, skip the name question.
- **Existing package.json** → "There's already a project here (`[name]`). Are we extending it or starting in a new subfolder?"

---

## Phase 2 — Plan

Launch `cli-planner` agent. Pass:
- The goal or name from `$ARGUMENTS`
- Any `cli-explorer` findings (if extending)
- Current directory

The planner runs the same interview as `cli:plan` — interface, AI usage, sources, output, distribution — then writes:
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

**Write in this order. Announce each file before writing it. No `// TODO` stubs.**

1. `CLAUDE.md` — references `.cli/plan/CONTEXT.md`, lists `bun hud`, summarizes architecture
2. `.gitignore` — node_modules, .env, output/, .propane/, .cache/, .fonts/
3. `.env.example` — one line per key, `# description` above each
4. `package.json` — scripts: hud, test, and optionally mcp/serve/run
5. `src/models.ts` — only the tiers from PLAN_COMPLETE (read assets/models.ts)
6. `src/configure.ts` — copy verbatim from assets/configure.ts
7. `src/cli.ts` — routes to hud/wizard/run, under 80 lines
8. Interface files — read assets/ for reference, adapt for this project
9. Source files
10. Server + UI (if browser)
11. MCP server (if mcp)
12. `tests/cli.test.ts` — bun:test covering configure, models, at least one source

**HUD rules** (read `${CLAUDE_SKILL_DIR}/../../rules/hud-screens.md`):
- Adapt menu items from assets/hud.ts to this project
- `process.stdout.on('resize', redraw)` — required
- `Math.min(process.stdout.columns ?? 80, 66)` for all widths
- If terminal < 50 cols, show a message instead of a broken layout

**Wizard rules** (read `${CLAUDE_SKILL_DIR}/../../rules/wizard-steps.md`):
- Extend assets/App.tsx with this project's actual steps
- NEXT and PREV maps must cover every step — no dead ends
- Every step gets exactly `onNext(value)` and `onBack()` props

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

## Phase 7 — Ship checklist

- [ ] `bun hud` starts, main screen renders
- [ ] Arrow keys navigate, `ctrl+c` exits cleanly and restores cursor
- [ ] ANSI HUD: resize terminal — layout adapts, no corruption
- [ ] Wizard: Frame shows correct progress dots per step
- [ ] At least one menu item or step does real work (not a placeholder)
- [ ] All tests pass with `bun test`
- [ ] `.env.example` documents every required key
- [ ] `output/` and `.propane/` are in `.gitignore`
- [ ] `.cli/plan/CONTEXT.md`, `.cli/plan/DECISIONS.md`, `.cli/plan/PLAN.md` exist
- [ ] `CLAUDE.md` accurately describes the architecture
- [ ] If browser: `bun serve` opens and status shows "connected"
- [ ] If MCP: `src/mcp.ts` runs, `CLAUDE.md` has registration instructions

```bash
git add -A && git commit -m "chore: ready for first run — [name]"
```

Tell the user: "Run `git push` when you're ready to share this."

---

## Rules reference

Read when generating the corresponding files:

- HUD screen loop, resize, navigation: `${CLAUDE_SKILL_DIR}/../../rules/hud-screens.md`
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
