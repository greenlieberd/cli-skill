---
name: source-results
description: The SourceResult interface — every external data fetch returns a result object, never throws.
metadata:
  tags: sources, data, api, error-handling, pattern
---

# Source Results

> Prerequisites: Bun runtime, `src/sources/types.ts` in the project.

Every external data fetch — HTTP API, file read, web scrape — follows this pattern. Sources never throw. They always return a `SourceResult`. The caller decides what to do with errors.

---

## The SourceResult interface

```typescript
// src/sources/types.ts — copy this verbatim into every project
export interface SourceResult {
  source:   string     // machine ID: 'reddit', 'firecrawl', 'local-file'
  label:    string     // human display: 'Reddit r/saas', 'Firecrawl'
  content:  string     // fetched text — empty string on error or skip
  links?:   string[]   // URLs found in the content
  error?:   string     // error message if fetch failed (content will be '')
  skipped?: boolean    // true if source was toggled off in config (content will be '')
}

// Helpers — use these instead of constructing objects manually
export function sourceError(source: string, label: string, err: unknown): SourceResult {
  return { source, label, content: '', error: String(err) }
}

export function sourceSkip(source: string, label: string): SourceResult {
  return { source, label, content: '', skipped: true }
}
```

**Reading results in callers:**
```typescript
const result = await fetchReddit(query)
if (result.skipped) continue                    // user turned this off
if (result.error)   logError(result)            // fetch failed — log but continue
if (!result.content) continue                   // nothing to process
processContent(result.content)                  // happy path
```

---

## HTTP API source

```typescript
// src/sources/reddit.ts
import type { SourceResult } from './types.ts'
import { sourceError } from './types.ts'

export async function fetchReddit(query: string): Promise<SourceResult> {
  const label = `Reddit "${query}"`
  try {
    const url = `https://www.reddit.com/search.json?q=${encodeURIComponent(query)}&limit=10&sort=new`
    const res  = await fetch(url, { headers: { 'User-Agent': 'cli-tool/1.0' } })

    if (res.status === 429) return sourceError('reddit', label, 'Rate limited — wait 60s')
    if (!res.ok)            return sourceError('reddit', label, `HTTP ${res.status}`)

    const data  = await res.json() as any
    const posts = data.data.children
      .map((c: any) => `### ${c.data.title}\n${c.data.selftext}`)
      .join('\n\n')

    return {
      source:  'reddit',
      label,
      content: posts || '(no results)',
      links:   data.data.children.map((c: any) => `https://reddit.com${c.data.permalink}`),
    }
  } catch (err) {
    return sourceError('reddit', label, err)
  }
}
```

---

## API key source (with key check)

```typescript
// src/sources/perplexity.ts
import type { SourceResult } from './types.ts'
import { sourceError } from './types.ts'

export async function fetchPerplexity(query: string): Promise<SourceResult> {
  const label = 'Perplexity'
  const key   = process.env.PERPLEXITY_API_KEY
  if (!key) return sourceError('perplexity', label, 'PERPLEXITY_API_KEY not set — add to .env')

  try {
    const res = await fetch('https://api.perplexity.ai/chat/completions', {
      method:  'POST',
      headers: { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        model: 'llama-3.1-sonar-small-128k-online',
        messages: [{ role: 'user', content: query }],
      }),
    })
    if (!res.ok) return sourceError('perplexity', label, `HTTP ${res.status}`)
    const data = await res.json() as any
    return { source: 'perplexity', label, content: data.choices[0].message.content }
  } catch (err) {
    return sourceError('perplexity', label, err)
  }
}
```

---

## File system source

```typescript
// src/sources/local-files.ts
import type { SourceResult } from './types.ts'
import { sourceError } from './types.ts'
import { readdirSync, readFileSync, existsSync } from 'fs'
import { join } from 'path'

export async function readLocalFiles(dir: string): Promise<SourceResult> {
  const label = `Local files in ${dir}`
  if (!existsSync(dir)) return sourceError('local', label, `Directory not found: ${dir}`)

  try {
    const files = readdirSync(dir).filter(f => f.endsWith('.md'))
    if (!files.length) return { source: 'local', label, content: '', skipped: true }

    const content = files
      .map(f => `## ${f}\n${readFileSync(join(dir, f), 'utf8')}`)
      .join('\n\n---\n\n')

    return { source: 'local', label, content }
  } catch (err) {
    return sourceError('local', label, err)
  }
}
```

---

## Skippable source (user toggle)

```typescript
// src/sources/twitter.ts
import type { SourceResult } from './types.ts'
import { sourceSkip } from './types.ts'
import { loadIndex } from '../index-config.ts'

export async function fetchTwitter(query: string): Promise<SourceResult> {
  const label = 'Twitter/X'
  const index = loadIndex()  // .propane/index.json

  if (!index.sources.twitter?.enabled) {
    return sourceSkip('twitter', label)
  }

  // ... fetch logic
}
```

---

## Running sources in parallel

```typescript
// Run all sources concurrently — each returns SourceResult (never throws)
const [reddit, perplexity, local] = await Promise.all([
  fetchReddit(query),
  fetchPerplexity(query),
  readLocalFiles('./data'),
])

const results = [reddit, perplexity, local]
const errors  = results.filter(r => r.error)
const content = results.filter(r => r.content)

// Log errors but continue
errors.forEach(r => logError('source', r.error))
```

---

## Response caching

Avoid re-fetching the same query within a session:

```typescript
// src/sources/cached.ts
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs'
import { join, createHash } from 'path'  // note: createHash is from 'crypto'
import { createHash as ch } from 'crypto'

const CACHE_DIR = join(process.cwd(), '.cache')

function cacheKey(source: string, query: string): string {
  return ch('md5').update(`${source}:${query}`).digest('hex').slice(0, 16)
}

export async function withCache<T>(
  source: string, query: string, ttlMs: number, fn: () => Promise<T>
): Promise<T> {
  const key  = cacheKey(source, query)
  const file = join(CACHE_DIR, `${source}-${key}.json`)
  mkdirSync(CACHE_DIR, { recursive: true })

  if (existsSync(file)) {
    const cached = JSON.parse(readFileSync(file, 'utf8'))
    if (Date.now() - cached.ts < ttlMs) return cached.data
  }

  const data = await fn()
  writeFileSync(file, JSON.stringify({ ts: Date.now(), data }))
  return data
}

// Usage:
const result = await withCache('reddit', query, 30 * 60 * 1000, () => fetchReddit(query))
```

---

## Testing sources

Test the logic, not the HTTP call. Use a Bun fetch mock:

```typescript
// tests/sources.test.ts
import { test, expect, mock } from 'bun:test'
import { fetchReddit } from '../src/sources/reddit.ts'

// Mock fetch globally
const originalFetch = globalThis.fetch

test('fetchReddit returns sourceError on 429', async () => {
  globalThis.fetch = mock(() => Promise.resolve({ ok: false, status: 429 } as Response))
  const result = await fetchReddit('test')
  expect(result.error).toContain('Rate limited')
  expect(result.content).toBe('')
  globalThis.fetch = originalFetch
})

test('fetchReddit returns content on success', async () => {
  globalThis.fetch = mock(() => Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ data: { children: [
      { data: { title: 'Test post', selftext: 'Content', permalink: '/r/test/1' } }
    ] } }),
  } as Response))
  const result = await fetchReddit('test')
  expect(result.content).toContain('Test post')
  expect(result.error).toBeUndefined()
  globalThis.fetch = originalFetch
})
```
