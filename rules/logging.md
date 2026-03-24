---
name: logging
description: Structured JSONL usage logs, error logs, log rotation, and displaying usage stats in the config screen.
metadata:
  tags: logging, jsonl, usage, events, rotation
---

# Logging

> Platform: macOS (Terminal.app, iTerm2, Warp).

Logging has two jobs: help you debug when something goes wrong, and give you usage data when everything goes right. Keep them separate. Errors go to `errors.jsonl`. Usage events go to `usage.jsonl`. Neither blocks the UI.

## Prerequisites

- `.propane/logs/` directory (created at startup, gitignored)
- `src/logger.ts` module (created in this guide)
- `error-recovery.md` — `logError()` is defined there; this guide extends it with usage logging

---

## 1. Log directory setup — create at startup

```typescript
// src/cli.ts — call before any logging
import { mkdirSync } from 'fs'
import { join } from 'path'

const LOG_DIR = join(import.meta.dir, '..', '.propane', 'logs')
mkdirSync(LOG_DIR, { recursive: true })
```

Add to `.gitignore`:
```
.propane/
```

---

## 2. Usage log — what users do

Track commands run, sources fetched, and AI calls made. One line per event.

```typescript
// src/logger.ts
import { appendFileSync } from 'fs'
import { join } from 'path'

const LOG_DIR    = join(import.meta.dir, '..', '.propane', 'logs')
const USAGE_FILE = join(LOG_DIR, 'usage.jsonl')

export type UsageEvent =
  | { type: 'run';    command: string }
  | { type: 'source'; name: string; durationMs: number; ok: boolean }
  | { type: 'ai';     model: string; inputTokens: number; outputTokens: number; taskId?: string }
  | { type: 'export'; format: string; path: string }

export function logUsage(event: UsageEvent): void {
  const entry = { ts: new Date().toISOString(), ...event }
  appendFileSync(USAGE_FILE, JSON.stringify(entry) + '\n')
}
```

Call sites:
```typescript
// On command run
logUsage({ type: 'run', command: 'generate' })

// After a source fetch
const start = Date.now()
const result = await fetchReddit(query)
logUsage({ type: 'source', name: 'reddit', durationMs: Date.now() - start, ok: !result.error })

// After an AI call (use token counts from response)
logUsage({ type: 'ai', model: MODELS.smart, inputTokens: usage.input_tokens, outputTokens: usage.output_tokens })
```

---

## 3. Error log — structured crash snapshots

Defined in `error-recovery.md`. Reproduced here for cross-reference:

```typescript
// src/logger.ts (continued)
const ERR_FILE = join(LOG_DIR, 'errors.jsonl')

export function logError(type: string, err: Error, context?: Record<string, unknown>): void {
  const entry = {
    ts:      new Date().toISOString(),
    type,
    message: err.message,
    stack:   err.stack?.split('\n').slice(0, 6),
    context: context ?? {},
  }
  appendFileSync(ERR_FILE, JSON.stringify(entry) + '\n')
}
```

---

## 4. Log rotation — prevent runaway files

Rotate when the log exceeds 1 MB. Run at startup, not during a run.

```typescript
// src/logger.ts
import { statSync, renameSync, unlinkSync } from 'fs'

const MAX_BYTES = 1_000_000   // 1 MB

export function rotateLogs(): void {
  for (const file of [USAGE_FILE, ERR_FILE]) {
    try {
      const { size } = statSync(file)
      if (size > MAX_BYTES) {
        const rotated = file.replace('.jsonl', `.${Date.now()}.jsonl`)
        renameSync(file, rotated)
        // Keep only last 2 rotated files
        pruneOldLogs(file)
      }
    } catch { /* file doesn't exist yet */ }
  }
}

function pruneOldLogs(basePath: string): void {
  const dir  = basePath.split('/').slice(0, -1).join('/')
  const stem = basePath.split('/').at(-1)!.replace('.jsonl', '')
  const old  = readdirSync(dir)
    .filter(f => f.startsWith(stem) && f.includes('.') && f !== `${stem}.jsonl`)
    .sort()
    .slice(0, -2)   // keep last 2
  old.forEach(f => unlinkSync(join(dir, f)))
}
```

---

## 5. Log summary — show in config screen

Let users see their own usage data in the HUD's config/keys screen:

```typescript
// In HUD config screen
import { readFileSync } from 'fs'

function readLogSummary(): { runs: number; errors: number; aiCalls: number } {
  let runs = 0, errors = 0, aiCalls = 0
  try {
    const lines = readFileSync(USAGE_FILE, 'utf8').trim().split('\n').filter(Boolean)
    for (const line of lines) {
      const e = JSON.parse(line)
      if (e.type === 'run')    runs++
      if (e.type === 'ai')     aiCalls++
    }
    const errLines = readFileSync(ERR_FILE, 'utf8').trim().split('\n').filter(Boolean)
    errors = errLines.length
  } catch { /* logs may not exist yet */ }
  return { runs, errors, aiCalls }
}

const { runs, errors, aiCalls } = readLogSummary()
process.stdout.write(`  Runs this session      ${runs}\n`)
process.stdout.write(`  AI calls               ${aiCalls}\n`)
process.stdout.write(`  Errors logged          ${errors > 0 ? `\x1b[31m${errors}\x1b[0m` : '0'}\n`)
```

---

## 6. What NOT to log

- API keys or any value from `.env`
- Full HTTP response bodies — log only metadata (status, duration, item count)
- User content (prompts, generated text) — log only that a call happened
- Stack traces longer than 6 frames in production

---

## Rules

- One `appendFileSync` per event — never buffer logs in memory
- Log files stay in `.propane/logs/` — never in `output/` or root
- Rotation check runs at startup, not mid-run
- Usage log and error log are separate files — different retention, different consumers
