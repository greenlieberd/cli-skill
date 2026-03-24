---
name: conventions
description: Non-negotiable conventions for all Propane CLI projects — models, sources, storage, entry point.
metadata:
  tags: conventions, standards, rules, models, sources
---

# Conventions

> **Platform:** macOS only. These tools use `process.stdout` raw mode, SIGWINCH, and terminal escape sequences — all tested on macOS Terminal and iTerm2. Windows/Linux support is out of scope for now.

These are non-negotiable rules. Every generated CLI must follow them. The `check_conventions.py` hook warns when they're violated.

---

## Model IDs

```typescript
// ✓ Correct — only in src/models.ts
export const MODELS = {
  fast:  { id: 'claude-haiku-4-5-20251001', maxTokens: 2048 },
  smart: { id: 'claude-sonnet-4-6',         maxTokens: 8000 },
} as const

// ✗ Wrong — hardcoded anywhere else
model: 'claude-sonnet-4-6'   // in any other file
```

Rule: `src/models.ts` is the only place model ID strings appear. All other files import from it.

---

## Sources never throw

```typescript
// ✓ Correct
export async function fetchReddit(q: string): Promise<SourceResult> {
  try {
    const res = await fetch(URL)
    if (!res.ok) return sourceError('reddit', 'Reddit', `HTTP ${res.status}`)
    return { source: 'reddit', label: 'Reddit', content: await res.text() }
  } catch (err) {
    return sourceError('reddit', 'Reddit', err)
  }
}

// ✗ Wrong
export async function fetchReddit(q: string): Promise<string> {
  const res = await fetch(URL)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)  // NEVER
  return res.text()
}
```

Rule: every external data fetch returns `SourceResult`. The caller decides how to handle errors. Sources never throw, never return `null`, never return `undefined`.

---

## No databases

```typescript
// ✓ Correct — flat JSON file
const prefs = JSON.parse(readFileSync('.propane/prefs.json', 'utf8'))

// ✗ Wrong — any of these
import Database from 'better-sqlite3'
import { drizzle } from 'drizzle-orm'
import mongoose from 'mongoose'
const db = new Prisma()
```

Rule: flat files only. Claude is the query layer. See `rules/how-to-flat-files.md`.

---

## Entry command

```json
// ✓ Correct
{ "scripts": { "hud": "bun src/cli.ts" } }

// ✗ Wrong
{ "scripts": { "start": "...", "dev": "..." } }
```

Rule: `bun hud` is always the primary entry point. Never `start`, `dev`, or `index`.

---

## `.propane/` and `output/` are gitignored

```gitignore
# ✓ Required in every .gitignore
.propane/
output/
.env
node_modules/
```

---

## cli.ts is the router only

`src/cli.ts` must stay under 80 lines. It imports and calls — it does not contain business logic.

```typescript
// ✓ Correct
import { loadEnv } from './configure.ts'
loadEnv()
const args = process.argv.slice(2)
switch (args[0]) {
  case undefined:
  case 'hud': await import('./hud.ts').then(m => m.runHud()); break
  default: process.stderr.write(`Unknown: ${args[0]}\n`); process.exit(1)
}
```

---

## loadEnv() runs first

`loadEnv()` must be called before any `process.env` access. It must be the first statement in `cli.ts`.

```typescript
// ✓ Correct — first line
import { loadEnv } from './configure.ts'
loadEnv()

// ✗ Wrong — env used before load
if (process.env.ANTHROPIC_API_KEY) { ... }
import { loadEnv } from './configure.ts'
loadEnv()
```

---

## ANSI HUDs handle resize

Every ANSI HUD must register a resize handler and use adaptive widths.

```typescript
// ✓ Required
let COLS = Math.min(process.stdout.columns ?? 80, 66)
process.stdout.on('resize', () => {
  COLS = Math.min(process.stdout.columns ?? 80, 66)
  redraw()
})

// ✗ Wrong
const BAR = '─'.repeat(62)  // hardcoded width
```

macOS delivers `SIGWINCH` when the terminal is resized. If not handled, the layout corrupts. Ink handles this automatically — only ANSI HUDs need this.

---

## Cursor always restored

Every exit path must restore the terminal cursor.

```typescript
// ✓ Required
process.on('SIGINT', () => {
  process.stdout.write('\x1b[?25h')  // show cursor
  process.exit(0)
})
process.on('exit', () => process.stdout.write('\x1b[?25h'))
```

---

## Platform scope

These tools target **macOS only** (Terminal.app, iTerm2, Warp). Specifically:
- Uses `process.stdin.setRawMode(true)` — works on macOS, not available on Windows
- Uses ANSI escape sequences — broadly supported on macOS terminals, inconsistent on Windows
- Resize detection via `process.stdout.on('resize')` — maps to SIGWINCH on macOS/Linux
- No cross-platform terminal library (blessed, charm, etc.) — out of scope

If Windows support becomes a requirement, replace raw mode and ANSI code usage with Ink (which abstracts these via react-reconciler) or a cross-platform library. Ink-based Wizards are inherently more portable than ANSI HUDs.
