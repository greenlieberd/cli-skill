# cli-skill — Context

## Purpose
A distributable Claude Code plugin that teaches Claude how to design and build production-quality CLI tools. Pure markdown and JSON — no runnable application code. Users invoke skills (`/cli:cli-new`, `/cli:cli-audit`, etc.) which run planning interviews, scaffold projects, and improve existing CLIs.

## What this is NOT
- Not a CLI tool itself (doesn't run with `bun hud`)
- Not an application — it's a plugin that extends Claude Code
- Not a code generator in isolation — it's a system that keeps learning

## Architecture
```
.claude-plugin/     — plugin registration and marketplace entry
skills/             — 5 thin skill orchestrators (SKILL.md per skill)
agents/             — 5 agents that do the actual work
rules/              — 42 subject-named rules (loaded on-demand, not all at once)
hooks/              — 3 Python scripts: convention check, error capture, session logger
tests/              — test bed: unit tests for hooks, fixtures, report generator
```

## Model tier strategy
- **haiku** — read-only work: cli-explorer, cli-learner, cli-explore skill
- **sonnet** — decision/planning: cli-planner, cli-architect, cli-reviewer, all other skills
- **opus** — not used in plugin agents (reserved for user CLIs when write quality matters most)

## Key conventions
- Skills are thin wrappers — no interview logic, just context load + agent launch + show results
- Agents do the actual work (interview, analysis, writing)
- Rules are loaded on-demand based on PLAN_COMPLETE fields — never all at once
- Assets in skills/cli-new/assets/ are the reference implementations for every new project
- `.cli/` folder travels with each generated project (plan, audit, learnings — committed; sessions — gitignored)

## Do not
- Add interview logic to skills (belongs in agents)
- Load rules speculatively — only load based on confirmed plan fields
- Use `tools:` in agent frontmatter (must be `allowed-tools:`)
- Write skill descriptions in second person ("Use this skill when..." → "This skill should be used when...")
