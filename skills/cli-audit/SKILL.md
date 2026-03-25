---
name: cli-audit
description: This skill should be used when the user wants a strategic review of an existing CLI — what's working, what's broken, what to build next. Triggers on "audit this CLI", "what should I work on next", "review my project", "what's the state of X", "health check", or any request to understand and improve a CLI that already exists. Loads all context first, proposes multiple directions with trade-offs, then executes the chosen one task by task with commits.
argument-hint: "[path/to/cli-project]"
model: sonnet
effort: high
context: fork
allowed-tools: Read, Write, Edit, Glob, Grep, LS, Bash
---

# cli:audit — Read everything. Propose directions. Execute.

Strategic review first, execution second. Never asks "what do you want to do?" — reads everything that exists, assesses the full picture, then presents options with trade-offs. The user picks a direction. Then it executes, task by task, with commits.

## Context loaded at runtime

Directory: !`pwd`
Target: `$ARGUMENTS`
CONTEXT.md: !`cat "${ARGUMENTS:-.}/.cli/plan/CONTEXT.md" 2>/dev/null | head -80 || echo "none"`
PLAN.md: !`cat "${ARGUMENTS:-.}/.cli/plan/PLAN.md" 2>/dev/null || echo "none"`
DECISIONS.md: !`cat "${ARGUMENTS:-.}/.cli/plan/DECISIONS.md" 2>/dev/null | head -60 || echo "none"`
Project memory: !`cat "${ARGUMENTS:-.}/.cli/learnings/SUMMARY.md" 2>/dev/null | head -30 || echo "none"`
Sessions logged: !`ls "${ARGUMENTS:-.}/.cli/sessions/"*.jsonl 2>/dev/null | grep -v errors_buffer | wc -l | tr -d ' '`
Last session: !`ls -t "${ARGUMENTS:-.}/.cli/sessions/"*.jsonl 2>/dev/null | grep -v errors_buffer | head -1 | xargs basename 2>/dev/null | sed 's/.jsonl//' || echo "none"`
Recent errors: !`cat "${ARGUMENTS:-.}/.cli/sessions/.errors_buffer.jsonl" 2>/dev/null | tail -5 || echo "none"`
EXPLORE.md: !`[ -f "${ARGUMENTS:-.}/.cli/audit/EXPLORE.md" ] && (find "${ARGUMENTS:-.}/.cli/audit/EXPLORE.md" -mtime +7 2>/dev/null && echo "stale" || echo "fresh") || echo "missing"`

---

## Step 0 — Confirm path

If `$ARGUMENTS` is a path, use it. Otherwise:
```
Which CLI should I audit?
(paste the path, or press enter for current directory)
```

---

## Step 1 — Explore if needed

If EXPLORE.md is `missing` or `stale`: spawn `cli-explorer` agent (via Task tool) to map the codebase.

> Analyze the CLI at [path]. Report:
> 1. How to run it — entry points, bun scripts
> 2. Interface type — ANSI HUD, Ink Wizard, Commands, Hybrid
> 3. AI usage — model IDs location, tiers, what Claude does
> 4. APIs and sources — what's fetched, SourceResult or throw?
> 5. Output — what gets written, where, in what format
> 6. Tests — what's covered, what's missing
> 7. Feature completeness — v0.1 plan items: done vs. scaffolded vs. missing
> 8. Convention gaps — hardcoded models, throwing sources, no resize, no CLAUDE.md
> 9. The 5 files to read first before touching anything

Write findings to `.cli/audit/EXPLORE.md`. Wait for completion before continuing.

If EXPLORE.md is `fresh`: read it now — `cat .cli/audit/EXPLORE.md | head -100`.

---

## Step 2 — Full analysis

With all context loaded, assess the full picture. Think like an architect and reviewer simultaneously.

**What's working:**
- Convention-clean areas (models in models.ts, sources returning SourceResult, tests passing)
- Stable features with no recent errors
- Plan tasks completed on schedule

**What's broken or drifting:**
- Convention violations (hardcoded model IDs, throwing sources, missing resize handler)
- Failing or missing tests
- Recurring errors from the error buffer
- Tasks marked pending for 3+ sessions without progress

**What's stalled:**
- v0.2+ features that have been parked for many sessions — are they still real?
- Plan tasks that were started but never committed

**What the history says:**
- Session count and frequency pattern
- Key watch-outs from SUMMARY.md
- Last session date — is this a return after a long break?

