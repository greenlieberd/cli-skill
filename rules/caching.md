---
name: caching
description: .cache/ directory, TTL-based invalidation, diff tracking for changelogs, and cache-first fetch patterns.
metadata:
  tags: caching, cache, ttl, diff, fetch
---

# Caching

> Platform: macOS — Bun file I/O is used for all cache reads and writes.

Caching has two jobs: avoid redundant API calls (saves money and time), and track what changed between runs (enables diff detection). Both use the same `.cache/` directory pattern.

## Prerequisites

- `.cache/` in `.gitignore` — cached data is never committed
- `output/` for generated content, `.cache/` for raw fetched data — keep them separate
- Bun runtime for `Bun.file()` and `Bun.write()`

---

## 1. .gitignore entries

```bash
# .gitignore
.cache/
.propane/
output/
```

---

## 2. Cache-first fetch — skip if fresh

```typescript
// src/cache.ts
import { existsSync, mkdirSync } from 'fs'
import { join } from 'path'

const CACHE_DIR = join(import.meta.dir, '..', '.cache')

export interface CacheEntry<T> {
  data:      T
  fetchedAt: string   // ISO timestamp
}

export async function cachedFetch<T>(
  key: string,                       // e.g., 'reddit-MachineLearning'
  fetcher: () => Promise<T>,
  ttlMs = 60 * 60 * 1000            // default: 1 hour
): Promise<T> {
  mkdirSync(CACHE_DIR, { recursive: true })

  const path  = join(CACHE_DIR, `${key}.json`)
  const file  = Bun.file(path)

  if (await file.exists()) {
    const entry: CacheEntry<T> = await file.json()
    const age = Date.now() - new Date(entry.fetchedAt).getTime()
    if (age < ttlMs) return entry.data   // cache hit
  }

  // Cache miss or expired — fetch and store
  const data = await fetcher()
  await Bun.write(path, JSON.stringify({ data, fetchedAt: new Date().toISOString() }))
  return data
}
```

Usage:
```typescript
// 1 hour TTL for Reddit data
const posts = await cachedFetch(
  'reddit-MachineLearning',
  () => fetchRedditPosts('MachineLearning'),
  60 * 60 * 1000
)
```

---

## 3. Diff tracking — detect what changed between runs

For changelog scraping, store the previous content and compare:

```typescript
// src/cache.ts
const CHANGELOG_DIR = join(CACHE_DIR, 'changelogs')

export async function fetchWithDiff(
  url: string,
  fetcher: () => Promise<string>
): Promise<{ content: string; isNew: boolean; diff: string | null }> {
  mkdirSync(CHANGELOG_DIR, { recursive: true })

  // Sanitize URL to filename
  const key  = url.replace(/[^a-z0-9]/gi, '-').slice(0, 80)
  const path = join(CHANGELOG_DIR, `${key}.txt`)
  const file = Bun.file(path)

  const current = await fetcher()

  if (!(await file.exists())) {
    await Bun.write(path, current)
    return { content: current, isNew: true, diff: null }
  }

  const previous = await file.text()

  if (current === previous) {
    return { content: current, isNew: false, diff: null }
  }

  // Content changed — compute line diff
  const diff = computeDiff(previous, current)
  await Bun.write(path, current)   // update cache to latest
  return { content: current, isNew: false, diff }
}

function computeDiff(before: string, after: string): string {
  const bLines = before.split('\n')
  const aLines = after.split('\n')
  const added   = aLines.filter(l => !bLines.includes(l)).slice(0, 20)
  const removed = bLines.filter(l => !aLines.includes(l)).slice(0, 10)

  const lines: string[] = []
  for (const l of added)   lines.push(`+ ${l}`)
  for (const l of removed) lines.push(`- ${l}`)
  return lines.join('\n')
}
```

---

## 4. Cache namespacing — avoid key collisions

Use a naming convention that includes the source name and enough context to be unique:

```typescript
// Patterns:
`${sourceName}-${identifier}`          // 'reddit-MachineLearning'
`${sourceName}-${date}`                // 'hn-2026-03-24'
`${sourceName}-${hash(url)}`           // for URL-keyed content
```

Simple hash for URLs:
```typescript
function hashUrl(url: string): string {
  // djb2 hash — fast, no crypto needed for cache keys
  let h = 5381
  for (let i = 0; i < url.length; i++) h = ((h << 5) + h) ^ url.charCodeAt(i)
  return Math.abs(h).toString(36)
}
```

---

## 5. Cache invalidation — manual clear command

Add a `bun run cache:clear` command for when users want fresh data:

```typescript
// src/cli.ts
if (cmd === 'cache:clear') {
  const dir = join(import.meta.dir, '..', '.cache')
  if (existsSync(dir)) {
    rmSync(dir, { recursive: true })
    process.stdout.write('  ✓  Cache cleared\n')
  } else {
    process.stdout.write('  –  No cache to clear\n')
  }
  process.exit(0)
}
```

```json
// package.json
{
  "scripts": {
    "cache:clear": "bun src/cli.ts cache:clear"
  }
}
```

---

## 6. Cache size reporting in config screen

```typescript
function getCacheSize(): string {
  const dir = join(import.meta.dir, '..', '.cache')
  if (!existsSync(dir)) return '0 KB'
  let bytes = 0
  for (const file of readdirSync(dir, { recursive: true }) as string[]) {
    try { bytes += statSync(join(dir, file)).size } catch { /* skip */ }
  }
  return bytes > 1_000_000 ? `${(bytes / 1_000_000).toFixed(1)} MB` : `${Math.round(bytes / 1000)} KB`
}

process.stdout.write(`  Cache size           ${getCacheSize()}\n`)
process.stdout.write(`  \x1b[2mbun run cache:clear to reset\x1b[0m\n`)
```

---

## Rules

- `.cache/` is gitignored — never commit cached data
- TTL defaults: fast-changing APIs (Twitter, HN) → 1 hour; slow-changing (changelogs) → 24 hours
- Always `mkdirSync({ recursive: true })` before writing — cache dir may not exist
- Diff tracking stores the raw previous content, not a hash — enables line-level comparison
- Cache keys are sanitized filenames — no slashes, no special characters
