---
name: plan
description: Use this skill when the user wants to define what to build before writing any code — for a new CLI or an improvement to an existing one. Triggers on "plan a CLI", "help me think through this", "what should I build", "I want to redesign X", "map out what needs to change", or any request to think before acting. Can read existing explore findings if .cli/audit/EXPLORE.md exists. Outputs a .cli/plan/ folder with CONTEXT.md, DECISIONS.md, and PLAN.md.
argument-hint: "[project-name or path/to/existing-cli]"
model: sonnet
effort: medium
context: fork
allowed-tools: Read, Write, Glob, Grep, LS, Bash
---

# cli:plan — Define what to build

A focused planning session. Interview the user, recommend an architecture, confirm decisions, then write a `.cli/plan/` folder that any skill — or any future AI session — can pick up and execute.

Works in two modes:
- **New** — blank slate, full interview
- **Improve** — reads existing explore findings, asks only what's missing

## Context loaded at runtime

Directory: !`pwd`
Argument: `$ARGUMENTS`
Existing explore findings: !`[ -f "${ARGUMENTS:-.}/.cli/audit/EXPLORE.md" ] && echo "found" || echo "none"`
Existing plan: !`[ -f "${ARGUMENTS:-.}/.cli/plan/PLAN.md" ] && echo "found" || echo "none"`

---

## Step 0 — Detect mode

**If an existing PLAN.md is found:**
```
There's already a plan at .cli/plan/PLAN.md.

  A) Continue from the existing plan
  B) Re-plan from scratch (overwrites the existing plan)
  C) Add to the existing plan — new tasks only

Which would you like?
```

**If EXPLORE.md exists but no PLAN.md:** → improve mode, skip questions already answered by the findings.

**If neither exists:** → new mode, full interview.

---

## Step 1 — Goal and context (always asked)

One message, clear and direct:

```
What are we building?

Describe the goal in one or two sentences — what does this CLI do, who uses it,
and what does success look like when it's done?
```

Wait for the answer. Use it to shape every recommendation that follows.

---

## Step 2 — Planning interview

Ask these in groups of 2–3, not one by one. Skip any question already answered by EXPLORE.md findings.

**Interface (skip if EXPLORE.md has this):**
```
What does the main experience look like?

  A) Dashboard / HUD — persistent screen, arrow-key navigation, always-on output
     Good for: monitoring tools, dashboards, tools you run and leave open
  B) Wizard — step-by-step flow with progress indicator
     Good for: setup flows, generators, anything with a clear start → end
  C) Commands — run it, get output, done
     Good for: scriptable tools, CI, piping output
  D) Hybrid — HUD for the main loop, wizard for setup or complex actions

[Recommendation based on the goal they described]
```

**AI usage:**
```
Does this tool use Claude?

  A) Yes — fast responses (Haiku, low cost, high volume)
  B) Yes — smart reasoning (Sonnet, balanced)
  C) Yes — both tiers (fast for drafts, smart for final)
  D) Reads Claude output but doesn't call the API directly
  E) No AI

[Recommendation based on goal]
```

**Data sources (skip if none make sense for the goal):**
```
Where does the data come from?

List the APIs, files, or services this tool will read from.
(e.g., Reddit, Twitter, a local markdown folder, a REST API, competitor websites)

Or type "none" if it's self-contained.
```

**Output:**
```
What does the tool produce?

  A) Displays in the terminal — nothing written to disk
  B) Writes files — markdown, JSON, HTML, images
  C) Browser view — opens a page with the results
  D) Feeds into another tool — stdout or MCP

[Multiple ok]
```

**Distribution:**
```
How will this be used?

  A) Personal — runs on my machine, not shared
  B) Team — shared internally, cloned and run
  C) Global install — `bun install -g`, runs as a command anywhere
  D) MCP server — queryable from Claude Desktop or another agent

[Multiple ok]
```

---

## Step 3 — Architecture recommendation

Based on the answers, write a recommendation before proceeding. Keep it short — the key decision and why:

```
Here's what I'd build:

Interface:    [choice] — [one-line rationale]
AI:           [choice] — [one-line rationale]
Sources:      [list or "none"]
Output:       [choice]
Distribution: [choice]

Files this generates:
  src/cli.ts          entry point + router
  src/hud.ts          ANSI HUD screen loop        [if HUD or hybrid]
  cli/App.tsx         Ink wizard state machine     [if wizard or hybrid]
  src/models.ts       model tier config            [if AI]
  src/sources/        one file per data source     [if sources]
  src/server.ts       browser view                 [if browser output]
  src/mcp.ts          MCP server                   [if MCP]
  tests/cli.test.ts   bun:test suite

Does this look right? Any changes before I write the plan?
```

Wait for confirmation or adjustments. Apply any changes.

---

## Step 4 — Launch the architect

Run the `cli-architect` agent with:
- The confirmed goal
- The confirmed architecture decisions
- The EXPLORE.md findings (if improve mode)

The architect produces the detailed implementation blueprint.

---

## Step 5 — Write `.cli/plan/`

Create `.cli/plan/` in the project root. Write three files.

### `.cli/plan/CONTEXT.md`

```markdown
# [project-name] — Context

## Purpose
[What it does, who runs it, what triggers it, what it produces]

## Interface
[HUD | Wizard | Commands | Hybrid] — key file: [path]

## AI
[Tiers used, what Claude does — or "none"]

## Sources
[List or "none"]

## Output
[What gets written, where]

## Storage
.propane/ — runtime state (gitignored)
output/   — generated files (gitignored)

## Conventions
- Model IDs: src/models.ts only — never hardcoded
- Sources: return SourceResult, never throw
- Entry: bun hud
- Resize: process.stdout.on('resize', redraw) in any ANSI HUD

## Do not
- [specific anti-pattern for this project]
- [another constraint]
```

### `.cli/plan/DECISIONS.md`

```markdown
# Decisions — [project-name]
> Planned: [date]

## Interface: [choice]
[Why this interface fits the goal]

## AI: [choice]
[Why these tiers]

## Sources: [list]
[Why these, not alternatives]

## Distribution: [choice]
[Why]
```

### `.cli/plan/PLAN.md`

```markdown
# PLAN — [project-name]

> Status: 0 of [N] tasks complete
> Planned: [date]
> Goal: [user's stated goal]

## Build next

- [ ] **Init project** `chore` — create folder, write package.json, run bun install, git init
- [ ] **[task]** `feat` — [specific, one sentence]
- [ ] **[task]** `feat` — [specific]

## Later

- [ ] **[task]** `feat` — [specific]

## Ideas

- **[idea]** — [tradeoff, not a task yet]
```

---

## Step 6 — Confirm and hand off

```
Plan written → .cli/plan/

  CONTEXT.md   — what this is and how it works
  DECISIONS.md — why each architecture choice was made
  PLAN.md      — [N] tasks, ordered by dependency

First task: [task name]
Scope: [under a day | a few days | week+]

What's next?
  /cli:new [name]   — build it from scratch using this plan
  /cli:audit [path] — improve an existing project using this plan
```
