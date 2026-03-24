---
name: update-checker
description: Non-blocking version checks on startup that notify users of available updates.
metadata:
  tags: updates, version, semver, startup, npm
---

# Update Checker

> Platform: macOS (Terminal.app, iTerm2, Warp).

A version check that blocks startup is worse than no version check at all. Check in the background, cache the result, and show a single line notice if an update is available — never interrupt the user.

## Prerequisites

- `package.json` with `name` and `version` fields in project root
- `.propane/` directory for caching the last-check result
- Network available (gracefully skip if not)

---

## 1. Background check — fire and forget

Run the version check as a detached async operation. Do not await it. The result will be shown on the next run (or at the end of the current one).

```typescript
// src/update.ts
import { existsSync, readFileSync, writeFileSync } from 'fs'
import { join } from 'path'

const CACHE_FILE   = join(import.meta.dir, '..', '.propane', 'update-check.json')
const CHECK_INTERVAL_MS = 24 * 60 * 60 * 1000   // 24 hours

interface UpdateCache {
  checkedAt:   string
  latest:      string
  current:     string
}

export function checkForUpdates(pkgName: string, current: string): void {
  // Don't check more than once per 24 hours
  if (existsSync(CACHE_FILE)) {
    const cache: UpdateCache = JSON.parse(readFileSync(CACHE_FILE, 'utf8'))
    const age = Date.now() - new Date(cache.checkedAt).getTime()
    if (age < CHECK_INTERVAL_MS) return   // cached — skip network call
  }

  // Fire and forget — never await this
  void fetchLatestVersion(pkgName, current)
}

async function fetchLatestVersion(pkgName: string, current: string): Promise<void> {
  try {
    const res  = await fetch(`https://registry.npmjs.org/${pkgName}/latest`, { signal: AbortSignal.timeout(3000) })
    if (!res.ok) return
    const data  = await res.json()
    const latest = data.version as string

    writeFileSync(CACHE_FILE, JSON.stringify({
      checkedAt: new Date().toISOString(),
      latest,
      current,
    } satisfies UpdateCache))
  } catch {
    // Network unavailable — silently skip
  }
}
```

---

## 2. Show the notice — one line, easy to dismiss

```typescript
// src/update.ts
export function getUpdateNotice(): string | null {
  if (!existsSync(CACHE_FILE)) return null
  try {
    const cache: UpdateCache = JSON.parse(readFileSync(CACHE_FILE, 'utf8'))
    if (cache.latest === cache.current) return null
    if (!isNewerVersion(cache.latest, cache.current)) return null
    return `  \x1b[33m↑\x1b[0m  Update available: ${cache.current} → ${cache.latest}  \x1b[2mbun install -g .\x1b[0m`
  } catch {
    return null
  }
}

function isNewerVersion(latest: string, current: string): boolean {
  const [lMaj, lMin, lPatch] = latest.split('.').map(Number)
  const [cMaj, cMin, cPatch] = current.split('.').map(Number)
  return lMaj > cMaj || (lMaj === cMaj && lMin > cMin) || (lMaj === cMaj && lMin === cMin && lPatch > cPatch)
}
```

---

## 3. Integrate at startup

```typescript
// src/cli.ts
import { checkForUpdates, getUpdateNotice } from './update.ts'
import pkg from '../package.json'

// 1. Check in background (non-blocking)
checkForUpdates(pkg.name, pkg.version)

// 2. Show cached notice from previous check
const notice = getUpdateNotice()
if (notice) process.stdout.write(`${notice}\n`)

// 3. Continue with normal startup
runHud()
```

---

## 4. Placement in HUD

In an ANSI HUD, show the notice on the footer line, not above the menu:

```typescript
function drawFooter(hints: string[]): void {
  const notice = getUpdateNotice()
  if (notice) process.stdout.write(`${notice}\n`)
  process.stdout.write(`  ${hints.map(h => `\x1b[2m${h}\x1b[0m`).join('   ')}\n`)
}
```

---

## 5. For non-npm tools — use GitHub releases API

If the tool isn't on npm, check the GitHub releases API instead:

```typescript
async function fetchLatestFromGitHub(repo: string): Promise<string | null> {
  // repo = "owner/repo-name"
  try {
    const res = await fetch(`https://api.github.com/repos/${repo}/releases/latest`, {
      headers: { 'User-Agent': 'cli-update-check' },
      signal: AbortSignal.timeout(3000),
    })
    if (!res.ok) return null
    const data = await res.json()
    return (data.tag_name as string).replace(/^v/, '')
  } catch {
    return null
  }
}
```

---

## Rules

- Never `await` the version check — it runs fire-and-forget
- Cache the result for 24 hours — no network call on every run
- Show the notice from cache, not from a live fetch
- One line maximum — update notice is informational, not a blocker
- Gracefully skip on network timeout or error — never crash because npm is down
