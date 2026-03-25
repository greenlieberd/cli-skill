---
name: cli-audit
description: This skill handles improvement, fixing, extending, and feature management on an existing CLI project. Triggers on "audit this CLI", "improve my CLI", "add a feature to X", "fix the issues", "manage the feature set", "what's in v0.1 vs v0.2", "work through the plan", or any request to evolve a tool that already exists. Reads all existing context before making any changes.
argument-hint: "[path/to/cli-project]"
model: sonnet
effort: high
context: fork
allowed-tools: Read, Write, Edit, Glob, Grep, LS, Bash
---

# cli:audit — Understand the system, then improve it

Full improvement cycle. Loads all existing context first, maps the current feature set, then explores, plans, and executes task by task with commits. Never makes changes without understanding what's already there.

## Context loaded at runtime

Directory: !`pwd`
Target: `$ARGUMENTS`
CONTEXT.md: !`cat "${ARGUMENTS:-.}/.cli/plan/CONTEXT.md" 2>/dev/null | head -80 || echo "none"`
PLAN.md status: !`grep "^> Status:" "${ARGUMENTS:-.}/.cli/plan/PLAN.md" 2>/dev/null || echo "none"`
Existing explore: !`[ -f "${ARGUMENTS:-.}/.cli/audit/EXPLORE.md" ] && echo "found" || echo "none"`
Project memory: !`cat "${ARGUMENTS:-.}/.cli/learnings/SUMMARY.md" 2>/dev/null || echo "none"`

---

## Step 0 — Confirm path

If `$ARGUMENTS` is a path, use it. Otherwise:
```
Which CLI should I audit?
(paste the path, or press enter for current directory)
```

---

## Step 1 — Quick snapshot

Using what's already loaded above, show a fast system snapshot — no additional file reads yet:

```
[project-name]  [plan-status from PLAN.md status]

  Interface: [from CONTEXT.md or "unknown"]
  Memory: [key watch-out from SUMMARY.md, or "none yet"]
```

If CONTEXT.md is missing: "No plan found. I'll explore the project in Step 3."

---

## Step 2 — Ask what we're working on

One question. Options cover the full range of audit work including feature management:

```
What are we working on today?

  A) Fix issues — crashes, broken patterns, convention violations
  B) Improve UX — navigation, output clarity, resize, feedback
  C) Add a feature — pick something from the v0.2+ list, or describe a new one
  D) Manage the feature set — review what's in v0.1, adjust scope, re-prioritize
  E) Prep for release — tests, docs, .env.example, CLAUDE.md
  F) Full audit — explore everything and decide from findings

Or describe what's on your mind.
```

**If D (feature set management):**
Show the current feature table from Step 1 and ask:
```
Here's the current feature set:

  v0.1 (build now):
    [list from PLAN.md]

  v0.2+ (parked):
    [list from PLAN.md]

What would you like to change?
  — Move something from v0.2+ to v0.1
  — Move something from v0.1 to v0.2+ (scope reduction)
  — Add a new feature to either list
  — Remove something entirely

After this we update the plan and decide what to build next.
```

Update PLAN.md to reflect changes before continuing.

---

## Step 2b — Load context for the goal

Read only what the chosen goal needs. Do not load files speculatively.

**A (fix) or B (improve UX) or E (release prep):**
Read `.cli/plan/PLAN.md` in full — need the task list. Skip DECISIONS.md.

**C (add feature):**
Read `.cli/plan/PLAN.md` + `.cli/plan/DECISIONS.md` — need prior decisions to avoid contradicting them.

**D (feature set management):**
Read `.cli/plan/PLAN.md` in full — need both v0.1 and v0.2+ lists to display the feature table.

**F (full audit):**
Read `.cli/plan/PLAN.md` + `.cli/plan/DECISIONS.md` + `.cli/learnings/decisions.md` if present + `.cli/audit/EXPLORE.md` if fresh (< 7 days old).

Show the feature table now if goal is D or F:
```
  ┌──────────────────────────────┬─────────┬──────────────────────────┐
  │ Feature                      │ Version │ Status                   │
  ├──────────────────────────────┼─────────┼──────────────────────────┤
  │ [feature]                    │ v0.1    │ ✓ done / ☐ pending       │
  │ [feature]                    │ v0.2+   │ parked                   │
  └──────────────────────────────┴─────────┴──────────────────────────┘
```

