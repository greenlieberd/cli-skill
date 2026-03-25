---
name: explore
description: Use this skill when the user wants to understand an existing CLI — what it does, how it's built, what's good, what's broken. Triggers on "explore this CLI", "what does this tool do", "explain this project", "map this codebase", "what's wrong with my CLI", or any request to understand before changing anything. Read-only — no files are modified. Works great before cli:audit or cli:plan.
argument-hint: "[path/to/cli-project]"
model: sonnet
effort: medium
context: fork
allowed-tools: Read, Glob, Grep, LS, Bash
---

# cli:explore — Understand what's here

Read-only analysis of an existing CLI. No changes, no plans — just a clear picture of what exists, how it's built, and what to watch out for. Writes findings to `.cli/audit/EXPLORE.md` so future skills can pick up where this leaves off.

## Context loaded at runtime

Directory: !`pwd`
Target path: `$ARGUMENTS`
Files at target: !`ls "${ARGUMENTS:-.}" 2>/dev/null | head -20 || ls . | head -20`
Project memory: !`cat "${ARGUMENTS:-.}/.cli/learnings/SUMMARY.md" 2>/dev/null || echo "none"`

---

## Step 0 — Confirm the project

If `$ARGUMENTS` is a valid path, use it. Otherwise:

```
Which CLI project should I explore?

You can paste a path, or press enter to use the current directory.
```

Confirm what you found before diving in:
```
Exploring: [resolved path]
I'll map the architecture, find patterns, and flag anything worth knowing before you make changes.
This is read-only — nothing will be modified.
```

---

## Step 1 — Launch the explorer

Run the `cli-explorer` agent on the confirmed path with this brief:

> Map the CLI at [path]. Cover:
> 1. How to run it — entry point, bun scripts, what `bun hud` / `bun run start` does
> 2. Interface type — ANSI HUD, Ink Wizard, plain commands, or hybrid
> 3. AI usage — model IDs location, what Claude does, which tiers are used
> 4. Data sources — what APIs or files feed it, do they return SourceResult or throw?
> 5. Output — what gets written, where, in what format
> 6. Storage — what's in .propane/ and output/
> 7. Tests — coverage, gaps, mock patterns used
> 8. Convention gaps — hardcoded model IDs, missing models.ts, sources that throw, no resize handler, missing CLAUDE.md
> 9. The 5 files a new developer should read first, in order

Wait for the full explorer report.

---

## Step 2 — Score against conventions

Using the explorer findings, run a fast check. Output a table the user can scan in 10 seconds:

```
Convention check — [project-name]

  ✓  models.ts exists — model IDs centralized
  ✗  2 sources throw instead of returning SourceResult
  ✓  loadEnv() called before first process.env access
  ✗  hud.ts has no resize handler — will corrupt on terminal resize
  ✓  .env.example present
  ✗  No CLAUDE.md — future AI sessions will have no context
  —  MCP server (not applicable — no AI output in this tool)
  ✓  Tests present — 14 cases

3 issues found. 2 will cause problems, 1 is a quick add.
```

---

## Step 3 — Write `.cli/audit/EXPLORE.md`

Create `.cli/audit/` in the project root if it doesn't exist. Write the full findings.

```markdown
# Explore — [project-name]
> Explored: [date]
> Path: [absolute path]

## How to run
[entry command, bun scripts, what each does]

## Interface
[ANSI HUD | Ink Wizard | Commands | Hybrid]
Key file: [path]
Pattern: [brief description of how it works]

## AI
[models used, what for, tier setup — or "none"]

## Sources
[list each source: name, what it fetches, does it return SourceResult?]

## Output
[what gets written, where, format]

## Storage
.propane/ — [what's here]
output/   — [what's here]

## Tests
[test runner, coverage areas, notable gaps]

## Convention check
| Item | Status | Notes |
|------|--------|-------|
| models.ts | ✓/✗ | |
| SourceResult | ✓/✗ | [which sources throw] |
| loadEnv() first | ✓/✗ | |
| resize handler | ✓/✗ | |
| .env.example | ✓/✗ | |
| CLAUDE.md | ✓/✗ | |
| Tests | ✓/✗ | |

## Read these first
1. [path] — [why]
2. [path] — [why]
3. [path] — [why]
4. [path] — [why]
5. [path] — [why]

## Watch out for
- [specific thing that will bite you if you don't know it]
- [another gotcha]
```

---

## Step 4 — Tell the user what you found

Keep it short. Lead with the most important thing:

```
[project-name] explored — here's the short version:

Interface:  [type] — [key file]
AI:         [usage or "none"]
Sources:    [count] ([working] ok, [broken] need fixing)
Tests:      [coverage summary]

Issues found: [N]
  ✗ [most important issue]
  ✗ [second issue]
  ✗ [third if any]

Full findings → .cli/audit/EXPLORE.md

What's next?
  /cli:audit [path]  — fix the issues above, with commits
  /cli:plan [path]   — plan new features or a bigger change
```

No recommendations unless asked. Just facts.
