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

A focused planning session. Interview the user, confirm every decision in a table before writing anything, then produce a `.cli/plan/` folder any skill or future session can execute from.

Works in two modes:
- **New** — blank slate, full interview
- **Improve** — reads existing explore findings, asks only what's missing

## Context loaded at runtime

Directory: !`pwd`
Argument: `$ARGUMENTS`
Existing explore findings: !`[ -f "${ARGUMENTS:-.}/.cli/audit/EXPLORE.md" ] && echo "found" || echo "none"`
Existing plan: !`[ -f "${ARGUMENTS:-.}/.cli/plan/PLAN.md" ] && echo "found" || echo "none"`
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

**EXPLORE.md exists, no PLAN.md** → improve mode, skip questions the code already answers.

**Neither exists** → new mode, full interview.

---

## Step 1 — Goal and v0.1

One message. Two questions:

```
What are we building?

1. What does this CLI do, who uses it, what does it produce?

2. What's the smallest version you'd run tomorrow and say "yes, this is it"?
   Not the full vision — just the core thing.
```

After the answer, reflect back the v0.1 scope explicitly:

```
Here's what I'm treating as v0.1:
  • [core thing 1]
  • [core thing 2 if any]

Everything else goes in v0.2+. We can always append — but we ship something
working first. Does this scope feel right?
```

If the scope is too broad, push back:
```
That's a lot for v0.1. Which 2–3 things prove the core idea works?
The rest will be in the plan as v0.2+ — nothing gets lost.
```

Lock the v0.1 scope before continuing. Use it to filter everything that follows.

---

## Step 2 — Interview

Ask in two rounds. Use tables to present options — easier to scan than prose.

**Round 1 — Interface and AI:**

```
Two questions:

Interface — what does the main experience look like?

  | Option   | What it is                                    | Good for                              |
  |----------|-----------------------------------------------|---------------------------------------|
  | HUD      | Persistent screen, arrow-key nav, always-on   | Monitoring, dashboards, run and leave |
  | Wizard   | Step-by-step with progress dots               | Setup flows, generators               |
  | Commands | Run it, get output, done                      | Scriptable, CI, piped output          |
  | Hybrid   | HUD main loop + wizard for setup              | Tools that do both                    |

AI — does this tool use Claude?

  | Option | Model        | Cost    | Good for                      |
  |--------|--------------|---------|-------------------------------|
  | Fast   | Haiku        | Low     | High-volume, quick responses  |
  | Smart  | Sonnet       | Medium  | Reasoning, quality output     |
  | Both   | Haiku+Sonnet | Varies  | Fast drafts, smart finals     |
  | None   | —            | Free    | No AI needed                  |

[Your recommendation with one-line rationale for each]
```

**Round 2 — Data, output, APIs, distribution:**

```
Three more:

APIs and data sources — where does the data come from?
List them (e.g. Reddit, a REST API, local markdown files) or say "none".

Output — what does this tool produce?

  | Option   | What it means                          |
  |----------|----------------------------------------|
  | Terminal | Displays only — nothing written        |
  | Files    | Writes markdown, JSON, HTML to output/ |
  | Browser  | Opens a page via Bun.serve             |
  | MCP      | Queryable from Claude Desktop / agents |

  Multiple ok.

Distribution — how will this be used?

  | Option  | What it means                          |
  |---------|----------------------------------------|
  | Personal | Runs on your machine, not shared      |
  | Team    | Cloned and run by the team             |
  | Global  | bun install -g, runs as a command      |
  | MCP server | Exposed as an MCP server           |

  Multiple ok. MCP server = adds src/mcp.ts.
```

---

## Step 3 — Confirm decisions in a table

Before touching any files, show everything back as a single confirmation table:

```
Here's the full plan. Confirm before I write anything.

  Project
  ┌─────────────────┬──────────────────────────────────────────────────┐
  │ Name            │ [project-name]                                   │
  │ v0.1 scope      │ [1-line summary]                                 │
  └─────────────────┴──────────────────────────────────────────────────┘

  Architecture
  ┌─────────────────┬──────────────────────────────────────────────────┐
  │ Interface       │ [HUD / Wizard / Commands / Hybrid]               │
  │ AI              │ [None / Fast / Smart / Both] — [model names]     │
  │ APIs            │ [list or "none"]                                 │
  │ Output          │ [Terminal / Files / Browser / MCP]               │
  │ Distribution    │ [Personal / Team / Global / MCP server]         │
  └─────────────────┴──────────────────────────────────────────────────┘

  What gets generated
  ┌─────────────────────────────┬────────────┬────────────────────────┐
  │ File                        │ Version    │ Why                    │
  ├─────────────────────────────┼────────────┼────────────────────────┤
  │ src/cli.ts                  │ v0.1       │ entry point + router   │
  │ src/hud.ts + ASCII art      │ v0.1       │ HUD + logo             │
  │ src/models.ts               │ v0.1       │ [tiers]                │
  │ src/configure.ts            │ v0.1       │ env loading            │
  │ src/sources/[name].ts       │ v0.1       │ [each API]             │
  │ tests/cli.test.ts           │ v0.1       │ required               │
  │ src/server.ts + ui/         │ v0.2+      │ browser view           │
  │ src/mcp.ts                  │ v0.2+      │ MCP server             │
  └─────────────────────────────┴────────────┴────────────────────────┘

  [Show only rows relevant to this project. Mark each as v0.1 or v0.2+.]

Confirm? (yes / change [item])
```

