# Guide 07 — Claude Code-Quality Patterns

This guide covers the patterns that separate a production-quality CLI (like Claude Code itself) from a basic script. These are the things you can't learn from tutorials — they come from studying how Claude Code is actually built.

---

## Image and file input (clipboard paste)

Claude Code accepts images via clipboard paste. Any Bun CLI can implement the same:

### Keyboard shortcut to paste image

In a Bun readline-based CLI, intercept the paste event and check if clipboard contains an image:

```typescript
// src/lib/clipboard.ts
import { execFileSync } from 'child_process'

export function readClipboardText(): string | null {
  try {
    return execFileSync('pbpaste', [], { encoding: 'utf8' }).trim()
  } catch { return null }
}

export function readClipboardImagePath(): string | null {
  // Check if clipboard has an image file path (drag-from-finder)
  const text = readClipboardText()
  if (text && (text.endsWith('.png') || text.endsWith('.jpg') || text.endsWith('.jpeg') || text.endsWith('.gif') || text.endsWith('.webp'))) {
    return text
  }
  return null
}

export async function saveClipboardImageToTemp(): Promise<string | null> {
  // Save clipboard image to temp file using osascript
  try {
    const outPath = `/tmp/cli-paste-${Date.now()}.png`
    execFileSync('osascript', [
      '-e',
      `set png_data to the clipboard as «class PNGf»
       set out_file to open for access POSIX file "${outPath}" with write permission
       write png_data to out_file
       close access out_file`
    ])
    return outPath
  } catch { return null }
}
```

In an Ink component, handle `Ctrl+V`:
```tsx
useInput((input, key) => {
  if (key.ctrl && input === 'v') {
    const imgPath = await saveClipboardImageToTemp()
    if (imgPath) {
      setAttachment({ type: 'image', path: imgPath })
    } else {
      const text = readClipboardText()
      if (text) setInputValue(v => v + text)
    }
  }
})
```

### Sending an image to Claude API

```typescript
import { readFileSync } from 'fs'

const imageData = readFileSync(imgPath)
const base64 = imageData.toString('base64')

const response = await anthropic.messages.create({
  model: MODELS.smart.id,
  max_tokens: MODELS.smart.maxTokens,
  messages: [{
    role: 'user',
    content: [
      {
        type: 'image',
        source: { type: 'base64', media_type: 'image/png', data: base64 }
      },
      { type: 'text', text: userMessage }
    ]
  }]
})
```

### @filename mention autocomplete

When users type `@` in the input, show a file picker:
```typescript
// In input handler — when '@' is typed, open file picker
if (input === '@') {
  const files = await glob('**/*', { cwd: process.cwd(), nodir: true, ignore: ['node_modules/**', '.git/**'] })
  // Show SelectList with files, on select: insert path into input
}
```

---

## Status bar (HUD outside the conversation)

Claude Code's status bar is a shell script that receives JSON on stdin and prints to stdout. Any CLI can expose the same mechanism:

### Implementation in your CLI

1. Output a JSON status line to a known file after each significant operation:
```typescript
// src/lib/status.ts
import { writeFileSync, mkdirSync } from 'fs'
import { join } from 'path'

const STATUS_FILE = join(process.cwd(), '.propane', 'status.json')

export function updateStatus(data: Record<string, unknown>) {
  mkdirSync(join(process.cwd(), '.propane'), { recursive: true })
  writeFileSync(STATUS_FILE, JSON.stringify({
    ts: Date.now(),
    cwd: process.cwd(),
    ...data
  }))
}
```

2. Provide a `statusline.sh` in your project that reads this file:
```bash
#!/bin/bash
# statusline.sh — put in project root
STATUS_FILE=".propane/status.json"
if [ -f "$STATUS_FILE" ]; then
  node -e "
    const s = JSON.parse(require('fs').readFileSync('$STATUS_FILE', 'utf8'));
    const age = Math.round((Date.now() - s.ts) / 1000);
    console.log('\x1b[33m' + (s.tool || 'idle') + '\x1b[0m  \x1b[2m' + age + 's ago\x1b[0m');
    if (s.model) console.log('\x1b[2m' + s.model + '\x1b[0m');
  "
fi
```

