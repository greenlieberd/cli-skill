---
name: audit
description: Use this skill when the user wants to improve, fix, or evolve an existing CLI. Triggers on "audit this CLI", "improve my CLI", "fix the issues", "work through the plan", "what needs changing", "review and fix", or when the user has an existing Bun/ANSI/Ink CLI and wants it better. Combines explore + plan + execute into one flow. Skips phases already done if .cli/ files exist.
argument-hint: "[path/to/cli-project]"
model: sonnet
effort: high
context: fork
allowed-tools: Read, Write, Edit, Glob, Grep, LS, Bash
---

# cli:audit — Explore, plan, improve

Full improvement cycle for an existing CLI. Explores the codebase, asks what you want to change, writes a plan, then executes it task by task with commits. Skips phases that are already done.

## Context loaded at runtime

Directory: !`pwd`
Target: `$ARGUMENTS`
Existing explore: !`[ -f "${ARGUMENTS:-.}/.cli/audit/EXPLORE.md" ] && echo "found" || echo "none"`
Existing plan: !`[ -f "${ARGUMENTS:-.}/.cli/plan/PLAN.md" ] && echo "found" || echo "none"`
Project memory: !`cat "${ARGUMENTS:-.}/.cli/learnings/SUMMARY.md" 2>/dev/null || echo "none"`

---

## Step 0 — Confirm and orient

If `$ARGUMENTS` is a path, use it. Otherwise:
```
Which CLI should I audit?
(paste the path, or press enter for current directory)
```

Then show what already exists:

```
Auditing: [path]

  .cli/audit/EXPLORE.md  — [found, will reuse | not found, will explore]
  .cli/plan/PLAN.md      — [found: X of N tasks complete | not found, will plan]

[If plan found with tasks remaining:]
  There's an existing plan with [N] tasks remaining.
  A) Continue working through it
  B) Re-explore and re-plan (overwrites existing plan)
  C) Add to the existing plan after re-exploring

Which would you like?
```

If plan is complete or not found, continue to explore.

---

## Step 1 — Explore (skip if EXPLORE.md is fresh)

If `.cli/audit/EXPLORE.md` does not exist, run the `cli-explorer` agent:

> Analyze the CLI at [path]. Report:
> 1. How to run it — entry point, bun scripts
> 2. Interface type — ANSI HUD, Ink Wizard, Commands, Hybrid
> 3. AI usage — model IDs, what Claude does, which tiers
> 4. Data sources — what APIs or files, SourceResult or throw?
> 5. Output — what gets written, where
> 6. Storage — .propane/ and output/
> 7. Tests — coverage and gaps
> 8. Convention gaps — hardcoded models, throwing sources, no resize, no CLAUDE.md
> 9. The 5 files to read first

Write findings to `.cli/audit/EXPLORE.md`.

Show the user a quick summary:
```
Explored [project-name]:

  Interface:  [type]
  Sources:    [N] ([working] ok, [broken] need fixing)
  Tests:      [summary]
  Issues:     [N] found

Full details → .cli/audit/EXPLORE.md
```

---

## Step 2 — Understand the goal

One question, not a form:

```
What are you trying to improve?

  A) Fix issues — crashes, broken patterns, convention violations
  B) Better UX — navigation, output clarity, resize handling, feedback
  C) New capabilities — sources, commands, interface features
  D) Prep for release — tests, docs, .env.example, CLAUDE.md
  E) All of the above — full audit

Or tell me what's on your mind.
```

---

## Step 3 — Plan improvements

Run the `cli-planner` agent in **improve mode**. Pass:
- The EXPLORE.md findings
- The user's stated goal
- The project path

The planner produces improvements as a PLAN.md — ordered by impact, scoped to what was asked. It writes:
- `.cli/plan/CONTEXT.md` (create or update)
- `.cli/plan/DECISIONS.md` (create or update)
- `.cli/plan/PLAN.md`
- `.cli/audit/GAPS.md` — issues found vs conventions
- `.cli/audit/FIXES.md` — prioritized improvement list (mirrors PLAN.md, human-readable)

