---
name: configuration
description: Interactive readline setup wizard for API keys — KeyDef array, parseEnv/serializeEnv, masked display, required vs optional.
metadata:
  tags: configuration, setup, wizard, readline, keys
---

# Configuration

> Platform: macOS (Terminal.app, iTerm2, Warp).

Every CLI that calls external APIs needs a setup flow. `bun run configure` walks the user through entering keys, shows masked current values, skips optional keys, and writes a clean `.env`. It's the difference between "add your key to .env" (docs-only) and "run this to get started" (guided).

## Prerequisites

- `src/configure.ts` for `loadEnv()` and `maskValue()` (see `environment-setup.md`)
- `.env.example` documenting every key (see `environment-setup.md`)
- Node `readline` built-in — no external dependency

---

## 1. KeyDef array — single source of truth

Define every key in a typed array. This drives the wizard, validation, and the config screen display:

```typescript
// src/configuration.ts
export interface KeyDef {
  key:      string
  required: boolean
  label:    string
  hint:     string       // where to get the key
}

export const KEY_DEFS: KeyDef[] = [
  {
    key:      'ANTHROPIC_API_KEY',
    required: true,
    label:    'Anthropic API Key',
    hint:     'Get at console.anthropic.com/keys — required for all AI features',
  },
  {
    key:      'PERPLEXITY_API_KEY',
    required: false,
    label:    'Perplexity API Key',
    hint:     'Get at perplexity.ai/settings/api — enables live web search (~$0.002/query)',
  },
  {
    key:      'FIRECRAWL_API_KEY',
    required: false,
    label:    'Firecrawl API Key',
    hint:     'Get at firecrawl.dev — enables JS-rendered site scraping',
  },
]
```

---

## 2. .env file helpers — parse and serialize cleanly

```typescript
// src/configuration.ts
import { existsSync, readFileSync } from 'fs'
import { join } from 'path'

const ENV_PATH = join(import.meta.dir, '..', '.env')

export function parseEnv(text: string): Record<string, string> {
  const env: Record<string, string> = {}
  for (const line of text.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue
    const idx = trimmed.indexOf('=')
    if (idx === -1) continue
    const k = trimmed.slice(0, idx).trim()
    const v = trimmed.slice(idx + 1).trim()
    if (k) env[k] = v
  }
  return env
}

export function serializeEnv(env: Record<string, string>): string {
  const required = KEY_DEFS.filter(d => d.required)
  const optional = KEY_DEFS.filter(d => !d.required)

  const lines: string[] = ['# Required']
  for (const def of required) lines.push(`${def.key}=${env[def.key] ?? ''}`)

  lines.push('', '# Optional')
  for (const def of optional) lines.push(`${def.key}=${env[def.key] ?? ''}`)

  return lines.join('\n').trimEnd() + '\n'
}

export function maskValue(v: string): string {
  if (!v)         return '(not set)'
  if (v.length <= 8) return '••••••••'
  return v.slice(0, 4) + '•'.repeat(Math.min(v.length - 8, 12)) + v.slice(-4)
}
```

---

## 3. The wizard — readline walk-through

```typescript
// src/configuration.ts
import { createInterface } from 'readline'

export async function runConfigure(): Promise<void> {
  const existing = existsSync(ENV_PATH)
    ? parseEnv(readFileSync(ENV_PATH, 'utf8'))
    : {}

  const rl  = createInterface({ input: process.stdin, output: process.stdout })
  const ask = (q: string): Promise<string> =>
    new Promise(resolve => rl.question(q, resolve))

  process.stdout.write('\n  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')
  process.stdout.write('    Configuration\n')
  process.stdout.write('  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n')
  process.stdout.write('  Press Enter to keep the current value.\n')
  process.stdout.write('  Type "clear" to remove a key.\n\n')

  const updated: Record<string, string> = { ...existing }

  for (const def of KEY_DEFS) {
    const current = existing[def.key] ?? ''
    const tag     = def.required ? ' \x1b[31m[required]\x1b[0m' : ' \x1b[2m[optional]\x1b[0m'
    const status  = current
      ? `\x1b[2mcurrent: ${maskValue(current)}\x1b[0m`
      : '\x1b[31mnot set\x1b[0m'

    process.stdout.write(`  ${def.label}${tag}\n`)
    process.stdout.write(`  \x1b[2m${def.hint}\x1b[0m\n`)
    process.stdout.write(`  Status: ${status}\n`)

    const answer = (await ask('  → ')).trim()

    if (answer === '') {
      // Keep current
    } else if (answer.toLowerCase() === 'clear') {
      delete updated[def.key]
      process.stdout.write('  \x1b[32m✓\x1b[0m  Cleared\n')
    } else {
      updated[def.key] = answer
      process.stdout.write('  \x1b[32m✓\x1b[0m  Saved\n')
    }
    process.stdout.write('\n')
  }

  rl.close()
  await Bun.write(ENV_PATH, serializeEnv(updated))

  // Summary
  const missing = KEY_DEFS.filter(d => d.required && !updated[d.key])
  process.stdout.write('  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')
  if (missing.length > 0) {
    process.stdout.write('  \x1b[33m⚠\x1b[0m  Missing required keys:\n')
    for (const d of missing) {
      process.stdout.write(`     \x1b[31m✗\x1b[0m  ${d.key}\n`)
    }
  } else {
    process.stdout.write('  \x1b[32m✓\x1b[0m  All required keys set. Run \x1b[1mbun hud\x1b[0m to start.\n')
  }
  process.stdout.write('  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n')
}
```

---

## 4. Wire it into cli.ts

```typescript
// src/cli.ts
const cmd = process.argv[2]

if (cmd === 'configure') {
  await runConfigure()
  process.exit(0)
}
```

Add to `package.json`:
```json
{
  "scripts": {
    "configure": "bun src/cli.ts configure",
    "hud":       "bun src/cli.ts"
  }
}
```

---

## 5. Config screen in HUD — read KeyDefs for live status

Reuse `KEY_DEFS` to render a status screen inside the HUD (no separate data):

```typescript
function drawConfigScreen(): void {
  process.stdout.write('\n  \x1b[1mAPI Keys\x1b[0m\n\n')
  for (const def of KEY_DEFS) {
    const val    = process.env[def.key]
    const status = val
      ? `\x1b[32m${maskValue(val)}\x1b[0m`
      : def.required
        ? '\x1b[31m(not set)\x1b[0m'
        : '\x1b[2m(not set)\x1b[0m'
    process.stdout.write(`  ${def.label.padEnd(26)}${status}\n`)
  }
  process.stdout.write('\n  \x1b[2mRun: bun run configure\x1b[0m\n')
}
```

---

## Rules

- `KEY_DEFS` is the single source of truth — never hardcode key names elsewhere
- Always mask values in display: `sk-ant-••••••••••••••••efgh` not the full key
- Enter to keep, "clear" to remove — minimal cognitive load
- Print a summary at the end: required missing → warn, all set → ready message
- Wire `bun run configure` as a separate script, not part of `bun hud`
