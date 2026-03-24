---
name: error-recovery
description: Global crash handlers, structured error logging, terminal restoration, and actionable error messages.
metadata:
  tags: errors, crash, recovery, logging, terminal
---

# Error Recovery

> Platform: macOS (Terminal.app, iTerm2, Warp).

Crashes are inevitable. A CLI that recovers gracefully — logging context, printing actionable messages, and leaving the terminal in a clean state — feels like a professional tool. One that dumps a stack trace and freezes the cursor feels broken.

## Prerequisites

- `src/configure.ts` with `loadEnv()` in place (see `environment-setup.md`)
- `.propane/logs/` directory created at startup
- ANSI escape constants defined (see `hud-screens.md`)

---

## 1. Global crash handler — always install at entry

Before any async code runs, register an uncaught exception handler. This is the last line of defense.

```typescript
// src/cli.ts — install before anything else
process.on('uncaughtException', (err) => {
  restoreTerminal()               // must be sync — see §3
  logError('uncaughtException', err)
  process.stderr.write(`\n  ✗  Unexpected error: ${err.message}\n`)
  process.stderr.write(`  Snapshot saved to .propane/logs/errors.jsonl\n\n`)
  process.exit(1)
})

process.on('unhandledRejection', (reason) => {
  const err = reason instanceof Error ? reason : new Error(String(reason))
  restoreTerminal()
  logError('unhandledRejection', err)
  process.stderr.write(`\n  ✗  Unhandled promise rejection: ${err.message}\n`)
  process.exit(1)
})
```

---

## 2. Structured error log — JSONL snapshot

Append one JSON line per error to `.propane/logs/errors.jsonl`. Each entry is self-contained: timestamp, error type, message, stack, and active context.

```typescript
// src/logger.ts
import { appendFileSync, mkdirSync } from 'fs'
import { join } from 'path'

const LOG_DIR  = join(import.meta.dir, '..', '.propane', 'logs')
const ERR_FILE = join(LOG_DIR, 'errors.jsonl')

export function logError(type: string, err: Error, context?: Record<string, unknown>): void {
  mkdirSync(LOG_DIR, { recursive: true })
  const entry = {
    ts:      new Date().toISOString(),
    type,
    message: err.message,
    stack:   err.stack?.split('\n').slice(0, 6),   // first 6 frames only
    context: context ?? {},
    version: process.env.npm_package_version ?? 'unknown',
  }
  appendFileSync(ERR_FILE, JSON.stringify(entry) + '\n')
}
```

Keep the stack short — six frames is enough to locate the error. Long stacks scroll the terminal and obscure the message.

---

## 3. Terminal restore — required for raw mode

ANSI HUDs call `process.stdin.setRawMode(true)`. If they crash without restoring, the terminal is left in a broken state where typed characters don't echo. Always restore synchronously before exit.

```typescript
// src/hud.ts
let rawModeActive = false

export function enterRawMode(): void {
  if (process.stdin.isTTY) {
    process.stdin.setRawMode(true)
    rawModeActive = true
  }
}

export function restoreTerminal(): void {
  if (rawModeActive && process.stdin.isTTY) {
    process.stdin.setRawMode(false)
    rawModeActive = false
  }
  process.stdout.write('\x1b[?25h')   // show cursor
  process.stdout.write('\x1b[0m')     // reset colors
  // do NOT clear screen — leave output visible for debugging
}
```

Register `restoreTerminal` in the crash handler (§1) AND in the clean exit path:

```typescript
process.on('SIGINT',  () => { restoreTerminal(); process.exit(0) })
process.on('SIGTERM', () => { restoreTerminal(); process.exit(0) })
```

---

## 4. Source errors — return, never throw

Sources should never crash the process. They return a `SourceResult` with `error` set:

```typescript
import type { SourceResult } from './sources/types.ts'

export async function fetchReddit(query: string): Promise<SourceResult> {
  try {
    const data = await callRedditAPI(query)
    return { source: 'reddit', label: 'Reddit', content: data }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    logError('source:reddit', err instanceof Error ? err : new Error(message))
    return { source: 'reddit', label: 'Reddit', content: '', error: message }
  }
}
```

The HUD displays the error inline, then continues with other sources. The process never crashes.

---

## 5. User-facing error messages — actionable, not technical

```typescript
// Map error codes to human messages
const ERROR_MESSAGES: Record<string, string> = {
  ENOENT:         'File not found',
  ECONNREFUSED:   'Could not connect — is the server running?',
  ETIMEDOUT:      'Request timed out — check your network',
  ENOTFOUND:      'DNS lookup failed — check your network',
  'fetch failed':  'Network request failed — check your .env keys',
}

export function humanError(err: Error): string {
  for (const [code, msg] of Object.entries(ERROR_MESSAGES)) {
    if (err.message.includes(code)) return msg
  }
  return err.message   // fall back to raw message if not recognized
}
```

Display pattern in the HUD:
```
  ✗  Reddit      Could not connect — is the server running?
  ✓  Perplexity  12 results
```

---

## 6. Debug mode — full stack on demand

Add a `DEBUG=1` flag that prints full stack traces without changing normal behavior:

```typescript
export function debugLog(label: string, data: unknown): void {
  if (!process.env.DEBUG) return
  process.stderr.write(`\n  [debug] ${label}\n`)
  process.stderr.write(JSON.stringify(data, null, 2) + '\n')
}
```

Users run `DEBUG=1 bun hud` to see full output. Document this in the help screen.

---

## UX checklist

- [ ] `uncaughtException` + `unhandledRejection` handlers installed at entry
- [ ] `restoreTerminal()` called on crash AND on SIGINT/SIGTERM
- [ ] All sources return `SourceResult`, never throw
- [ ] Errors written to `.propane/logs/errors.jsonl`
- [ ] User-facing messages are actionable (no raw stack traces)
- [ ] `DEBUG=1` flag available for full output
