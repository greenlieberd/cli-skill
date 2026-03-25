# Contributing to cli-skill

cli-skill is open source, sponsored by [Propane](https://usepropane.ai) and created by [Dennis Green-Lieber](https://github.com/greenlieberd).

---

## What you're contributing to

This is a Claude Code plugin — pure markdown and JSON, no runnable code (except hooks). It teaches Claude how to design and build CLI tools that feel like real software. HUDs that resize cleanly. Wizards with proper progress tracking. Output that doesn't look like a dump.

Contributing means improving the instructions Claude follows, not writing application code. A good contribution makes the next CLI Claude builds slightly better than the last one.

---

## What has the most impact

**The A-list rules** — these cover 90% of what gets built. If they're wrong, everything built from them is wrong.

`hud-screens` · `ascii-art` · `colors` · `source-results` · `models` · `display-system` · `error-recovery` · `testing`

Improvements here — better examples, caught edge cases, clearer guidance — have the highest leverage.

**The assets** — `skills/cli-new/assets/` are the reference implementations copied into every new project. Quality here equals quality in every generated CLI.

---

## Ways to contribute

### Add or improve a rule

Rules live in `rules/`. Each rule covers one subject (`caching.md`, `retry.md`).

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

Rules must use subject names (`caching.md`) — never `how-to-` prefixes or numbers. If a rule doesn't have working TypeScript, it's not done.

### Improve an agent

Agents live in `agents/`. They do the actual interview, analysis, and file-writing. If an agent produces consistently wrong output, improve its instructions.

Every agent needs correct frontmatter:

```markdown
---
name: agent-name
description: one-line description
allowed-tools: Read, Write, Glob, Grep, LS
model: sonnet
color: blue
---
```

Use `allowed-tools:` — not `tools:`. Use `/plugin-dev:agent-creator` when building a new one.

### Improve a skill

Skills live in `skills/`. They're thin orchestrators — load context, launch agents, show results. Skills must not contain interview logic (that belongs in agents).

Description field must be third-person: `"This skill should be used when..."` — not `"Use this skill when..."`. The description is how Claude decides whether to load the skill; second-person phrasing reduces reliability.

### Improve assets

Assets live in `skills/cli-new/assets/`. These get adapted into every new project. The patterns here — resize handling, theme import, model shape — directly affect the quality of every CLI this plugin builds.

### Report a bug

Open an issue. Include: which skill you ran, what you expected, what happened.

---

## Required tools — use these, not manual review

This plugin has plugin-dev skills specifically for validating and reviewing itself. **Use them. Don't submit a PR without running them.**

| When | Tool |
|------|------|
| After editing any SKILL.md | `/plugin-dev:skill-reviewer` |
| After any structural change | `/plugin-dev:plugin-validator` |
| Creating a new agent | `/plugin-dev:agent-creator` |

These catch issues invisible in a text editor — wrong field names, description antipatterns, missing frontmatter, orphaned files. They're the equivalent of running a type checker before committing.

---

## Standards

- No build step — edit markdown and JSON directly
- Rules must have frontmatter + Prerequisites block
- Skills must be thin wrappers — interview logic belongs in agents
- Assets must follow all A-list rules
- Descriptions must be third-person
- `allowed-tools:` not `tools:` in agent frontmatter
- No API keys, internal service URLs, or private data in any file

---

## Submitting changes

1. Fork the repo
2. Make your changes
3. Run `/plugin-dev:skill-reviewer` on any SKILL.md you touched
4. Run `/plugin-dev:plugin-validator` — must pass with zero critical issues
5. Test locally: `claude plugin marketplace add ./cli-skill && claude plugin install cli@cli`
6. Open a PR with a clear description of what changed and why
