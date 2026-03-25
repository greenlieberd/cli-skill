---
name: cli-plan
description: This skill should be used when the user wants to define what to build before writing any code, for either a new CLI or an improvement to an existing one. Triggers on "plan a CLI", "let's spec this out first", "I want to redesign X", "map out what needs to change", "before we write any code", or any request to think through architecture and scope before acting. Outputs CONTEXT.md, DECISIONS.md, and PLAN.md in .cli/plan/.
argument-hint: "[project-name or path/to/existing-cli]"
model: sonnet
effort: medium
context: fork
allowed-tools: Read, Write, Glob, Grep, LS, Bash
---

# cli:plan — Define what to build

A focused planning session. Loads existing context, then hands off to the `cli-planner` agent for the full interview. Never asks questions the code already answers.

## Context loaded at runtime

Directory: !`pwd`
Argument: `$ARGUMENTS`
Existing plan: !`[ -f "${ARGUMENTS:-.}/.cli/plan/PLAN.md" ] && echo "found" || echo "none"`
Existing explore findings: !`[ -f "${ARGUMENTS:-.}/.cli/audit/EXPLORE.md" ] && echo "found" || echo "none"`
Project memory: !`cat "${ARGUMENTS:-.}/.cli/learnings/SUMMARY.md" 2>/dev/null || echo "none"`

---

## Step 0 — Detect mode

**Existing PLAN.md found:**
```
There's already a plan at .cli/plan/PLAN.md.

  A) Continue from the existing plan
  B) Re-plan from scratch
  C) Add new tasks only

Which would you like?
```

**EXPLORE.md exists, no PLAN.md** → tell cli-planner to skip questions the code already answers.

**Neither exists** → full interview mode.

---

## Step 1 — Launch cli-planner

Run the `cli-planner` agent. Pass:
- The mode (new / improve / continue)
- Any EXPLORE.md findings (if improve mode)
- `$ARGUMENTS` (project name or path)
- Current directory

The planner runs the interview — goal, v0.1 scope, interface, AI, sources, output, distribution, theme — and writes:
- `.cli/plan/CONTEXT.md`
- `.cli/plan/DECISIONS.md`
- `.cli/plan/PLAN.md`

**Wait for `PLAN_COMPLETE` before continuing.**

---

## Step 2 — Confirm and hand off

Once the planner returns `PLAN_COMPLETE`, show:

```
Plan written → .cli/plan/

  CONTEXT.md   — [project-name]: what it is, v0.1 scope, conventions
  DECISIONS.md — interface, AI, APIs, output, distribution — and why
  PLAN.md      — [N] v0.1 tasks + [M] v0.2+ features parked for later

v0.1 is [N] tasks.
Ship v0.1 first. Use /cli:audit to append from the v0.2+ list.

  /cli:new [name]   — build v0.1 now
  /cli:audit [path] — improve an existing project using this plan
```
