# Guide 05 — MCP Patterns

Add an MCP server when your CLI produces output that an agent should be able to query — reports, battlecards, content drafts, run history. The MCP server is a thin read layer over the flat files that already exist.

## When to add MCP

Add `src/mcp.ts` if any of these are true:
- The CLI generates reports or structured output that's useful in Claude Desktop chats
- The team needs to query the output without running the CLI
- You want Claude to trigger CLI actions (run, generate, refresh) from a chat

Skip MCP if:
- The CLI is a pure wizard (one-shot, no persistent output)
- Output is always consumed immediately by another process

## Standard MCP server

```typescript
// src/mcp.ts
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { z } from 'zod'
import { readdirSync, readFileSync, existsSync } from 'fs'
import { join } from 'path'

const OUTPUT_DIR = join(import.meta.dir, '..', 'output')
const server = new McpServer({ name: 'CLI_NAME', version: '1.0.0' })

// ── Tool: list available output files ──────────────────────────────────
server.tool(
  'list_outputs',
  'List all generated output files',
  {},
  async () => {
    if (!existsSync(OUTPUT_DIR)) return { content: [{ type: 'text', text: '[]' }] }
    const files = readdirSync(OUTPUT_DIR)
      .filter(f => f.endsWith('.md') || f.endsWith('.html'))
      .sort()
      .reverse()
    return { content: [{ type: 'text', text: JSON.stringify(files) }] }
  }
)

// ── Tool: get a specific output file ──────────────────────────────────
server.tool(
  'get_output',
  'Read a specific output file by filename',
  { filename: z.string().describe('Filename from list_outputs') },
  async ({ filename }) => {
    // Sanitize: only allow filenames, no path traversal
    const safe = filename.replace(/[^a-zA-Z0-9._-]/g, '')
    const file = join(OUTPUT_DIR, safe)
    if (!existsSync(file)) return { content: [{ type: 'text', text: 'File not found' }] }
    const content = readFileSync(file, 'utf8')
    return { content: [{ type: 'text', text: content }] }
  }
)

// ── Tool: get the most recent output ──────────────────────────────────
server.tool(
  'get_latest',
  'Get the most recently generated output',
  {},
  async () => {
    if (!existsSync(OUTPUT_DIR)) return { content: [{ type: 'text', text: 'No output yet' }] }
    const files = readdirSync(OUTPUT_DIR)
      .filter(f => f.endsWith('.md'))
      .sort()
    if (!files.length) return { content: [{ type: 'text', text: 'No output yet' }] }
    const content = readFileSync(join(OUTPUT_DIR, files[files.length - 1]), 'utf8')
    return { content: [{ type: 'text', text: content }] }
  }
)

const transport = new StdioServerTransport()
await server.connect(transport)
```

## Path safety rule

Always sanitize filenames before using them in file paths. Never pass user-supplied strings directly to `join()`:

```typescript
// Safe: strip anything that isn't a valid filename character
const safe = filename.replace(/[^a-zA-Z0-9._-]/g, '')
const file = join(OUTPUT_DIR, safe)

// Never do this:
// const file = join(OUTPUT_DIR, filename)  // path traversal risk
```

## Registering with Claude Desktop

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "CLI_NAME": {
      "command": "bun",
      "args": ["/absolute/path/to/CLI_NAME/src/mcp.ts"]
    }
  }
}
```

Use the absolute path. Bun resolves `import.meta.dir` relative to the source file, not the working directory.

Document this in the project's `manifest.json` (see Guide 01) so anyone cloning the repo knows what to add.

## manifest.json MCP section

```json
{
  "mcp": {
    "entry": "src/mcp.ts",
    "tools": [
      { "name": "list_outputs", "description": "List all generated files" },
      { "name": "get_output",   "description": "Read a file by name",   "args": ["filename"] },
      { "name": "get_latest",   "description": "Get most recent output" }
    ],
    "registration": {
      "command": "bun",
      "args_template": ["/absolute/path/to/src/mcp.ts"]
    }
  }
}
```

## Adding action tools (CLI triggers from Claude)

If Claude should be able to trigger a CLI run (not just read output), add an action tool. Use a simple flag file as the trigger — the CLI polls for it:

```typescript
// In mcp.ts — trigger a run
server.tool(
  'trigger_run',
  'Trigger a new CLI run',
  { topic: z.string().optional() },
  async ({ topic }) => {
    const triggerFile = join(OUTPUT_DIR, '..', '.propane', 'trigger.json')
    writeFileSync(triggerFile, JSON.stringify({ topic, ts: Date.now() }))
    return { content: [{ type: 'text', text: 'Run triggered. Check output in a few minutes.' }] }
  }
)

// In cli.ts — poll for trigger
async function watchForTrigger() {
  const triggerFile = join('.propane', 'trigger.json')
  if (existsSync(triggerFile)) {
    const { topic } = JSON.parse(readFileSync(triggerFile, 'utf8'))
    unlinkSync(triggerFile)
    await cmdRun({ topic })
  }
}
```

## MCP + browser bridge

When both MCP and a browser view exist, they read the same files:

```
CLI writes output/report.md
  └─ browser: fs.watch() → SSE → renders in UI
  └─ MCP: get_latest() → reads the same file → returns to Claude Desktop
```

No synchronization needed. The file is the single source of truth.
