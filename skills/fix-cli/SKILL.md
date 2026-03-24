---
name: fix-cli
description: Use this skill to execute tasks from a PLAN.md one by one. Triggers on "execute the plan", "work through the plan", "fix the CLI", "implement task 1", or when the user wants to act on audit findings. Requires a PLAN.md to exist (run /audit-cli first if it doesn't).
argument-hint: "[path/to/cli-project]"
model: sonnet
effort: high
context: fork
allowed-tools: Read, Write, Edit, Glob, Grep, LS, Bash
---

# Fix CLI — Execute the Plan

Work through tasks in `PLAN.md` one at a time. Implement, verify, check off. Never skip verification. Never mark a task done without testing it.

## Context loaded at runtime

Project path from arguments: `$ARGUMENTS`

Current directory: !`pwd`

---

## Step 0 — Find the plan

If `$ARGUMENTS` contains a path, look for `PLAN.md` there. Otherwise check the current directory.

If no `PLAN.md` exists:
```
No PLAN.md found. Run /audit-cli [path] first to generate one, then come back here.
```

Read the full `PLAN.md` before doing anything else.

---

## Step 1 — Show the current state

After reading PLAN.md, display a summary:

```
PLAN.md found — [project name]
Audited: [date]
Progress: [X] of [N] tasks complete

Next up:
  ☐ [first unchecked task] — [description]

Coming after that:
  ☐ [second unchecked task]
  ☐ [third unchecked task]

Proceed with "[first task name]"? (yes / skip / pick different task)
```

Wait for confirmation before writing any code.

---

## Step 2 — Implement the task

For the confirmed task:

**If it's a code fix (bug, crash, bad pattern):**
1. Read the affected file(s) fully before editing
2. Make the minimal change that fixes the issue — don't refactor surrounding code
3. If fixing a source that throws: replace `throw` with `return sourceError(...)` and add the import
4. If fixing hardcoded model IDs: create/update `src/models.ts`, replace all occurrences, verify imports

**If it's a new file (missing configure.ts, models.ts, tests, etc.):**
1. Check if a reference exists in `${CLAUDE_SKILL_DIR}/../new-cli/examples/` — read it and adapt
2. Write the complete file — no placeholders or TODO comments
3. Verify imports from the new file are added wherever needed

**If it's a refactor (cli.ts too long, hud.ts needs splitting):**
1. Read the full file before splitting
2. Identify the split boundary — usually a complete screen function or command handler
3. Extract to the new file, update the import in the original
4. Confirm the entry point still calls the right function

**If it's a test:**
1. Read the existing test file if one exists
2. Follow the same mock/fixture pattern already in use
3. Write the test to cover the specific case mentioned in the plan — not a general suite

---

## Step 3 — Verify

After every implementation:

**Always run:**
```bash
cd [project-path] && bun --version && echo "bun ok"
```

**If code was changed:**
```bash
cd [project-path] && bun typecheck 2>&1 | head -20
```

**If tests exist or were added:**
```bash
cd [project-path] && bun test 2>&1 | tail -20
```

**If the main entry was touched:**
Ask the user: "Can you run `bun hud` and confirm it starts up?" — don't assume it works.

If any check fails, fix it before marking the task done.

---

## Step 4 — Check off the task

Edit `PLAN.md` in the project:
- Change `- [ ] **[task]**` to `- [x] **[task]**`
- Update the status line: `Status: [X+1] of [N] tasks complete`

Then show the user:

```
✓ Done: [task name]

Progress: [X] of [N] complete

Next task:
  ☐ [next unchecked task] — [description]

Continue? (yes / skip this one / stop for now)
```

---

## Step 5 — Continue or stop

**If user says yes:** loop back to Step 2 with the next unchecked task.

**If user says skip:** mark the task with `- [~]` (deferred) and move to the next.

**If user says stop:** summarize what was completed this session and remind them to run `/fix-cli [path]` to resume.

**If all tasks are complete:**
```
✓ All tasks complete.

[project-name] is ready. Here's what was done:
[bulleted list of completed tasks]

Consider running /audit-cli [path] again to check if anything new came up during implementation.
```

---

## Rules

- Read before writing. Always read the full file before editing any part of it.
- One task at a time. Never batch two tasks into one step.
- No scope creep. If you notice something outside the current task, add it to PLAN.md as a new item — don't fix it now.
- Ask before destructive changes. If a task requires deleting or renaming files, confirm first.
- Never mark done without verification. If the verify step can't run (no Bun, wrong directory), flag it and ask the user to confirm manually.
