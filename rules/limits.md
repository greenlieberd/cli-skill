---
name: limits
description: Central LIMITS registry for all API fetch limits, time windows, and batch sizes — tune in one place.
metadata:
  tags: limits, api, rate, fetch, tuning
---

# Limits

> Platform: macOS.

Every CLI that calls external APIs needs knobs: how many posts per source, how far back to look, how many concurrent requests. Scatter these as magic numbers and tuning means a codebase-wide search. Put them in a central `limits.ts` and tuning means editing one file.

## Prerequisites

- `src/limits.ts` created at project setup (see `folder-structure.md`)
- Sources reference `LIMITS` rather than hardcoding numbers
- Used alongside retry logic for rate-limit handling (see `retry.md`)

---

## 1. The LIMITS registry

```typescript
// src/limits.ts
// Central registry for all data-fetch limits and time windows.
// Tune here when you want more or less signal.
// Rule of thumb: lean toward more data. Synthesis is cheap; missing a signal is not.

export const LIMITS = {
  reddit: {
    maxPostsPerSub: 15,     // posts fetched per subreddit per run
    timeFilter:     'week', // recency window: 'day' | 'week' | 'month'
  },
  twitter: {
    maxTweetsPerQuery: 20,
    searchTermsLimit:  5,   // how many keywords to search
  },
  youtube: {
    maxResultsPerKeyword: 10,
    lookbackDays: 7,
  },
  hn: {
    maxStories: 30,
    lookbackHours: 24,
  },
  ai: {
    batchSize: 3,           // parallel Claude/Perplexity queries per batch
    maxContextTokens: 8000, // input token ceiling before truncation
  },
  retry: {
    maxAttempts: 3,
    baseMs: 1000,
  },
} as const
```

`as const` makes every value a literal type — TypeScript will catch if a source exceeds a limit by type.

---

## 2. Using limits in sources

Reference `LIMITS` directly in source files:

```typescript
// src/sources/reddit.ts
import { LIMITS } from '../limits.ts'

export async function runRedditSource(subreddits: string[]): Promise<SourceResult> {
  const results = await Promise.all(
    subreddits.map(sub =>
      fetch(`https://www.reddit.com/r/${sub}/top.json?limit=${LIMITS.reddit.maxPostsPerSub}&t=${LIMITS.reddit.timeFilter}`)
    )
  )
  // ...
}
```

```typescript
// src/sources/youtube.ts
import { LIMITS } from '../limits.ts'

const cutoff = Date.now() - LIMITS.youtube.lookbackDays * 24 * 60 * 60 * 1000
```

---

## 3. Batch parallelization — use batchSize

When calling Claude or a search API multiple times, batch to avoid overwhelming the API:

```typescript
// src/ai.ts
import { LIMITS } from './limits.ts'

export async function batchCallClaude(prompts: string[]): Promise<string[]> {
  const results: string[] = []
  for (let i = 0; i < prompts.length; i += LIMITS.ai.batchSize) {
    const batch = prompts.slice(i, i + LIMITS.ai.batchSize)
    const batchResults = await Promise.all(batch.map(p => callClaude(p)))
    results.push(...batchResults)
  }
  return results
}
```

---

## 4. Context truncation — respect maxContextTokens

Before sending content to Claude, truncate if it exceeds the token ceiling:

```typescript
// src/ai.ts
import { LIMITS } from './limits.ts'

function truncateToTokenLimit(text: string, maxTokens: number): string {
  // Rough estimate: 1 token ≈ 4 chars in English
  const maxChars = maxTokens * 4
  if (text.length <= maxChars) return text
  return text.slice(0, maxChars) + '\n\n[truncated to fit context window]'
}

export async function synthesize(content: string): Promise<string> {
  const safe = truncateToTokenLimit(content, LIMITS.ai.maxContextTokens)
  return callClaude(safe)
}
```

---

## 5. Displaying limits in config screen

Show current limits in the HUD config screen so users know what they're running with:

```typescript
function drawLimitsSection(): void {
  process.stdout.write('\n  \x1b[1mFetch limits\x1b[0m\n\n')
  process.stdout.write(`  Reddit posts/sub       ${LIMITS.reddit.maxPostsPerSub}\n`)
  process.stdout.write(`  YouTube videos         ${LIMITS.youtube.maxResultsPerKeyword}\n`)
  process.stdout.write(`  HN stories             ${LIMITS.hn.maxStories}\n`)
  process.stdout.write(`  AI batch size          ${LIMITS.ai.batchSize}\n`)
  process.stdout.write('\n  \x1b[2mEdit src/limits.ts to tune\x1b[0m\n')
}
```

---

## Rules

- One `LIMITS` object in `src/limits.ts` — never hardcode fetch counts in source files
- Add a comment to every limit: what it controls and the tradeoff (more data = more cost)
- `batchSize` governs parallel AI calls — 3 is safe for most APIs, reduce if you hit 429s
- Add `retry` limits here too — single place to tune both data volume and resilience
- Use `as const` — TypeScript literal types catch accidental mutations
