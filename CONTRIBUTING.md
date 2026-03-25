# Contributing to cli-skill

cli-skill is free and open source, sponsored by [Propane](https://usepropane.ai) and created by [Dennis Green-Lieber](https://github.com/greenlieberd).

---

## What this project is

A Claude Code plugin — pure markdown and JSON, no runnable code (except hooks). It teaches Claude how to plan, scaffold, audit, and build production-quality CLI tools using Bun, Ink, and ANSI patterns.

Contributing means improving the instructions Claude follows, not writing application code.

---

## Ways to contribute

### Add or improve a rule
Rules live in `rules/`. Each rule covers one subject (e.g. `caching.md`, `retry.md`).

Every rule must have:
```markdown
---
name: subject-name
description: one-line description of what this rule covers
metadata:
  tags: [tag1, tag2]
---

# Subject Name

## Prerequisites
- what needs to exist before applying this rule

[content — concrete TypeScript examples, not abstract advice]
```

Rules must use subject names (`caching.md`), never `how-to-` prefixes or numbers.

### Improve an agent
Agents live in `agents/`. They're the workhorses — they do the actual interview, analysis, and file-writing work. If an agent produces consistently wrong output, improve its instructions.

### Improve a skill
Skills live in `skills/`. They're thin orchestrators — they load context, launch agents, and show results. Skills should not contain interview logic (that belongs in agents).

### Improve assets
Assets live in `skills/cli-new/assets/`. These are reference implementations that get copied into every new project. Quality here = quality in every generated CLI.

### Report a bug
Open an issue. Include: what skill you ran, what you expected, what happened.

---

## Standards

- No build step — edit markdown and JSON directly
- Rules must have frontmatter + Prerequisites block
- Skills must be thin wrappers — interview logic belongs in agents
- Assets must follow all A-list rules (hud-screens, ascii-art, colors, source-results, models, display-system, error-recovery, testing)
- No API keys, internal service URLs, or private data in any file

## A-list rules (core — these must be excellent)

`hud-screens` · `ascii-art` · `colors` · `source-results` · `models` · `display-system` · `error-recovery` · `testing`

These eight rules cover 90% of what gets built. Improvements here have the most impact.

---

## Required tools when working on this plugin

Use the plugin-dev skills that ship with Claude Code. **Do not edit plugin files by hand and submit without running these.**

### After editing a skill
```
/plugin-dev:skill-reviewer
```
Checks description phrasing, trigger coverage, content quality, and progressive disclosure. Run on every SKILL.md you touch.

### After any structural change
```
/plugin-dev:plugin-validator
```
Validates plugin.json, marketplace.json, all skill frontmatter, all agent frontmatter, hooks.json, and rules structure. Run before every PR.

### When creating a new agent
```
/plugin-dev:agent-creator
```
Generates correct frontmatter and structure. Don't write agent files from scratch.

These tools catch issues (wrong field names, missing required fields, description antipatterns) that are invisible in a text editor. They're the equivalent of running `bun typecheck` before committing.

---

## Submitting changes

1. Fork the repo
2. Make your changes
3. Run `/plugin-dev:skill-reviewer` on any SKILL.md you touched
4. Run `/plugin-dev:plugin-validator` — must pass with zero critical issues
5. Test by installing locally: `claude plugin install ./cli-skill`
6. Open a PR with a clear description of what changed and why

---

## Code of conduct

Be direct. Be specific. Prefer concrete examples over abstract advice. If a rule doesn't have working TypeScript, it's not done.
