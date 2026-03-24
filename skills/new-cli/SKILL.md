---
name: new-cli
description: Use this skill when the user wants to build a new CLI tool, says "build a new CLI", "create a CLI", "I need a terminal tool for X", "start a CLI project", or asks to scaffold a Bun/Ink/ANSI command-line application. Also use when extending an existing CLI with new capabilities.
argument-hint: "[project-name or path]"
model: sonnet
effort: high
context: fork
allowed-tools: Read, Write, Edit, Glob, Grep, LS, Bash
---

# New CLI — Plan, Scaffold, and Verify

Build a new CLI project through three phases: plan with the user, scaffold the code, verify it runs. Never scaffold before the plan is confirmed.

## Context loaded at runtime

Directory: !`pwd`

Environment:
!`echo "bun: $(bun --version 2>/dev/null || echo 'NOT INSTALLED')" && echo "git: $(git rev-parse --is-inside-work-tree 2>/dev/null && echo 'repo exists' || echo 'no repo')" && echo "existing package.json: $([ -f package.json ] && python3 -c 'import json; d=json.load(open(\"package.json\")); print(d.get(\"name\",\"?\"))' 2>/dev/null || echo none)"`

References available:
!`echo "guides: $(ls ${CLAUDE_SKILL_DIR}/../../guides/ 2>/dev/null | tr '\n' ' ')" && echo "examples: $(ls ${CLAUDE_SKILL_DIR}/examples/ 2>/dev/null | tr '\n' ' ')"`

---

## Phase 1 — Plan

### Step 1a — Handle arguments + environment

- If `$ARGUMENTS` is a project name: use it, skip to Step 1b
- If `$ARGUMENTS` is a path to an existing project: run `cli-explorer` on it first, use findings to pre-answer the planning interview, then continue
- If Bun is not installed: tell the user now — "Bun is required. Should I install it? (`curl -fsSL https://bun.sh/install | bash`)" — wait for yes before running
- If a `package.json` already exists here: "There's already a project named `[name]` here. Are we extending this or starting in a new subfolder?"

### Step 1b — Run the planning interview

Launch the `cli-planner` agent. Pass it:
- The user's stated goal or project name from `$ARGUMENTS`
- Any findings from the explorer (if extending an existing project)
- The current directory path

The planner will conduct a goal-driven interview, make architecture recommendations, write `.cli/CONTEXT.md`, `.cli/DECISIONS.md`, and `.cli/PLAN.md`, and return a structured `PLAN_COMPLETE` summary.

**Wait for the planner to return `PLAN_COMPLETE` before continuing.**

---

## Phase 2 — Dependency setup

After receiving `PLAN_COMPLETE`, show the user what will be installed based on the plan:

```
Here's what this project needs:

  ✓ bun (runtime)                     [already installed / needs install]
  ✓ @anthropic-ai/sdk                 [if AI: yes]
  ✓ ink ^5 + react ^19                [if interface: wizard]
  ✓ ink-text-input ^6                 [if interface: wizard]
  ✓ @modelcontextprotocol/sdk         [if distribution: mcp]

Should I create the project folder and run `bun install`?
I'll write package.json first — you can review before I install anything.
```

Wait for explicit confirmation ("yes" / "go ahead" / "do it") before running `bun install`.

On confirmation:
1. `mkdir -p <name>` — create project folder
2. Write `package.json` first (user can review)
3. `cd <name> && bun install`
4. `git init && git add package.json bun.lockb && git commit -m "chore: init project"`

---

## Phase 3 — Scaffold

Generate files in this order. Show the filename before writing each one. Write each completely — no `// TODO` stubs.

**Always (every project):**
1. `CLAUDE.md` — references `.cli/` for context, lists run command and architecture
2. `.gitignore` — node_modules, .env, output/, .propane/, .cache/, .fonts/
3. `.env.example` — one line per required key with a description comment
4. `manifest.json` — capabilities: commands, ai tiers, sources, browser, mcp
5. `src/models.ts` — only the tiers from the plan (see examples/models.ts)
6. `src/configure.ts` — copy verbatim from examples/configure.ts
7. `src/cli.ts` — command router, under 80 lines

