---
name: fix-cli
description: Use this skill to execute tasks from .cli/PLAN.md one by one. Triggers on "execute the plan", "work through the plan", "fix the CLI", "implement task 1", or when the user wants to act on audit findings. Requires .cli/PLAN.md to exist (run /audit-cli first if it doesn't).
argument-hint: "[path/to/cli-project]"
model: sonnet
effort: high
context: fork
allowed-tools: Read, Write, Edit, Glob, Grep, LS, Bash
---

# Fix CLI — Execute the Plan

Work through tasks in `.cli/PLAN.md` one at a time. Implement, verify, commit, check off. Never batch tasks. Never mark done without verification. Never push to remote.

## Context loaded at runtime

Project path: `$ARGUMENTS`
Current directory: !`pwd`

---

## Step 0 — Find the plan

Look for `.cli/PLAN.md` at the path from `$ARGUMENTS`, or the current directory.

If missing:
```
No .cli/PLAN.md found at [path].
Run /audit-cli [path] to generate one, then come back.
```

Read the full `.cli/PLAN.md` and `.cli/CONTEXT.md` before doing anything.

---

## Step 1 — Show progress and confirm next task

```
[project-name] — [X] of [N] tasks complete

Ready to work on:
  ☐ [first unchecked task from "Build next"] — [description]

After that:
  ☐ [second task]
  ☐ [third task]

Proceed? (yes / skip this one / pick a different task / stop)
```

---

## Step 2 — Implement

Determine the task type from its label (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`) and apply the right approach:

**`fix` — correcting broken behavior:**
Read the affected files fully before editing. Make the minimal change. Don't refactor surrounding code.
- Hardcoded model ID → update `src/models.ts`, grep for all occurrences, replace with `MODELS.fast.id` / `MODELS.smart.id`
- Source throws → replace `throw` with `return sourceError(source, label, err)`, add import
- `cli.ts` too long → extract business logic to a new module, leave router lean

**`feat` — new file or capability:**
Check `.cli/CONTEXT.md` to understand architecture. Check `${CLAUDE_SKILL_DIR}/assets/` for reference patterns. Write the complete file — no stubs.

**`refactor` — restructuring without behavior change:**
Read the full file before splitting. Extract to a new file at a clean boundary. Update all imports. Confirm the entry point still calls the right function.

**`test` — adding or fixing tests:**
Read existing test files first. Follow the same mock/fixture pattern already in use. Test the specific case from the task — not a general suite.

**`docs` — CLAUDE.md, README, comments:**
Read `.cli/CONTEXT.md` and `.cli/DECISIONS.md` first. Keep CLAUDE.md under 80 lines. Accurate > comprehensive.

**`chore` — config, gitignore, manifest:**
Make the minimal change. No scope creep.

---

## Step 3 — Verify

After every implementation — always run in order:

1. Type check (if TypeScript was touched):
```bash
cd [project-path] && bun typecheck 2>&1 | head -30
```

2. Tests (if tests exist or were added):
```bash
bun test 2>&1 | tail -20
```

3. Entry point (if src/cli.ts, src/hud.ts, or cli/App.tsx was touched):
Ask the user: "Can you run `bun hud` and confirm it starts?" — don't assume it works.

If any check fails, fix it before marking the task done.

---

## Step 4 — Commit and check off

Pick the commit prefix from the task label:

| Label | Prefix | Example |
|-------|--------|---------|
| `feat` | `feat:` | `feat: add Reddit source` |
| `fix` | `fix:` | `fix: move model IDs to models.ts` |
| `refactor` | `refactor:` | `refactor: split hud.ts into screen functions` |
| `test` | `test:` | `test: add configure loadEnv test` |
| `docs` | `docs:` | `docs: update CLAUDE.md architecture section` |
| `chore` | `chore:` | `chore: add output/ to .gitignore` |

```bash
cd [project-path] && git add -A && git commit -m "[prefix]: [task name]"
```

Then edit `.cli/PLAN.md`:
- Change `- [ ] **[task]**` → `- [x] **[task]**`
- Update the status line: `Status: [X+1] of [N] tasks complete`

Do not push to remote. The user decides when to push.

---

## Step 5 — Continue or stop

Show the user:

```
✓ Done: [task name]

Progress: [X] of [N] complete

Next:
  ☐ [next unchecked task] — [description]

Continue? (yes / skip / stop for now)
```

**skip** → mark task as `- [~] **[task]**` (deferred) and move to the next.
**stop** → "Resume with `/fix-cli [path]` when you're ready to continue."

**All tasks complete:**
```
✓ All [N] tasks complete — [project-name] is ready.

Completed:
[bulleted list of done tasks]

Run /audit-cli [path] again to check if anything new surfaced during implementation.
```

---

## Rules

- **Read before writing.** Always read the full file before editing.
- **One task at a time.** Never batch.
- **No scope creep.** Notice something else? Add it to `## Later` in PLAN.md, don't fix it now.
- **Confirm before destructive changes.** Deleting or renaming files requires user confirmation.
- **Ideas section is not tasks.** Skip the `## Ideas` section — those are discussions, not work items.
- **Never push.** `git push` only happens when the user explicitly requests it.