Wait for confirmation. Apply any changes and re-show the table if anything material changed.

---

## Step 4 — Launch the architect

Run the `cli-architect` agent with:
- The confirmed goal and v0.1 scope
- The confirmed architecture table
- EXPLORE.md findings (if improve mode)

The architect produces the detailed implementation blueprint.

---

## Step 5 — Write `.cli/plan/`

Create `.cli/plan/`. Write three files.

### `.cli/plan/CONTEXT.md`

```markdown
# [project-name] — Context

## Purpose
[What it does, who runs it, what triggers it, what it produces]

## v0.1 scope
[The exact thing that ships first — 1–3 bullets]

## Interface
[HUD | Wizard | Commands | Hybrid] — key file: [path]

## AI
[Tiers used, what Claude does — or "none"]

## APIs and sources
[List each: name, what it fetches, SourceResult or not]

## Output
[What gets written, where, in what format]

## Storage
.propane/ — runtime state (gitignored)
output/   — generated files (gitignored)

## Conventions
- Model IDs: src/models.ts only — never hardcoded
- Sources: return SourceResult, never throw
- Entry: bun hud
- Resize: process.stdout.on('resize', redraw) in any ANSI HUD
- ASCII art logo on every HUD home screen

## Do not
- [specific anti-pattern for this project]
- [another constraint from decisions]
```

### `.cli/plan/DECISIONS.md`

```markdown
# Decisions — [project-name]
> Planned: [date]

## Interface: [choice]
[Why this fits the goal. What was considered and rejected.]

## AI: [choice]
[Which tiers, what each does in this tool. Why not the alternative.]

## APIs: [list]
[Why these sources. Authentication approach. Rate limit considerations.]

## Output: [choice]
[Why files vs terminal vs browser. Format rationale.]

## Distribution: [choice]
[Personal / team / global / MCP. Install story.]

## MCP server: [yes for v0.1 | deferred to v0.2+]
[Why now or why later.]
```

### `.cli/plan/PLAN.md`

```markdown
# PLAN — [project-name]

> Status: 0 of [N] tasks complete
> Planned: [date]
> Goal: [user's stated goal]
> v0.1 scope: [1-line summary]

## v0.1 — ship this

Ordered by dependency. Each task is specific enough to start immediately.

- [ ] **Init project** `chore` — create folder, package.json, bun install, git init
- [ ] **ASCII art + HUD shell** `feat` — src/hud.ts with logo, menu, resize handler, ctrl+c
- [ ] **Configure + env** `feat` — src/configure.ts, .env.example, all required keys
- [ ] **[core feature]** `feat` — [specific, one sentence]
- [ ] **[API source]** `feat` — src/sources/[name].ts returning SourceResult, never throws
- [ ] **Tests** `test` — tests/cli.test.ts: configure, models, [source] happy path + error path
- [ ] **Verify** `chore` — bun hud starts, bun test passes, ctrl+c restores cursor

## v0.2+ — append after v0.1 ships

Use /cli:audit to add these one at a time.

- [ ] **[feature]** `feat` — [specific]
- [ ] **[feature]** `feat` — [specific]
- [ ] **MCP server** `feat` — src/mcp.ts [if deferred]

## Ideas

Not tasks yet.

- **[idea]** — [tradeoff]
```

---

## Step 6 — Hand off

```
Plan written → .cli/plan/

  CONTEXT.md   — [project-name]: what it is, v0.1 scope, conventions
  DECISIONS.md — interface, AI, APIs, output, distribution — and why
  PLAN.md      — [N] v0.1 tasks + [M] v0.2+ features parked for later

v0.1 is [N] tasks — scope: [under a day | a few days].
Ship v0.1 first. Use /cli:audit to append from the v0.2+ list.

  /cli:new [name]   — build v0.1 now
  /cli:audit [path] — improve an existing project using this plan
```
