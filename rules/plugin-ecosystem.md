---
name: plugin-ecosystem
description: External Claude Code plugins worth composing with — what they do and when to use them.
metadata:
  tags: plugins, ecosystem, claude-code, integrations
---

# Plugin Ecosystem

The Claude Code plugin ecosystem has 8,000+ indexed repos. This guide covers what's worth installing, how to evaluate any plugin, and how to compose external skills into your own workflows.

## The Anthropic official directory first

Before looking at community plugins, check the official directory:
```
https://github.com/anthropics/claude-plugins-official
```

These are maintained by Anthropic, updated with each Claude Code release, and safe to install wholesale. The ones relevant to CLI and product work:

| Plugin | Command | What it does |
|--------|---------|--------------|
| `feature-dev` | `/feature-dev` | 7-phase workflow: discovery → exploration → clarification → architecture → implementation → review → iteration |
| `commit-commands` | `/commit`, `/commit-push-pr` | One-liner git commits and PRs |
| `hookify` | `/hookify` | Create enforcement hooks from natural language |
| `skill-creator` | `/skill-creator` | Author, improve, and evaluate skills |
| `pr-review-toolkit` | auto | 6 specialized review agents: comment accuracy, test coverage, error handling, type design, quality, simplification |
| `claude-code-setup` | `/claude-code-setup` | Analyzes any codebase and recommends hooks, subagents, and MCP servers |
| `playground` | `/playground` | Generates interactive HTML explorer files |
| `frontend-design` | `/frontend-design` | Production-grade UI implementation |

## High-value community plugins

These have been vetted from the awesome-claude-plugins index. Curated for a founder/PM + CLI builder context.

### PM workflows
**`phuryn/pm-skills`** — https://github.com/phuryn/pm-skills
65 PM skills, 8 plugins, 36 chained workflows. Teresa Torres Opportunity Solution Trees built in.
Key commands: `/discover`, `/strategy`, `/write-prd`, `/plan-launch`, `/north-star`
Install: add `phuryn/pm-skills` to your Claude Code plugin list.

**`deanpeters/Product-Manager-Skills`** — https://github.com/deanpeters/Product-Manager-Skills
46 skills, 6 commands. Amazon working backwards, MITRE frameworks. More structured than phuryn.
Best for: deep PRD and roadmap work.

### Research synthesis
**`mvanhorn/last30days-skill`** — https://github.com/mvanhorn/last30days-skill
One skill, one command. Synthesizes Reddit, X, Bluesky, YouTube, TikTok, HN, Polymarket for any topic. Returns cited 30-day synthesis.
Overlap with `pulse/`: pulse is a scheduled daily digest; last30days is a one-shot research query. Both are worth having.

### Design / UI
**`pbakaus/impeccable`** — https://github.com/pbakaus/impeccable
20 design commands that extend frontend-design.
Most useful: `/audit` (full design review), `/critique` (specific callouts), `/polish` (final pass), `/animate` (motion suggestions), `/bolder` / `/quieter` (tone adjustments).

**`Dammyjay93/interface-design`** — https://github.com/Dammyjay93/interface-design
Design memory: saves decisions to `system.md`, loads on each session. `/interface-design status` shows what's been decided. Best for multi-session UI projects.

### Marketing / content
**`coreyhaines31/marketingskills`** — https://github.com/coreyhaines31/marketingskills
33 skills: SEO, CRO, copywriting, email, paid ads, content strategy, analytics, referral, churn. Directly maps to byline and content pipeline work.

### Planning
**`OthmanAdi/planning-with-files`** — https://github.com/OthmanAdi/planning-with-files
Manus-style persistent markdown planning. Plans live in files, updated by the agent. More durable than task lists.

### Memory
**`thedotmack/claude-mem`** — https://github.com/thedotmack/claude-mem
Cross-session memory with AI compression. Captures, compresses, and injects context from previous sessions.
Consider if you're losing context between long multi-session builds.

### Visual output
**`nicobailon/visual-explainer`** — https://github.com/nicobailon/visual-explainer
Generates HTML pages for diagrams, diff reviews, plan audits, data tables. Useful for client-facing outputs from CLI tools.

---

## How to evaluate any plugin before installing

1. **Read the README** — does it say what it does in the first 3 lines? If not, skip.
2. **Check `plugin.json`** — does it list skills with clear descriptions and trigger phrases?
3. **Look at the skills/** directory — are they markdown files? Are they focused or sprawling?
4. **Star count is a weak signal** — the awesome-claude-plugins index ranks by composite score, not human curation. A 500-star focused skill pack beats a 10k-star repo that just happens to have a plugin.json.
5. **Check for hooks** — plugins with PreToolUse/PostToolUse hooks change Claude's default behavior globally. Read them before installing.

## How to compose external skills into your own workflows

You don't have to use external skills as-is. Three ways to compose:

### 1. Reference in your skill
Mention an external plugin as a dependency in your skill's steps:
```markdown
## Step 2 — Research
Run /last30days for the target topic before generating any content.
This gives 30 days of synthesized signal across Reddit, X, YouTube, and HN.
```

### 2. Wrap with context
Create a skill in `cc/skills/` that calls an external skill with Propane-specific context pre-loaded:
```markdown
# Content Research
Run last30days research pre-loaded with Propane's positioning and competitive landscape.
1. Load propane-context.md as background
2. Run /last30days for [topic]
3. Filter for Claude Code and AI coding assistant angles
4. Return a brief with signal + Propane-specific takeaways
```

### 3. Chain into a pipeline
Build a skill that sequences multiple external skills:
```markdown
# Launch Content Pipeline
1. /write-prd → get feature spec
2. /last30days [feature category] → get market signal
3. /content-brief [feature] + [signal] → generate brief
4. /commit-push-pr → ship the brief to the repo
```

---

## What NOT to install

- **LSP plugins** (clangd, gopls, rust-analyzer, etc.) — you're Bun/TypeScript, not C++/Go/Rust
- **Security deep-dives** (trailofbits, cybersecurity skills) — not your domain
- **Mobile** (SwiftUI agent, Firebase APK scanner)
- **Everything at once** — don't add `wshobson/agents` (72 plugins) or `sickn33/antigravity-awesome-skills` (1,304 skills). They bloat context and most are irrelevant. Install by need, not by FOMO.

## Staying current

The official directory releases alongside Claude Code. Check for new entries when you update Claude Code.
The awesome-claude-plugins index: https://github.com/quemsah/awesome-claude-plugins
It's machine-generated and updated daily — use it for discovery, not quality assurance.