**If interface = hud:**
- `src/hud.ts` — ANSI screen loop with ASCII art header
  - Read `examples/hud.ts` and adapt it for this project's menu items
  - Add `process.stdout.on('resize', redraw)` — see guide 08
  - Width-safe: use `Math.min(process.stdout.columns ?? 80, 66)` not hardcoded numbers

**If interface = wizard:**
- `cli/index.tsx` — `render(<App />)`
- `cli/App.tsx` — step state machine with NEXT/PREV maps (see examples/App.tsx)
- `cli/components/Frame.tsx` — copy from examples/Frame.tsx
- `cli/components/SelectList.tsx` — copy from examples/SelectList.tsx
- `cli/components/TextInput.tsx` — wraps ink-text-input with ← back support
- `tsconfig.json` — jsx: react-jsx, jsxImportSource: react

**If sources (external APIs):**
- `src/sources/types.ts` — copy from examples/sources/types.ts
- `src/sources/<api>.ts` — one stub per source from the plan

**If output = browser:**
- `src/server.ts` — Bun.serve with /events SSE, /health, /message POST
- `ui/index.html` — copy the template from guides/ui-patterns.md, replace CLI_NAME

**If distribution = mcp:**
- `src/mcp.ts` — copy from guides/mcp-patterns.md template

**Always last:**
- `tests/cli.test.ts` — bun:test for configure (env loading), models (export shape), at least one source round-trip

Commit after scaffold:
```bash
git add -A && git commit -m "feat: scaffold [name] — [interface] interface, [AI tier] AI, [sources]"
```

---

## Phase 4 — Quality review

Launch two `cli-reviewer` agents in parallel:
- `cli-reviewer correctness` — broken imports, bad paths, missing types, env vars used before load
- `cli-reviewer conventions` — models.ts, SourceResult, no DB patterns, .propane/ gitignored

Apply every fix. Commit fixes:
```bash
git add -A && git commit -m "fix: apply reviewer corrections"
```

---

## Phase 5 — Verify

```bash
cd <project-path> && bun hud
```

If it crashes, read the error and fix it. Do not present a broken project as done.

Run tests:
```bash
bun test
```

---

## Phase 6 — Ship checklist

Present this to the user. Do not claim done until all pass:

- [ ] `bun hud` starts without errors
- [ ] Main menu renders with correct items
- [ ] Arrow keys navigate, `ctrl+c` exits cleanly (cursor restored)
- [ ] ASCII art renders (HUD) or Frame title shows (Wizard)
- [ ] At least one menu item / wizard step does real work
- [ ] All tests pass with `bun test`
- [ ] `.env.example` lists every required key with a comment
- [ ] `output/` and `.propane/` are in `.gitignore`
- [ ] `.cli/` folder exists with CONTEXT.md, DECISIONS.md, PLAN.md
- [ ] If browser: `bun serve` opens and shows "connected"
- [ ] If MCP: `src/mcp.ts` runs and CLAUDE.md has registration instructions
- [ ] If ANSI HUD: resize terminal — layout should adapt, not break

Final commit:
```bash
git add -A && git commit -m "chore: ready for first run"
```

Do not push to remote. Tell the user: "Run `git push` when you're ready to share this."

---

## Reference

- UX patterns (resize, navigation, feedback, error messages): `${CLAUDE_SKILL_DIR}/../../guides/cli-ux.md`
- Folder structure: `${CLAUDE_SKILL_DIR}/../../guides/folder-structure.md`
- UI templates: `${CLAUDE_SKILL_DIR}/../../guides/ui-patterns.md`
- Data philosophy: `${CLAUDE_SKILL_DIR}/../../guides/data-philosophy.md`
- MCP patterns: `${CLAUDE_SKILL_DIR}/../../guides/mcp-patterns.md`
- Example files: `${CLAUDE_SKILL_DIR}/examples/`
