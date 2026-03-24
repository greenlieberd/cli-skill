---
name: testing
description: bun:test patterns for CLI tools — mocking fetch, testing SourceResult shape, fixture dirs, and testing HUD state.
metadata:
  tags: testing, bun, mock, fetch, fixtures
---

# Testing

> Platform: macOS — bun:test is Bun's built-in test runner, no separate install needed.

CLI tests have one enemy: real network calls. Mock `fetch` globally and restore it in `afterEach`. Test the shape of outputs, not the content — content is AI-generated and non-deterministic.

## Prerequisites

- Bun ≥ 1.0 (`bun --version`)
- `src/sources/types.ts` with `SourceResult` interface (see `source-results.md`)
- Tests in `tests/` at project root (not `src/tests/`)
- Run with: `bun test` or `bun test tests/sources.test.ts`

---

## 1. Mock fetch globally — the standard setup

```typescript
// tests/sources.test.ts
import { mock, beforeEach, afterEach, test, expect, describe } from 'bun:test'

describe('runRedditSource', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    global.fetch = mock(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: { children: MOCK_POSTS } }),
        text: () => Promise.resolve(''),
        headers: new Headers(),
      } as unknown as Response)
    ) as unknown as typeof fetch
  })

  afterEach(() => {
    global.fetch = originalFetch   // always restore — don't leak into other tests
  })

  test('returns valid SourceResult shape', async () => {
    const { runRedditSource } = await import('../src/sources/reddit')
    const result = await runRedditSource({ subreddits: ['MachineLearning'] })
    expect(result.source).toBe('reddit')
    expect(result.label).toBe('Reddit')
    expect(typeof result.content).toBe('string')
    expect(Array.isArray(result.links)).toBe(true)
    expect(result.error).toBeUndefined()
  })
})
```

Key patterns:
- `await import()` **inside the test** — ensures the mock is in place before the module executes any module-level `fetch`
- Always `global.fetch = originalFetch` in `afterEach` — never assume test isolation
- Test the shape, not the exact content

---

## 2. Mock fixtures — realistic test data

```typescript
// tests/fixtures/reddit.ts
export const MOCK_POSTS = [
  {
    data: {
      id: 't3_abc1',
      title: 'Claude Code plugin system released',
      url: 'https://reddit.com/r/MachineLearning/comments/abc1',
      score: 120,
      num_comments: 45,
      subreddit: 'MachineLearning',
      created_utc: 1700000000,
    },
  },
  {
    data: {
      id: 't3_abc2',
      title: 'AI coding tools comparison',
      url: 'https://reddit.com/r/programming/comments/abc2',
      score: 80,
      num_comments: 30,
      subreddit: 'programming',
      created_utc: 1700000100,
    },
  },
]
```

Keep fixtures minimal but realistic — enough fields to trigger your parsing logic.

---

## 3. Test error paths — sources must handle failures gracefully

```typescript
test('returns SourceResult with error when API fails', async () => {
  // Override with a failing mock for this test only
  global.fetch = mock(() => Promise.reject(new Error('ECONNREFUSED'))) as unknown as typeof fetch

  const { runRedditSource } = await import('../src/sources/reddit')
  const result = await runRedditSource({ subreddits: ['MachineLearning'] })

  expect(result.source).toBe('reddit')
  expect(typeof result.error).toBe('string')
  expect(result.content).toBe('')
  // must not throw
})

test('returns skipped result when API key is missing', async () => {
  const originalKey = process.env.REDDIT_API_KEY
  delete process.env.REDDIT_API_KEY

  const { runRedditSource } = await import('../src/sources/reddit')
  const result = await runRedditSource({ subreddits: [] })

  expect(result.skipped).toBe(true)

  process.env.REDDIT_API_KEY = originalKey
})
```

---

## 4. Test pure functions separately — no mocking needed

Not everything calls the network. Pure functions (formatters, parsers, validators) test without any mocks:

```typescript
// tests/output.test.ts
import { test, expect } from 'bun:test'
import { makeFilename, progressBar } from '../src/output'

test('makeFilename produces YYYY-MM-DD-slug.ext', () => {
  const name = makeFilename('Reddit AI roundup', 'md')
  expect(name).toMatch(/^\d{4}-\d{2}-\d{2}-reddit-ai-roundup\.md$/)
})

test('progressBar renders correct fill ratio', () => {
  const bar = progressBar(10, 20, 10)
  expect(bar).toContain('█'.repeat(5))   // 50% fill
  expect(bar).toContain('░'.repeat(5))
})
```

---

## 5. Test HUD state transitions — no terminal required

ANSI HUD state machines are testable by extracting state transitions into pure functions:

```typescript
// src/hud-state.ts
export type Screen = 'home' | 'content' | 'config' | 'help'

export interface State {
  screen:   Screen
  selected: number
  items:    string[]
}

export function handleKey(state: State, key: string): State {
  if (key === '\x1b[A') return { ...state, selected: Math.max(0, state.selected - 1) }
  if (key === '\x1b[B') return { ...state, selected: Math.min(state.items.length - 1, state.selected + 1) }
  if (key === '\r')     return { ...state, screen: 'content' }
  if (key === '?')      return { ...state, screen: 'help' }
  return state
}
```

```typescript
// tests/hud-state.test.ts
import { test, expect } from 'bun:test'
import { handleKey } from '../src/hud-state'

test('arrow down increments selection', () => {
  const state = { screen: 'home' as const, selected: 0, items: ['a', 'b', 'c'] }
  expect(handleKey(state, '\x1b[B').selected).toBe(1)
})

test('selection clamps at bottom', () => {
  const state = { screen: 'home' as const, selected: 2, items: ['a', 'b', 'c'] }
  expect(handleKey(state, '\x1b[B').selected).toBe(2)   // stays at 2
})
```

---

## 6. File fixtures — create and clean up temp dirs

```typescript
// tests/output.test.ts
import { mkdirSync, rmSync } from 'fs'
import { join } from 'path'
import { beforeEach, afterEach } from 'bun:test'

const TMP = join(import.meta.dir, '__tmp__')

beforeEach(() => mkdirSync(TMP, { recursive: true }))
afterEach(() => rmSync(TMP, { recursive: true, force: true }))
```

---

## Rules

- Always restore `global.fetch` in `afterEach` — test file order affects global state
- `await import()` inside each test — ensures the module sees your mock, not the real fetch
- Test SourceResult shape (source, label, content, error, skipped) — not content text
- Extract state transitions into pure functions — makes HUD logic testable without a TTY
- Never hit real APIs in tests — if a source can't be mocked, mark it `test.skip`
