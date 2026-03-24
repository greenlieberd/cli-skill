---
name: retry
description: Exponential backoff with jitter for API calls, retryable status detection, and communicating retries in the terminal.
metadata:
  tags: retry, backoff, rate-limit, api, resilience
---

# Retry

> Platform: macOS (Terminal.app, iTerm2, Warp).

Network failures and rate limits are normal. A CLI that crashes on the first 429 feels fragile. One that silently retries with clear feedback feels professional.

## Prerequisites

- `src/colors.ts` with `A` color constants (see `colors.md`)
- `src/logger.ts` with `logError()` (see `logging.md`)
- Sources return `SourceResult` — retry inside the source, never at the caller (see `source-results.md`)

---

## 1. Core retry function

```typescript
// src/retry.ts
export interface RetryOptions {
  maxAttempts?: number    // default: 3
  baseMs?:      number    // default: 1000 — first delay in ms
  onRetry?:     (err: unknown, attempt: number, delayMs: number) => void
}

function sleep(ms: number): Promise<void> {
  return new Promise(r => setTimeout(r, ms))
}

function getStatus(err: unknown): number | undefined {
  if (err && typeof err === 'object') {
    const e = err as Record<string, unknown>
    if (typeof e.status === 'number') return e.status
    const msg = String(e.message ?? '')
    const m = msg.match(/\b(\d{3})\b/)
    if (m) return parseInt(m[1], 10)
  }
}

function isRetryable(err: unknown): boolean {
  const status = getStatus(err)
  if (status === undefined) {
    // Network error — always retry
    const code = (err as NodeJS.ErrnoException)?.code
    return ['ECONNRESET', 'ETIMEDOUT', 'ENOTFOUND', 'ECONNREFUSED'].includes(code ?? '')
  }
  return status === 429 || status >= 500
}

export async function retry<T>(
  fn: () => Promise<T>,
  opts: RetryOptions = {}
): Promise<T> {
  const { maxAttempts = 3, baseMs = 1000, onRetry } = opts
  let lastErr: unknown
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (err) {
      lastErr = err
      if (attempt === maxAttempts || !isRetryable(err)) throw err
      const delay = baseMs * Math.pow(2, attempt - 1)
      const jitter = Math.random() * 0.3 * delay   // ±30% jitter
      onRetry?.(err, attempt, delay + jitter)
      await sleep(delay + jitter)
    }
  }
  throw lastErr
}
```

---

## 2. Communicating retries — show feedback, don't silently spin

The `onRetry` callback is how you tell the user what's happening:

```typescript
import { c, A } from './colors.ts'

// In a source file:
const result = await retry(
  () => callRedditAPI(query),
  {
    maxAttempts: 3,
    baseMs: 1000,
    onRetry: (err, attempt, delayMs) => {
      const status = getStatus(err)
      const reason = status === 429
        ? 'rate limited'
        : status ? `HTTP ${status}` : 'network error'
      process.stdout.write(
        `  ${A.warning}↷${A.reset}  Reddit  ${A.dim}${reason} — retry ${attempt}/3 in ${Math.round(delayMs / 1000)}s${A.reset}\n`
      )
    },
  }
)
```

Output during a retry sequence:
```
  ↷  Reddit  rate limited — retry 1/3 in 1s
  ↷  Reddit  rate limited — retry 2/3 in 2s
  ✓  Reddit  12 results
```

---

## 3. Retry inside SourceResult — never propagate

Wrap `retry()` inside your source function and return `SourceResult`. The caller never sees a throw:

```typescript
// src/sources/reddit.ts
import { retry } from '../retry.ts'
import type { SourceResult } from './types.ts'

export async function runRedditSource(query: string): Promise<SourceResult> {
  try {
    const data = await retry(
      () => fetchReddit(query),
      {
        onRetry: (_, attempt) => {
          process.stdout.write(`  ${A.dim}↷  Reddit retry ${attempt}…${A.reset}\n`)
        },
      }
    )
    return { source: 'reddit', label: 'Reddit', content: format(data) }
  } catch (err) {
    return {
      source: 'reddit',
      label: 'Reddit',
      content: '',
      error: err instanceof Error ? err.message : String(err),
    }
  }
}
```

---

## 4. Rate limit detection — respect Retry-After

When an API returns a `Retry-After` header, honor it:

```typescript
async function fetchWithRateLimitRespect(url: string): Promise<Response> {
  const res = await fetch(url)
  if (res.status === 429) {
    const retryAfter = res.headers.get('Retry-After')
    const waitMs = retryAfter ? parseInt(retryAfter, 10) * 1000 : 2000
    process.stdout.write(`  ${A.warning}⏳${A.reset}  Rate limited — waiting ${waitMs / 1000}s\n`)
    await new Promise(r => setTimeout(r, waitMs))
    return fetch(url)   // one manual retry after the specified wait
  }
  return res
}
```

---

## 5. Configurable via LIMITS

Retry settings should be tunable from the central LIMITS registry (see `limits.md`):

```typescript
// src/limits.ts
export const LIMITS = {
  retry: {
    maxAttempts: 3,
    baseMs: 1000,
  },
}

// In source:
const data = await retry(fn, {
  maxAttempts: LIMITS.retry.maxAttempts,
  baseMs: LIMITS.retry.baseMs,
})
```

---

## Rules

- Retry inside the source function, not at the call site
- Always call `onRetry` so the user sees what's happening — never silent retry
- Jitter is non-negotiable — without it, multiple parallel sources hammer the API in sync
- Do not retry 4xx errors (except 429) — they indicate bad input, not transient failure
- Max 3 attempts by default — more than that and the API is probably down