---

## Step 3 — Health snapshot + directions

Present the health snapshot first, then three directions. Never skip the snapshot.

```
[project-name] — audit

  ┌──────────────────────────────────────────────────────────┐
  │ Plan       [X of N] tasks complete · [P] pending         │
  │ Sessions   [N] logged · last: [date or "today"]          │
  │ Issues     [N] convention violations · [N] stalled       │
  │ Tests      [passing / failing / missing]                  │
  └──────────────────────────────────────────────────────────┘

What I found:
  ✗ [most critical issue]
  ✗ [second issue]
  — [stalled item or pattern worth noting]

Three directions:

  A) [Direction name]
     [What this does in 1-2 sentences]
     Trade-off: [what you get vs. what you give up]
     Estimate: [N sessions]

  B) [Direction name]
     [What this does in 1-2 sentences]
     Trade-off: [what you get vs. what you give up]
     Estimate: [N sessions]

  C) [Direction name]
     [What this does in 1-2 sentences]
     Trade-off: [what you get vs. what you give up]
     Estimate: [N sessions]

Which direction? Or describe what's on your mind.
```

**Direction archetypes to draw from — pick the 3 most relevant:**

- **Stabilize** — fix violations and failing tests. Conservative, high confidence.
- **Ship a feature** — promote something from v0.2+ and build it now.
- **Refactor then extend** — clean the foundation before adding anything.
- **Scope down** — move something from v0.1 to v0.2+. Smaller but shippable sooner.
- **Prep for release** — tests, docs, .env.example, CLAUDE.md, ship checklist.
- **Start fresh plan** — current plan is stale; re-plan before executing anything.

Always include trade-offs. Never present one direction as obviously correct.

---

## Step 4 — Build the task list

Based on the chosen direction, produce a concrete task list. Spawn `cli-planner` agent (via Task tool) in **improve mode** with:
- The chosen direction and its constraints
- EXPLORE.md findings
- CONTEXT.md, PLAN.md, DECISIONS.md already loaded
- Instruction: do not re-open decisions in DECISIONS.md, do not contradict existing architecture

The planner produces an updated `.cli/plan/PLAN.md`. Show the tasks before executing:

```
[Direction name] — [N] tasks:

  ┌────┬─────────────────────────────────┬──────────┬──────────────────────────┐
  │ #  │ Task                            │ Type     │ Why                      │
  ├────┼─────────────────────────────────┼──────────┼──────────────────────────┤
  │ 1  │ [task name]                     │ fix      │ [one-line reason]        │
  │ 2  │ [task name]                     │ feat     │ [one-line reason]        │
  │ 3  │ [task name]                     │ test     │ [one-line reason]        │
  └────┴─────────────────────────────────┴──────────┴──────────────────────────┘

  Parked (not in this run):
    — [item deferred]

Proceed with all? Or tell me where to start.
```

Wait for confirmation.

---

## Step 5 — Execute task by task

Work through tasks top to bottom. One at a time.

Before each task:
```
Working on: [task name]  ([type])
[One sentence — what this does and why]
```

**By task type:**

`fix` — minimal, targeted:
- Hardcoded model ID → move to `src/models.ts`, grep all, replace with `MODELS.fast.id`
- Source throws → `return sourceError(source, label, err)`, import the helper
- No resize handler → `process.stdout.on('resize', redraw)` in hud.ts
- Missing CLAUDE.md → write from `.cli/plan/CONTEXT.md`

`feat` — read CONTEXT.md first, then the relevant rule, write complete files, no stubs:
- Check `.cli/plan/DECISIONS.md` — don't contradict a prior decision
- Check `.cli/learnings/watch-out.md` — known gotchas for this project
- Reference the correct rule from `${CLAUDE_SKILL_DIR}/../../rules/`

`refactor` — read the full file, extract at clean boundaries, update all imports

`test` — follow the existing mock pattern, test the specific case in the task

`docs` — accurate > comprehensive, CLAUDE.md under 80 lines

`chore` — minimal change only

**After each task:**

1. Verify:
```bash
cd [path] && bun typecheck 2>&1 | head -20
bun test 2>&1 | tail -10
```
If entry point was touched: ask user to confirm `bun hud` starts.

2. Commit:
```bash
git add -A && git commit -m "[type]: [task name]"
```

