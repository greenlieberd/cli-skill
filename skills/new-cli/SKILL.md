---
name: new-cli
description: Use this skill when the user wants to build a new CLI tool, says "build a new CLI", "create a CLI", "I need a terminal tool for X", "start a CLI project", or asks to scaffold a Bun/Ink/ANSI command-line application. Also use when extending an existing CLI.
argument-hint: "[project-name or path]"
model: sonnet
effort: high
context: fork
allowed-tools: Read, Write, Edit, Glob, Grep, LS, Bash
---

# New CLI — Plan, Scaffold, Verify

Three phases: plan with the user first, then scaffold exactly what the plan specifies, then verify it runs. Never scaffold before the plan is confirmed.

## Context loaded at runtime

Directory: !`pwd`
Bun: !`bun --version 2>/dev/null || echo "NOT INSTALLED"`
Git: !`git rev-parse --is-inside-work-tree 2>/dev/null && echo "repo exists" || echo "no repo"`
Existing package.json: !`[ -f package.json ] && python3 -c 'import json; d=json.load(open("package.json")); print(d.get("name","?"))' 2>/dev/null || echo "none"`

Rules available: !`ls "${CLAUDE_SKILL_DIR}/../../rules/" 2>/dev/null || ls "${CLAUDE_SKILL_DIR}/../../rules/" 2>/dev/null`
Assets available: !`ls "${CLAUDE_SKILL_DIR}/assets/" 2>/dev/null || ls "${CLAUDE_SKILL_DIR}/assets/" 2>/dev/null`

---

## Phase 1 — Environment check

Before anything else:

- **Bun not installed** → "Bun is required for all Propane CLIs. Should I install it? (runs `curl -fsSL https://bun.sh/install | bash`)" — wait for yes.
- **Existing package.json** → "There's already a project here (`[name]`). Are we extending this project or starting in a new subfolder?"
- **`$ARGUMENTS` is a path to an existing project** → run `cli-explorer` on it, use findings in the planning interview to skip questions already answered by the existing code.
- **`$ARGUMENTS` is a project name** → use it, skip the name question in the interview.

---

## Phase 2 — Plan (cli-planner agent)

Launch the `cli-planner` agent. Pass it:
- The user's goal or project name (from `$ARGUMENTS` or from context)
- Any `cli-explorer` findings (if extending an existing project)
- The current directory

The planner conducts a goal-driven interview, recommends architecture, confirms with the user, then writes `.cli/CONTEXT.md`, `.cli/DECISIONS.md`, and `.cli/PLAN.md`.

**Wait for `PLAN_COMPLETE` before continuing.**

---

## Phase 3 — Dependency setup

After `PLAN_COMPLETE`, read the fields and show what will be installed:

```
Based on your plan, here's what this project needs:

  bun (runtime)                  [installed ✓ / needs install]
  @anthropic-ai/sdk              [if ai ≠ none and ≠ piped]
  ink ^5 + react ^19             [if interface = wizard or hybrid]
  ink-text-input ^6              [if interface = wizard or hybrid]
  @modelcontextprotocol/sdk      [if distribution includes mcp]

Create `[name]/` and run `bun install`? (yes / no)
```

On yes:
```bash
mkdir -p [name] && cd [name]
# write package.json first (see below), then:
bun install
git init
git add package.json bun.lockb
git commit -m "chore: init [name]"
```

---

## Phase 4 — Scaffold

Read the `PLAN_COMPLETE` fields. Use this exact mapping to decide what to generate:

| PLAN_COMPLETE field | Value | Files to generate |
|---------------------|-------|-------------------|
| `interface` | `hud` | `src/hud.ts` (from assets/hud.ts, adapted) |
| `interface` | `wizard` | `cli/index.tsx`, `cli/App.tsx`, `cli/components/Frame.tsx`, `cli/components/SelectList.tsx`, `cli/components/TextInput.tsx`, `tsconfig.json` |
| `interface` | `commands` | `src/cli.ts` only (no hud.ts, no cli/ folder) |
| `interface` | `hybrid` | Both `src/hud.ts` AND `cli/` folder |
| `ai` | `fast` | `src/models.ts` with fast tier only |
| `ai` | `smart` | `src/models.ts` with smart tier only |
| `ai` | `both` | `src/models.ts` with fast + smart tiers |
| `ai` | `piped` | No models.ts — add note in CLAUDE.md |
| `ai` | `none` | No models.ts, no @anthropic-ai/sdk |
| `sources` | any list | `src/sources/types.ts` + one `src/sources/<name>.ts` per item |
| `output` | includes `browser` | `src/server.ts` + `ui/index.html` |
| `distribution` | includes `mcp` | `src/mcp.ts` |
| `distribution` | includes `global` | Add `"bin": {"[name]": "src/cli.ts"}` to package.json |

