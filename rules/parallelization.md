---
name: parallelization
description: Running sources concurrently with Promise.allSettled, batching to avoid rate limits, and communicating parallel progress in the UI.
metadata:
  tags: parallelization, concurrent, promise, batch, performance
---

# Parallelization

> Platform: macOS — Bun handles concurrent async operations natively with V8's event loop.

Running 8 sources sequentially takes 40 seconds. Running them in parallel takes 6. The terminal UI challenge: showing progress for multiple simultaneous operations without the output becoming a chaotic mess.

## Prerequisites

- `src/display.ts` with `Display` class (see `display-system.md`)
- `src/limits.ts` with `LIMITS.ai.batchSize` (see `limits.md`)
- Sources return `SourceResult` (see `source-results.md`)

---

## 1. Promise.allSettled — run all sources in parallel

Use `Promise.allSettled` (not `Promise.all`) so one failing source doesn't abort the rest:

```typescript
// src/commands/run.ts
import { Display } from '../display.ts'

export async function cmdRun(): Promise<void> {
  const display = new Display()
  display.header('My Tool')
  display.spin('Fetching sources…')

  // All sources fire simultaneously
  const [reddit, hn, youtube, perplexity] = await Promise.allSettled([
    runRedditSource(config),
    runHNSource(config),
    runYouTubeSource(config),
    runPerplexitySource(config),
  ])

  // Report each result
  for (const settled of [reddit, hn, youtube, perplexity]) {
    if (settled.status === 'rejected') {
      // Should not happen — sources never throw — but handle it
      display.fail('unknown', String(settled.reason))
      continue
    }
    const r = settled.value
    if (r.error)        display.fail(r.label, r.error)
    else if (r.skipped) display.skip(r.label, 'no API key')
    else                display.done(r.label, `${r.links?.length ?? 0} results`)
  }

  display.section('Synthesizing…')
  // ...
}
```

---

## 2. Progressive completion — print as each source finishes

For better perceived performance, print each source as it completes rather than waiting for all:

```typescript
// src/commands/run.ts
async function runSourcesWithProgress(
  sources: Array<() => Promise<SourceResult>>,
  display: Display
): Promise<SourceResult[]> {
  const results: SourceResult[] = []

  // Fire all and report as each settles
  await Promise.all(
    sources.map(async (runSource) => {
      const result = await runSource()
      results.push(result)

      // Report immediately — Display handles spinner-pause-print-resume
      if (result.error)        display.fail(result.label, result.error)
      else if (result.skipped) display.skip(result.label, 'not configured')
      else                     display.done(result.label, `${result.links?.length ?? 0} items`)
    })
  )

  return results
}
```

---

## 3. Batched parallelism — don't overwhelm APIs

For AI calls or expensive endpoints, batch using `LIMITS.ai.batchSize`:

```typescript
// src/ai.ts
import { LIMITS } from './limits.ts'

export async function runInBatches<T, R>(
  items: T[],
  fn: (item: T) => Promise<R>,
  batchSize = LIMITS.ai.batchSize
): Promise<R[]> {
  const results: R[] = []
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize)
    const batchResults = await Promise.all(batch.map(fn))
    results.push(...batchResults)
  }
  return results
}

// Usage
const summaries = await runInBatches(
  posts,
  post => callClaude(`Summarize: ${post.title}`),
  3   // 3 Claude calls at once
)
```

---

## 4. Communicating parallel progress in UI

When running multiple operations in parallel, show a count or list — not a single spinner label:

**Good — count-based:**
```typescript
let done = 0
const total = sources.length
display.spin(`Running ${total} sources…`)

await Promise.all(sources.map(async (source) => {
  const result = await source()
  done++
  display.update(`${done}/${total} sources complete`)
  display.done(result.label, `${result.links?.length ?? 0} items`)
}))
```

Output progression:
```
  ⠼  1/4 sources complete
  ✓  Reddit        12 posts
  ⠙  2/4 sources complete
  ✓  HN            8 stories
```

**For heavy parallel work — show all lanes simultaneously with a table:**
See `tables.md` — the `CrawlTable` pattern renders each row independently with its own status.

---

## 5. Timeout — don't let one slow source block the summary

Wrap slow sources with a timeout:

```typescript
function withTimeout<T>(promise: Promise<T>, ms: number, label: string): Promise<T> {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`${label} timed out after ${ms / 1000}s`)), ms)
    ),
  ])
}

// Usage
const reddit = await withTimeout(runRedditSource(config), 15_000, 'Reddit')
  .catch(err => ({
    source: 'reddit',
    label: 'Reddit',
    content: '',
    error: err.message,
  } satisfies SourceResult))
```

---

## Rules

- Use `Promise.allSettled` for source fetches — one failure must never cancel others
- Use `Promise.all` for batched AI calls where you need all results before proceeding
- Print each result as it arrives — don't buffer and dump at the end
- `Display.done/fail/skip` handles the spinner-pause-print cycle — thread-safe for parallel calls
- Add per-source timeouts for external APIs — 15s for web APIs, 30s for AI synthesis