3. Check off in PLAN.md: `- [ ]` → `- [x]`, update status line.

4. Show progress:
```
✓ [task name]  [X of N]

Next: [task] — [one sentence]
Continue? (yes / skip / stop)
```

**skip** → mark `- [~]`, move to next.
**stop** → "Resume with `/cli:audit [path]` when ready."

---

## Step 6 — Finish

When all tasks are done:

```
✓ [N] tasks complete — [project-name]

  ┌──────────────────────┬───────────────────────────────────────────┐
  │ What changed         │ [grouped: fixes / features / tests]       │
  │ Convention status    │ ✓ models.ts / ✓ SourceResult / ✓ resize   │
  │ Test status          │ bun test: [pass / fail summary]           │
  │ v0.1 progress        │ [X of N tasks complete]                   │
  │ v0.2+ parked         │ [N features waiting]                      │
  └──────────────────────┴───────────────────────────────────────────┘

Run /cli:learn [path] after a few more sessions to extract patterns.
Run git push when you're ready.
```

---

## Rules reference

Read before working on the corresponding file type. Always read only what the task requires.

**Foundation (always):**
- `rules/conventions.md` — naming, patterns, non-negotiables
- `rules/folder-structure.md` — canonical src/, cli/, output/, .propane/, .cli/ layout

**HUD (interface = hud or hybrid):**
- `rules/hud-screens.md` — screen state machine, resize, entry points
- `rules/ascii-art.md` — logo pattern, 6-line block letters
- `rules/alternate-screen.md` — fullscreen buffer entry/exit
- `rules/layouts.md` — sidebar, split-pane, modal, pinned footer
- `rules/spinners.md` — multi-phase loading indicators
- `rules/tables.md` — tabular data, column alignment, scroll
- `rules/tabs.md` — tab bar, ◄ ► switching, count badges
- `rules/keyboard-shortcuts.md` — shortcut design, help overlay
- `rules/clipboard.md` — pbcopy/pbpaste integration

**Wizard (interface = wizard or hybrid):**
- `rules/wizard-steps.md` — NEXT/PREV maps, step props, Frame
- `rules/confirmation.md` — y/n prompts for destructive actions
- `rules/rich-input.md` — multi-line, paste, image, stdin capture

**Hybrid:**
- `rules/hybrid-interface.md` — wiring HUD home to Ink sub-flows

**Display (any interface):**
- `rules/colors.md` — ANSI color constants, theme presets
- `rules/display-system.md` — output formatting, alignment
- `rules/gentle-terminal.md` — streaming, piped output, cursor
- `rules/notifications.md` — macOS osascript alerts
- `rules/diff-output.md` — before/after color-coded diffs

**Sources:**
- `rules/source-results.md` — SourceResult shape, never throw
- `rules/retry.md` — backoff, max attempts, error propagation
- `rules/caching.md` — .cache/ TTL, diff tracking, cache-first fetch
- `rules/limits.md` — LIMITS registry, rate limits, batch sizes
- `rules/parallelization.md` — Promise.allSettled, concurrent sources

**AI:**
- `rules/models.md` — model IDs only in models.ts, {id, maxTokens}
- `rules/token-spend.md` — tracking usage, cost estimation per call
- `rules/stream-to-agents.md` — stdout JSON lines, subprocess pipes

**Output & Storage:**
- `rules/flat-files.md` — .propane/ patterns, no databases
- `rules/output-files.md` — date-stamped naming, manifest, open from HUD
- `rules/logging.md` — JSONL usage/error logs, rotation

**Infrastructure:**
- `rules/error-recovery.md` — crash handling, process.exit()
- `rules/testing.md` — bun:test, mock fetch, fixture cleanup
- `rules/configuration.md` — configure.ts, loadEnv(), maskValue()
- `rules/environment-setup.md` — .env.example, key docs

**Browser:**
- `rules/browser-views.md` — SSE, HTML UI, status display
- `rules/file-watch.md` — Bun fs.watch → SSE → live reload

**Distribution:**
- `rules/mcp-servers.md` — stdio MCP server, Claude Desktop registration
- `rules/global-install.md` — bin config, global command install
- `rules/update-checker.md` — non-blocking startup version check

**Ecosystem:**
- `rules/plugin-ecosystem.md` — Claude Code plugins worth composing with
- `rules/workspace-settings.md` — .claude/ config, skills, hooks setup