---

## Step 3 — Explore (skip if EXPLORE.md is fresh and goal is known)

If `.cli/audit/EXPLORE.md` doesn't exist, or the goal requires fresh findings, run `cli-explorer`:

> Analyze the CLI at [path]. Report:
> 1. How to run it — entry points, bun scripts
> 2. Interface type — ANSI HUD, Ink Wizard, Commands, Hybrid
> 3. AI usage — model IDs location, tiers, what Claude does
> 4. APIs and sources — what's fetched, SourceResult or throw?
> 5. Output — what gets written, where, in what format
> 6. Storage — .propane/ and output/ contents
> 7. Tests — what's covered, what's missing, mock patterns
> 8. Feature completeness — which v0.1 plan items are actually done vs scaffolded
> 9. Convention gaps — hardcoded models, throwing sources, no resize, no CLAUDE.md
> 10. The 5 files to read first before touching anything

Write findings to `.cli/audit/EXPLORE.md`.

Show a summary table:
```
Explored [project-name]:

  ┌──────────────────┬───────────────────────────────────────────────┐
  │ Interface        │ [type] — [key file]                           │
  │ AI               │ [usage summary]                               │
  │ Sources          │ [N] total — [X] ok, [Y] throwing              │
  │ Tests            │ [coverage summary]                            │
  │ Convention gaps  │ [N] found                                     │
  └──────────────────┴───────────────────────────────────────────────┘

  Issues:
    ✗ [most important]
    ✗ [second]
    ✗ [third if any]

Full findings → .cli/audit/EXPLORE.md
```

---

## Step 4 — Plan improvements

Spawn the `cli-planner` agent (via Task tool) in **improve mode** with:
- The EXPLORE.md findings
- The system context already loaded (CONTEXT.md, PLAN.md)
- The user's stated goal from Step 2

The planner:
- Does not re-open decisions already in DECISIONS.md
- Does not suggest features already deferred to v0.2+
- Writes tasks that fit the existing architecture
- Produces: `.cli/plan/PLAN.md` updated with new tasks in the correct section

Show the plan before executing:

```
Improvement plan — [N] tasks:

  ┌────┬─────────────────────────────────┬──────────┬──────────────────────────┐
  │ #  │ Task                            │ Type     │ Why                      │
  ├────┼─────────────────────────────────┼──────────┼──────────────────────────┤
  │ 1  │ [task name]                     │ fix      │ [one-line reason]        │
  │ 2  │ [task name]                     │ feat     │ [one-line reason]        │
  │ 3  │ [task name]                     │ test     │ [one-line reason]        │
  └────┴─────────────────────────────────┴──────────┴──────────────────────────┘

  Parked for later (not in this run):
    — [feature or fix deferred]

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
  │ What changed         │ [grouped by type: fixes / features / tests]│
  │ Convention status    │ ✓ models.ts / ✓ SourceResult / ✓ resize   │
  │ Test status          │ bun test: [pass / fail summary]            │
  │ v0.1 progress        │ [X of N tasks complete]                   │
  │ v0.2+ parked         │ [N features waiting]                      │
  └──────────────────────┴───────────────────────────────────────────┘

Run /cli:learn [path] after a few more sessions to extract patterns.
Run git push when you're ready.
```

---

## Rules reference

Read before working on the corresponding file type:

- HUD, resize, navigation: `${CLAUDE_SKILL_DIR}/../../rules/hud-screens.md`
- ASCII art: `${CLAUDE_SKILL_DIR}/../../rules/ascii-art.md`
- Colors: `${CLAUDE_SKILL_DIR}/../../rules/colors.md`
- Display system: `${CLAUDE_SKILL_DIR}/../../rules/display-system.md`
- SourceResult: `${CLAUDE_SKILL_DIR}/../../rules/source-results.md`
- Models: `${CLAUDE_SKILL_DIR}/../../rules/models.md`
- Error recovery: `${CLAUDE_SKILL_DIR}/../../rules/error-recovery.md`
- Testing: `${CLAUDE_SKILL_DIR}/../../rules/testing.md`
- Retry: `${CLAUDE_SKILL_DIR}/../../rules/retry.md`
- Conventions: `${CLAUDE_SKILL_DIR}/../../rules/conventions.md`