Show the plan to the user before executing:
```
Here's the improvement plan — [N] tasks:

Build next:
  1. [task] — [one sentence]
  2. [task] — [one sentence]
  3. [task]

Later:
  4. [task]
  5. [task]

Proceed with all? Or pick where to start.
```

Wait for confirmation.

---

## Step 4 — Execute task by task

Work through `.cli/plan/PLAN.md` top to bottom. One task at a time.

Before each task:
```
Working on: [task name]
Type: [feat | fix | refactor | test | docs | chore]
[One sentence description]
```

**By task type:**

`fix` — minimal change, don't refactor surroundings:
- Hardcoded model ID → move to `src/models.ts`, grep all occurrences, replace with `MODELS.fast.id`
- Source throws → replace `throw` with `return sourceError(source, label, err)`
- No resize handler → add `process.stdout.on('resize', redraw)` to hud.ts
- No CLAUDE.md → write from `.cli/plan/CONTEXT.md`

`feat` — read `.cli/plan/CONTEXT.md` first, check assets/ for reference patterns, write complete files:
- Read `${CLAUDE_SKILL_DIR}/../../rules/[relevant-rule].md` before writing
- No stubs, no TODOs

`refactor` — read the full file before splitting, extract at clean boundaries, update all imports

`test` — follow the existing mock/fixture pattern, test the specific case named in the task

`docs` — accurate over comprehensive, keep CLAUDE.md under 80 lines

`chore` — minimal change only

**After each task:**

1. Verify:
   ```bash
   cd [path] && bun typecheck 2>&1 | head -20
   bun test 2>&1 | tail -10
   ```
   If entry point was touched: ask user to run `bun hud` and confirm it starts.

2. Commit:
   ```bash
   git add -A && git commit -m "[type]: [task name]"
   ```

3. Check off in PLAN.md:
   - `- [ ]` → `- [x]`
   - Update status line: `Status: [X] of [N] tasks complete`

4. Show progress:
   ```
   ✓ [task name]
   Progress: [X] of [N]

   Next: [task] — [description]
   Continue? (yes / skip / stop)
   ```

**skip** → mark as `- [~]` (deferred), move to next.
**stop** → "Resume with `/cli:audit [path]` when you're ready."

---

## Step 5 — Finish

When all tasks are done:

```
✓ All [N] tasks complete — [project-name] is in good shape.

What changed:
  [bulleted list of completed tasks, grouped by type]

Convention status:
  ✓ Model IDs centralized
  ✓ Sources return SourceResult
  ✓ Resize handler present
  [etc.]

Run /cli:explore [path] again anytime to check current state.
```

Run a final check:
```bash
cd [path] && bun hud && bun test
```

Do not push. Tell the user: "Run `git push` when you're ready."

---

## Rules reference

Read when working on the corresponding task types:

- HUD resize, navigation: `${CLAUDE_SKILL_DIR}/../../rules/hud-screens.md`
- Colors and ANSI palette: `${CLAUDE_SKILL_DIR}/../../rules/colors.md`
- Display system: `${CLAUDE_SKILL_DIR}/../../rules/display-system.md`
- SourceResult pattern: `${CLAUDE_SKILL_DIR}/../../rules/source-results.md`
- Model tiers: `${CLAUDE_SKILL_DIR}/../../rules/models.md`
- Error recovery: `${CLAUDE_SKILL_DIR}/../../rules/error-recovery.md`
- Testing patterns: `${CLAUDE_SKILL_DIR}/../../rules/testing.md`
- Retry + backoff: `${CLAUDE_SKILL_DIR}/../../rules/retry.md`
- Conventions: `${CLAUDE_SKILL_DIR}/../../rules/conventions.md`