**Generate files in this order.** Show the filename before writing each. Write complete files — no `// TODO` stubs.

1. `CLAUDE.md` — references `.cli/CONTEXT.md`; lists `bun hud` as entry; summarizes architecture
2. `.gitignore` — node_modules, .env, output/, .propane/, .cache/, .fonts/
3. `.env.example` — one line per required key with a `# description` comment above each
4. `package.json` — scripts: hud, test, and optionally mcp/serve/run
5. `src/models.ts` — only the tiers from PLAN_COMPLETE (read `assets/models.ts`)
6. `src/configure.ts` — copy verbatim from `assets/configure.ts`
7. `src/cli.ts` — routes to hud/wizard/run; under 80 lines
8. Interface files (per mapping above) — read assets/ for reference, adapt for this project
9. Source files (per mapping above)
10. Server + UI (per mapping above)
11. MCP server (per mapping above)
12. `tests/cli.test.ts` — bun:test covering configure, models, at least one source

**For HUD-style `src/hud.ts`:**
- Read `assets/hud.ts` and adapt menu items to match this project
- Add `process.stdout.on('resize', redraw)` — required, see cli-ux rules
- Use `Math.min(process.stdout.columns ?? 80, 66)` for all widths — no hardcoded column counts
- Minimum-width guard: if terminal < 50 cols, show a message instead of a broken layout

**For Wizard-style `cli/App.tsx`:**
- Read `assets/App.tsx` and extend with this project's actual steps
- NEXT and PREV maps must cover every step — no dead ends
- Every step component gets exactly `onNext(value)` and `onBack()` — nothing else

Commit:
```bash
git add -A && git commit -m "feat: scaffold [name] ([interface] / [ai] / [sources or no sources])"
```

---

## Phase 5 — Quality review

Launch in parallel:
- `cli-reviewer correctness` — broken imports, wrong paths, missing types, env loaded late
- `cli-reviewer conventions` — models.ts, SourceResult, gitignore, no DB patterns

Apply every fix. Commit:
```bash
git add -A && git commit -m "fix: reviewer corrections"
```

---

## Phase 6 — Verify

```bash
cd [project-path] && bun hud
```

If it crashes, read the error and fix it. Do not mark done with a broken entry point.

```bash
bun test
```

---

## Phase 7 — Ship checklist

- [ ] `bun hud` starts, main screen renders
- [ ] Arrow keys navigate, `ctrl+c` exits cleanly and restores cursor
- [ ] ANSI HUD: resize terminal — layout adapts, doesn't corrupt
- [ ] Wizard: Frame shows correct progress dots for each step
- [ ] At least one menu item or step does real work (not just a placeholder)
- [ ] All tests pass with `bun test`
- [ ] `.env.example` documents every required key
- [ ] `output/` and `.propane/` are in `.gitignore`
- [ ] `.cli/CONTEXT.md`, `.cli/DECISIONS.md`, `.cli/PLAN.md` exist
- [ ] `CLAUDE.md` accurately describes the architecture
- [ ] If browser: `bun serve` opens and status shows "connected"
- [ ] If MCP: `src/mcp.ts` runs, `CLAUDE.md` has registration instructions

Final commit:
```bash
git add -A && git commit -m "chore: ready for first run — [name]"
```

Do not push. Tell the user: "Run `git push` when you're ready to share this."

---

## Rules reference

Read these when generating the corresponding files:

- HUD screen loop, resize, navigation: `${CLAUDE_SKILL_DIR}/../../rules/how-to-hud-screen.md`
- Wizard steps, Frame, progress dots: `${CLAUDE_SKILL_DIR}/../../rules/how-to-wizard-step.md`
- Gentle terminal output, streaming, piping: `${CLAUDE_SKILL_DIR}/../../rules/how-to-gentle-terminal.md`
- SourceResult, error handling: `${CLAUDE_SKILL_DIR}/../../rules/how-to-source-result.md`
- Model tiers, caching: `${CLAUDE_SKILL_DIR}/../../rules/how-to-models.md`
- Browser view, SSE: `${CLAUDE_SKILL_DIR}/../../rules/how-to-browser-view.md`
- MCP server: `${CLAUDE_SKILL_DIR}/../../rules/how-to-mcp-server.md`
- Flat file storage: `${CLAUDE_SKILL_DIR}/../../rules/how-to-flat-files.md`
- Conventions: `${CLAUDE_SKILL_DIR}/../../rules/conventions.md`
