---
name: audit-cli
description: Use this skill when the user wants to review, improve, or plan work on an existing CLI project. Triggers on "audit this CLI", "review my CLI", "what needs fixing", "plan work on this tool", "give me a roadmap for X", or when the user passes a path to an existing Bun/Node CLI project. Produces a prioritized PLAN.md the user can then execute with /fix-cli.
argument-hint: "[path/to/cli-project]"
model: sonnet
effort: high
context: fork
allowed-tools: Read, Write, Glob, Grep, LS, Bash
---

# CLI Audit — Improvement Plan

Analyze an existing CLI project and produce a `PLAN.md` with specific, prioritized tasks the user can execute. This is not a generic code review — every finding must map to a concrete action item.

## Context loaded at runtime

Project path from arguments: `$ARGUMENTS`

Current directory: !`pwd`

Conventions reference (folder structure standard):
!`cat "${CLAUDE_SKILL_DIR}/../../guides/folder-structure.md" 2>/dev/null | head -60`

---

## Step 0 — Confirm path and goal

If `$ARGUMENTS` contains a path, use it. Otherwise ask:

```
Which CLI project should I audit?
(paste the path, or press enter to use the current directory)
```

Then immediately ask — one message:

```
What's your goal for this audit? Choose one:

1. Find bugs — correctness, crashes, error handling
2. Improve UX — navigation, output clarity, terminal experience
3. Add features — what new capabilities would be most valuable
4. Prep for release — production readiness, docs, tests, .env
5. Full review — everything

Or describe it in your own words.
```

---

## Step 2 — Explore the project

Launch the `cli-explorer` agent on the confirmed project path. Pass this exact instruction:

> Analyze the CLI at [path]. Report: entry points, command structure, UI layer (HUD vs Wizard vs script), model usage and whether IDs are hardcoded, data sources and whether they return SourceResult or throw, test coverage, storage patterns (.propane/, output/, .cache/), and any patterns that would be painful to change. List the 5 most important files to read before adding any code.

Wait for the full explorer report before continuing.

---

## Step 3 — Convention check

Using the explorer report and the folder structure guide loaded above, check these against the actual code:

**Will break or block future work:**
- Hardcoded model ID strings anywhere outside `src/models.ts`
- Sources that `throw` instead of returning `SourceResult`
- `cli.ts` doing business logic (should be router only, under 80 lines)
- No `loadEnv()` call before first env var access
- Hardcoded file paths that break on other machines

**Slows you down:**
- No `CLAUDE.md` or `CLAUDE.md` that doesn't match the actual architecture
- No `.env.example` documenting required keys
- No tests, or tests that only mock (never hit real endpoints)
- `hud.ts` over 300 lines without splitting into screen functions
- Direct `process.env` access outside of `configure.ts`

**Worth doing before the next release:**
- No `PLAN.md`
- No ASCII art header (HUD style)
- No MCP server — would this output be useful in Claude Desktop?
- Browser view would make output more readable but doesn't exist

---

## Step 4 — Write PLAN.md

Write to `<project-path>/PLAN.md`. Use this exact format — the `/fix-cli` skill reads it:

```markdown
# PLAN — [project name]

> Audit goal: [user's stated goal]
> Audited: [today's date]
> Status: 0 of [N] tasks complete

## Summary

[2–3 sentences: what's working well, the biggest gap, and the most valuable next step]

## Critical — fix before adding anything new

- [ ] **[short task name]** — [one sentence: what to do and why it unblocks other work]
- [ ] ...

## Improvements — high value, not blocking

- [ ] **[short task name]** — [what to do]
- [ ] ...

## Ideas — worth discussing before committing

- **[idea]** — [tradeoff in one sentence]
- ...

## Build order

Work through tasks in this sequence — each one unblocks the next:

1. [task name] — [why first]
2. [task name] — [why second]
3. ...
```

Confirm the full path with the user before writing.

---

## Step 5 — Quality check the plan

Launch `cli-reviewer` with argument `completeness` to verify:
- Does every finding from the explorer report appear as a task?
- Are tasks specific enough to act on immediately? (not "improve tests" but "add test for fetchReddit error case")
- Is the build order logical — does each task actually unblock the next?

Apply any corrections, then present the final summary.

---

## Output

Tell the user:
1. Path to `PLAN.md`
2. The single most important task to start with and why
3. Rough scope: "under a day" / "a few days" / "significant refactor"
4. How to execute: "Run `/fix-cli [path]` to start working through the plan"
