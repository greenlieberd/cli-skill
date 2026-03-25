---
name: cli-learn
description: This skill should be used to distill session history into project memory. Triggers on "learn from sessions", "what have we learned", "compress session logs", "summarize what's happened", "what keeps going wrong", or after a few sessions when you want future work on this project to be smarter. Reads .cli/sessions/, builds .cli/learnings/ — watch-out, patterns, decisions, errors. Never touches the cli-skill framework.
argument-hint: "[path/to/cli-project]"
model: sonnet
effort: medium
context: fork
allowed-tools: Read, Write, Glob, Grep, LS, Bash
---

# cli:learn — Turn session history into project memory

Reads what's happened in past sessions, extracts what's worth remembering, and writes it into `.cli/learnings/`. Future sessions load this at start — less re-discovering, less repeating mistakes, more context on how this project actually works.

The framework stays unchanged. This is memory for the project, not feedback for the plugin.

## Context loaded at runtime

Directory: !`pwd`
Target: `$ARGUMENTS`
Sessions found: !`ls "${ARGUMENTS:-.}/.cli/sessions/"*.jsonl 2>/dev/null | grep -v errors_buffer | wc -l | tr -d ' '`
Last learned: !`[ -f "${ARGUMENTS:-.}/.cli/learnings/SUMMARY.md" ] && grep "^updated:" "${ARGUMENTS:-.}/.cli/learnings/SUMMARY.md" | head -1 || echo "never"`

---

## Step 0 — Confirm

If `$ARGUMENTS` is a path, use it. Otherwise use current directory.

Check sessions exist:
```bash
ls .cli/sessions/*.jsonl 2>/dev/null | grep -v errors_buffer
```

If none found:
```
No session logs at .cli/sessions/ yet.

Sessions log automatically when any cli:* skill runs.
Come back after a few sessions — the more history, the more useful this gets.
```

If sessions exist:
```
[N] sessions found — [date range]
Last learning run: [date or "never"]

Building project memory from session history.
This stays in .cli/learnings/ — the framework is not touched.
```

---

## Step 1 — Run the learner

Launch `cli-learner` agent with:
- `PROJECT_PATH` — confirmed project path
- `SINCE` — date of last SUMMARY.md update, or all-time
- `FOCUS` — `all`

Wait for `LEARNER_COMPLETE`.

---

## Step 2 — Show what was learned

Read the new `.cli/learnings/SUMMARY.md` and present it to the user:

```
Memory updated — [N] sessions analyzed

Added to .cli/learnings/:

  watch-out.md   — [N] things to know before touching this project
  patterns.md    — [N] established patterns to follow
  decisions.md   — [N] choices already made
  errors.md      — [N] known errors with fixes

Top findings:
  ⚠  [most important watch-out]
  ✓  [most useful established pattern]
  —  [key decision that's been settled]

These load automatically at the start of future sessions on this project.
```

---

## Step 3 — Archive old sessions

```bash
mkdir -p .cli/sessions/archive
ls -t .cli/sessions/*.jsonl 2>/dev/null | grep -v errors_buffer | tail -n +6 | xargs -I{} mv {} .cli/sessions/archive/ 2>/dev/null || true
```

Tell the user:
```
Archived [N] older session logs → .cli/sessions/archive/
[N] recent sessions kept active for next run.

Commit when ready:
  git add .cli/learnings/ && git commit -m "learn: update project memory"
```

---

## Notes

- Run again after every 5–10 sessions — learnings compound.
- The learner merges with existing `.cli/learnings/` — it doesn't overwrite prior runs.
- Archived sessions are kept, never deleted.
- To see what future sessions will load, read `.cli/learnings/SUMMARY.md`.
