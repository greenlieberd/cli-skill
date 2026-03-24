---
name: workspace-settings
description: Claude Code workspace configuration — .claude/ directory, skills, hooks, MCP settings, model settings files.
metadata:
  tags: claude-code, workspace, settings, skills, hooks, mcp
---

# Workspace Settings

> Platform: macOS — Claude Code reads workspace config from `.claude/` in the project root.

A CLI tool that works *with* Claude Code can expose context, register hooks, lock skills, and configure MCPs. This is what makes a tool feel like a first-class resident of your Claude workspace rather than something you run separately.

## Prerequisites

- Claude Code installed (`claude --version`)
- `.claude/` directory in project root (created when Claude Code first runs in the project)
- `CLAUDE.md` in project root (Claude Code reads this for every session)

---

## 1. CLAUDE.md — the primary context file

`CLAUDE.md` at project root is read by Claude Code at the start of every session. Write it for an AI agent, not a human:

```markdown
# CLAUDE.md

## What this tool does
[one paragraph: purpose, trigger, output]

## Entry point
`bun hud` — always

## Key files
- `src/cli.ts` — command router
- `src/hud.ts` — ANSI HUD
- `src/models.ts` — all model IDs live here
- `src/limits.ts` — tune fetch limits here

## Conventions
- Sources return SourceResult, never throw
- Model IDs: src/models.ts only
- No databases — flat files in .propane/

## Do not
- Add SQLite or Prisma
- Hardcode model strings outside models.ts
- Use console.log — all output via Display class
```

---

## 2. .claude/settings.json — workspace permissions and hooks

Claude Code reads `.claude/settings.json` for workspace-level settings:

```json
{
  "permissions": {
    "allow": [
      "Bash(bun:*)",
      "Bash(bun run*)",
      "Read(**)",
      "Write(src/**)",
      "Write(.propane/**)",
      "Write(output/**)"
    ]
  }
}
```

Keep permissions tight — only allow what the tool needs. This prevents Claude from touching unrelated files.

---

## 3. Hooks — run checks on every session

Hooks execute shell commands in response to Claude Code events. Define in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'hardcoded\\|sk-ant-\\|console\\.log'; then echo 'BLOCKED: use src/models.ts, logError(), and Display class'; exit 1; fi"
          }
        ]
      }
    ]
  }
}
```

---

## 4. .mcp.json — MCP servers available to Claude Code

If your CLI exposes an MCP server, register it so Claude Code can query it:

```json
{
  "mcpServers": {
    "my-tool": {
      "command": "bun",
      "args": ["run", "src/mcp.ts"],
      "env": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
      }
    }
  }
}
```

After adding `.mcp.json`, Claude Code can call your tool's MCP tools directly in conversation. See `mcp-servers.md` for building the server itself.

---

## 5. Skills lock — pin external skills

If your tool depends on specific Claude Code skills (SEO, ads, etc.), lock them:

```json
// .claude/skills-lock.json
{
  "skills": [
    {
      "name": "seo-geo",
      "source": "git+ssh://git@github.com:propane/cli-skill.git",
      "version": "2.0.0",
      "install": "claude plugin install git+ssh://git@github.com:propane/cli-skill.git"
    }
  ]
}
```

Document install commands so collaborators can replicate your skill setup:
```bash
# Install all locked skills
cat .claude/skills-lock.json | jq -r '.skills[].install' | bash
```

---

## 6. Model settings — route tasks to the right model tier

Document which model tier each task uses in `src/models.ts`. Claude Code reads this file as context:

```typescript
// src/models.ts
// ─── Model assignments — change here, nowhere else ──────────────────────────
export const MODELS = {
  // Fast + cheap: routing, extraction, classification
  fast:    'claude-haiku-4-5-20251001',
  // Capable: generation, analysis, synthesis
  smart:   'claude-sonnet-4-6',
  // Most capable: complex reasoning, long context
  power:   'claude-opus-4-6',
  // Current session: piped from Claude Code (no API key needed)
  piped:   null,
} as const

// ─── Task assignments ────────────────────────────────────────────────────────
// routing, tagging, quick extraction  → MODELS.fast
// content generation, analysis        → MODELS.smart
// complex multi-step reasoning        → MODELS.power
// scripts running inside Claude Code  → MODELS.piped (use process.stdin)
```

---

## Rules

- `CLAUDE.md` is for AI agents — write what an agent needs to navigate the codebase, not what a human wants to read
- `.claude/settings.json` permissions should be minimal — only allow what the tool actively uses
- Register your MCP server in `.mcp.json` if it should be queryable from Claude Code chat
- `skills-lock.json` documents install commands so the setup is reproducible
- Model tier assignments belong in `src/models.ts` — never in conversation or as inline strings
