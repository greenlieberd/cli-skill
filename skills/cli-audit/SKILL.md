---
name: audit
description: Use this skill when the user wants to improve, fix, extend, or manage features on an existing CLI. Triggers on "audit this CLI", "improve my CLI", "add a feature", "fix the issues", "manage the feature set", "what's in v0.1 vs v0.2", "work through the plan", or any request to evolve an existing tool. Loads full system context first, then explores, plans, and executes. Skips phases already done if .cli/ files exist.
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
CONTEXT.md: !`cat "${ARGUMENTS:-.}/.cli/plan/CONTEXT.md" 2>/dev/null | head -40 || echo "none"`
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

## Step 1 — Load system context

Before exploring the code, read everything that already exists about this project.

Read in order (skip gracefully if not found):
1. `.cli/plan/CONTEXT.md` — what the project is, v0.1 scope, conventions
2. `.cli/plan/DECISIONS.md` — why each architecture choice was made
3. `.cli/plan/PLAN.md` — current task progress, v0.1 vs v0.2+ breakdown
4. `.cli/learnings/SUMMARY.md` — patterns, watch-outs, known errors from past sessions
5. `.cli/learnings/decisions.md` — choices already made, don't re-open
6. `.cli/audit/EXPLORE.md` — last explore findings if present

Then show a system snapshot:

```
System context loaded — [project-name]

  ┌─────────────────┬──────────────────────────────────────────────────┐
  │ Interface       │ [from CONTEXT.md or "unknown"]                   │
  │ AI              │ [tiers + purpose or "none"]                      │
  │ APIs            │ [list or "none"]                                 │
  │ Output          │ [type]                                           │
  │ Distribution    │ [how it's used]                                  │
  └─────────────────┴──────────────────────────────────────────────────┘

  Plan progress: [X of N v0.1 tasks complete]

  Feature set:
  ┌──────────────────────────────┬─────────┬──────────────────────────┐
  │ Feature                      │ Version │ Status                   │
  ├──────────────────────────────┼─────────┼──────────────────────────┤
  │ [feature from plan]          │ v0.1    │ ✓ done / ☐ pending       │
  │ [feature from plan]          │ v0.1    │ ✓ done / ☐ pending       │
  │ [feature from v0.2+ list]    │ v0.2+   │ parked                   │
  └──────────────────────────────┴─────────┴──────────────────────────┘

  [If learnings exist:]
  Memory: [key watch-out from SUMMARY.md]
```

If CONTEXT.md and PLAN.md don't exist yet, note it and continue — the explore step will fill in what's missing.

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

Run `cli-planner` in **improve mode** with:
- The EXPLORE.md findings
- The system context from Step 1
- The user's stated goal from Step 2
- The current PLAN.md feature set

The planner:
- Does not re-open decisions already in DECISIONS.md
- Does not suggest features already deferred to v0.2+
- Writes tasks that fit the existing architecture
- Produces:
  - `.cli/plan/PLAN.md` — updated with new tasks in the right section
  - `.cli/audit/GAPS.md` — convention violations found
  - `.cli/audit/FIXES.md` — improvement list, human-readable

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