3. Register it in `.claude/settings.json` for projects using this CLI:
```json
{
  "statusLine": {
    "type": "command",
    "command": "${cwd}/statusline.sh"
  }
}
```

### Status line for a Claude Code plugin

If your CLI is a Claude Code plugin, add a status line to `settings.json`:
```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ${CLAUDE_PLUGIN_ROOT}/statusline.sh",
    "padding": 2
  }
}
```

The JSON piped to your script has these fields available:
```
model.id, model.display_name, cwd, cost.total_cost_usd,
context_window.used_percentage, context_window.context_window_size,
session_id, agent.name, version
```

---

## Streaming output with live terminal updates

The async generator core (Guide 03) + live terminal updates:

```typescript
// In hud.ts or cli.ts — live terminal streaming
import { broadcastEvent } from './server.ts'

// Start a "live region" — a line that updates in place
function liveStart(): (text: string) => void {
  process.stdout.write('\n')  // reserve the line
  return function update(text: string) {
    process.stdout.write(`\r\x1b[K\x1b[33m${FRAMES[frame++ % FRAMES.length]}\x1b[0m ${text}`)
  }
}

function liveDone(text: string) {
  process.stdout.write(`\r\x1b[K\x1b[32m✓\x1b[0m ${text}\n`)
}

// Use it in a run loop
const update = liveStart()
for await (const event of run(config)) {
  if (event.type === 'progress') update(event.label)
  if (event.type === 'result')   { liveDone(event.label ?? 'Done'); break }
  if (event.type === 'error')    { process.stdout.write(`\r\x1b[K\x1b[31m✗\x1b[0m ${event.message}\n`); break }
  broadcastEvent(event)  // also push to browser
}
```

### Streaming Claude API responses to terminal

```typescript
// Stream Claude response token-by-token to terminal
const stream = anthropic.messages.stream({
  model: MODELS.smart.id,
  max_tokens: MODELS.smart.maxTokens,
  messages: [{ role: 'user', content: prompt }]
})

process.stdout.write('\n')  // new line before streaming
for await (const event of stream) {
  if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
    process.stdout.write(event.delta.text)
  }
}
process.stdout.write('\n\n')
const final = await stream.finalMessage()
```

---

## Multi-agent pattern (feature-dev quality)

The pattern from Claude Code's `feature-dev` plugin — 3-phase parallel agents:

```
Phase 1: EXPLORE (parallel)
  ├─ cli-explorer A: entry points + command structure
  ├─ cli-explorer B: data sources + storage patterns
  └─ cli-explorer C: tests + coverage gaps
       ↓ (wait for all 3, consolidate key files list)
       ↓ (read all key files directly)

Phase 2: ARCHITECT (parallel)
  ├─ cli-architect "minimal": fewest files, fastest to ship
  └─ cli-architect "modular": clean separation, extensible
       ↓ (present options to user, WAIT for choice)

Phase 3: IMPLEMENT
  ↓ (write all files in order, per chosen architecture)

Phase 4: REVIEW (parallel)
  ├─ cli-reviewer "correctness": broken imports, crashes
  ├─ cli-reviewer "completeness": missing pieces
  └─ cli-reviewer "conventions": Propane patterns
       ↓ (apply all fixes)
       ↓ (present to user with ship checklist)
```

**Critical rule from feature-dev**: Do NOT start implementing without explicit user approval of the architecture. Present options, wait for choice.

**Critical rule**: After all agents return, **read the key files they identified directly** before writing any new code. Agents return lists of files to read — they don't replace reading the files yourself.

---

## Chat-in-CLI (Claude Code-style conversation)

To build a CLI that accepts a chat prompt and streams a Claude response — the core loop:

```typescript
// src/chat.ts
import Anthropic from '@anthropic-ai/sdk'
import { createInterface } from 'readline'
import { loadEnv } from './configure.ts'

loadEnv()
const anthropic = new Anthropic()
const messages: Array<{ role: 'user' | 'assistant'; content: string }> = []

const rl = createInterface({ input: process.stdin, output: process.stdout })

function prompt(q: string): Promise<string> {
  return new Promise(resolve => rl.question(q, resolve))
}

process.stdout.write('\x1b[?25l')  // hide cursor
process.on('SIGINT', () => { process.stdout.write('\x1b[?25h'); process.exit(0) })

while (true) {
  const input = await prompt('\x1b[33m▶\x1b[0m ')
  if (!input.trim() || input === 'q' || input === 'exit') break

  messages.push({ role: 'user', content: input })

  // Stream response
  process.stdout.write('\x1b[2m')  // dim for streaming
  const stream = anthropic.messages.stream({
    model: 'claude-sonnet-4-6',
    max_tokens: 4096,
    messages
  })

  let response = ''
  for await (const event of stream) {
    if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
      process.stdout.write(event.delta.text)
      response += event.delta.text
    }
  }
  process.stdout.write('\x1b[0m\n\n')  // reset + spacing

  messages.push({ role: 'assistant', content: response })
}

process.stdout.write('\x1b[?25h')
rl.close()
```

### Conversation with system prompt + tools

```typescript
// System prompt from a file (brand voice, context)
const system = existsSync('voice.md') ? readFileSync('voice.md', 'utf8') : ''

const response = await anthropic.messages.create({
  model: MODELS.smart.id,
  max_tokens: MODELS.smart.maxTokens,
  system: [{ type: 'text', text: system, cache_control: { type: 'ephemeral' } }],
  messages,
  tools: [
    {
      name: 'read_file',
      description: 'Read a local file',
      input_schema: {
        type: 'object' as const,
        properties: { path: { type: 'string', description: 'File path' } },
        required: ['path']
      }
    }
  ]
})
```

---

## Hooks for CLI enforcement

Add `hooks/hooks.json` to enforce conventions during development:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/check_conventions.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

```python
# hooks/check_conventions.py — warns when writing files that violate CLI patterns
import json, sys

data = json.load(sys.stdin)
tool = data.get('tool_name', '')
inp  = data.get('tool_input', {})

warnings = []

# Check: no hardcoded model IDs in source files
file_path = inp.get('file_path', '') or inp.get('new_file', '')
new_content = inp.get('new_string', '') or inp.get('content', '')

if file_path.endswith('.ts') and file_path != 'src/models.ts':
    for model_id in ['claude-sonnet', 'claude-haiku', 'claude-opus']:
        if model_id in new_content:
            warnings.append(f'Hardcoded model ID in {file_path}. Use MODELS from src/models.ts instead.')

# Check: no database imports
for db_pkg in ['better-sqlite3', 'sqlite', 'pg', 'mysql', 'mongoose', 'prisma', 'drizzle']:
    if db_pkg in new_content:
        warnings.append(f'Database package {db_pkg} detected. Use flat files instead — see Guide 04.')

if warnings:
    msg = '\n'.join(f'⚠️  {w}' for w in warnings)
    print(json.dumps({'continue': True, 'systemMessage': msg}))
else:
    print(json.dumps({'continue': True}))
```

---

## Distribution checklist

A CLI built with this skill pack is distribution-ready when:

- [ ] `manifest.json` is complete with all commands, env vars, and outputs declared
- [ ] `README.md` has: one-line description, install steps (`bun install`), run command (`bun hud`), all env vars listed
- [ ] `.env.example` exists with all required keys and descriptions
- [ ] `CLAUDE.md` is present and accurate (future Claude sessions can orient without reading all source)
- [ ] `hooks/` contains at least the convention-check hook
- [ ] `statusline.sh` is present for Claude Code status bar integration
- [ ] `bun test` passes with at least 3 meaningful tests
- [ ] The CLI works without a browser open (browser is always optional)
- [ ] The CLI gracefully handles missing API keys (skip or prompt — never crash)
- [ ] Image/clipboard paste works if the CLI uses AI with visual input
