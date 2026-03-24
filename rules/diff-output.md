---
name: diff-output
description: Before/after terminal diffs — rendering added, removed, and changed lines with color coding.
metadata:
  tags: diff, output, comparison, before-after, changes
---

# Diff Output

> Platform: macOS (Terminal.app, iTerm2, Warp).

Diffs communicate change — not just "it ran" but "here's what's different from last time." Content CLIs that compare competitor pages, changelog scrapers, and voice-calibration tools all benefit from showing what changed rather than just the new state.

## Prerequisites

- `src/colors.ts` with `A` constants (see `colors.md`)
- Output directory set up (see `output-files.md`)
- Previous content stored in `.cache/` (see `caching.md`)

---

## 1. Line diff — added and removed

```typescript
// src/diff.ts
export interface LineDiff {
  added:   string[]
  removed: string[]
  unchanged: number   // count of unchanged lines
}

export function diffLines(before: string, after: string): LineDiff {
  const bLines = new Set(before.split('\n').map(l => l.trim()).filter(Boolean))
  const aLines = after.split('\n').map(l => l.trim()).filter(Boolean)

  const added   = aLines.filter(l => !bLines.has(l))
  const removed = [...bLines].filter(l => !new Set(aLines).has(l))
  const unchanged = [...bLines].filter(l => new Set(aLines).has(l)).length

  return { added, removed, unchanged }
}
```

---

## 2. Render diff — color coded terminal output

```typescript
// src/diff.ts
export function renderDiff(diff: LineDiff, maxLines = 20): string {
  const lines: string[] = []

  if (diff.added.length === 0 && diff.removed.length === 0) {
    lines.push(`  \x1b[2m–  No changes\x1b[0m`)
    return lines.join('\n')
  }

  const addCount = diff.added.length
  const rmCount  = diff.removed.length

  lines.push(
    `  \x1b[32m+${addCount} added\x1b[0m  \x1b[31m-${rmCount} removed\x1b[0m  \x1b[2m${diff.unchanged} unchanged\x1b[0m`
  )
  lines.push('')

  const addToShow = diff.added.slice(0, maxLines)
  for (const line of addToShow) {
    lines.push(`  \x1b[32m+\x1b[0m  ${line.slice(0, 80)}`)
  }
  if (diff.added.length > maxLines) {
    lines.push(`  \x1b[2m… ${diff.added.length - maxLines} more added lines\x1b[0m`)
  }

  if (diff.removed.length > 0) {
    lines.push('')
    const rmToShow = diff.removed.slice(0, 5)   // show fewer removed lines
    for (const line of rmToShow) {
      lines.push(`  \x1b[31m-\x1b[0m  ${A.dim}${line.slice(0, 80)}\x1b[0m`)
    }
    if (diff.removed.length > 5) {
      lines.push(`  \x1b[2m… ${diff.removed.length - 5} more removed lines\x1b[0m`)
    }
  }

  return lines.join('\n')
}
```

Output:
```
  +3 added  -1 removed  47 unchanged

  +  New AI-powered search feature released
  +  Changelog: v2.4 ships with MCP support
  +  Blog: How we built the plugin system

  -  Old post: Getting started with v1.x
```

---

## 3. Inline diff for short strings — word level

For short text (titles, descriptions), word-level diff is more useful than line-level:

```typescript
// src/diff.ts
export function diffWords(before: string, after: string): string {
  const bWords = before.split(/\s+/)
  const aWords = after.split(/\s+/)

  const bSet = new Set(bWords)
  const aSet = new Set(aWords)

  return aWords.map(w =>
    !bSet.has(w) ? `\x1b[32m${w}\x1b[0m` : w    // green = new
  ).join(' ') + (
    bWords.filter(w => !aSet.has(w)).length > 0
      ? `  \x1b[31m[-${bWords.filter(w => !aSet.has(w)).join(', ')}]\x1b[0m`
      : ''
  )
}
```

---

## 4. Diff in HUD — side-by-side when wide enough

When the terminal is wide enough (≥ 100 columns), show before/after side by side:

```typescript
function renderSideBySide(before: string, after: string): string {
  const cols  = Math.min(process.stdout.columns, 120)
  const half  = Math.floor((cols - 3) / 2)
  const bLines = before.split('\n').slice(0, 20)
  const aLines = after.split('\n').slice(0, 20)
  const maxLen = Math.max(bLines.length, aLines.length)

  const lines: string[] = [
    `  ${'Before'.padEnd(half)}  ${'After'}`,
    `  ${'─'.repeat(half)}  ${'─'.repeat(half)}`,
  ]

  for (let i = 0; i < maxLen; i++) {
    const b = (bLines[i] ?? '').slice(0, half - 2).padEnd(half)
    const a = (aLines[i] ?? '').slice(0, half - 2)
    const changed = bLines[i] !== aLines[i]
    lines.push(`  ${changed ? '\x1b[2m' : ''}${b}\x1b[0m  ${changed ? '\x1b[33m' : ''}${a}\x1b[0m`)
  }

  return lines.join('\n')
}
```

---

## 5. Writing diff to output file

Include diffs in generated markdown reports:

```typescript
function formatDiffForMarkdown(diff: LineDiff): string {
  const lines: string[] = ['## Changes since last run', '']
  if (diff.added.length === 0 && diff.removed.length === 0) {
    return lines.join('\n') + 'No changes detected.\n'
  }
  for (const l of diff.added)   lines.push(`- **+** ${l}`)
  for (const l of diff.removed) lines.push(`- **-** ~~${l}~~`)
  return lines.join('\n') + '\n'
}
```

---

## Rules

- Show counts first: `+3 added  -1 removed  47 unchanged` — users scan the summary, not the lines
- Limit lines shown: 20 added, 5 removed — more than that belongs in a file, not the terminal
- Added lines: green `+`. Removed lines: red `-`, dimmed. Unchanged: not shown
- Word diff for short strings (titles), line diff for long content (pages, files)
- For large diffs, write the full diff to a file and show the path
