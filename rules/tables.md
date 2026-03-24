---
name: tables
description: Rendering tabular data in ANSI HUDs — column alignment, scrollable rows, per-row status, review-and-discard patterns.
metadata:
  tags: tables, lists, columns, alignment, scroll
---

# Tables

> Platform: macOS (Terminal.app, iTerm2, Warp).

Tables in the terminal need three things: aligned columns, a scrollable viewport when rows exceed screen height, and per-row status indicators that update live. Done right, they feel as readable as a spreadsheet. Done wrong, they wrap unpredictably and become noise.

## Prerequisites

- `src/colors.ts` with `A` color constants (see `colors.md`)
- ANSI HUD with raw mode enabled (see `hud-screens.md`)
- Terminal width check: `Math.min(process.stdout.columns, 88)`

---

## 1. Column alignment — padEnd and padStart

Use `padEnd()` for left-aligned text, `padStart()` for right-aligned numbers:

```typescript
// Column widths as named constants — change in one place
const COL = {
  index:   4,
  domain:  30,
  status:  16,
  count:   6,
  bar:     18,
}

function headerRow(): string {
  return (
    '\x1b[2m' +
    '  #   ' +
    'Name'.padEnd(COL.domain) +
    'Status'.padEnd(COL.status) +
    'Found'.padStart(COL.count) +
    'Saved'.padStart(COL.count) +
    '  Progress' +
    '\x1b[0m'
  )
}

function dataRow(item: RowData): string {
  return (
    `  ${String(item.index).padStart(3)} ` +
    item.name.slice(0, COL.domain - 1).padEnd(COL.domain) +
    statusCell(item.status).padEnd(COL.status + 10) +  // +10 for escape codes
    (item.found ? String(item.found).padStart(COL.count) : '     -') +
    (item.saved ? String(item.saved).padStart(COL.count) : '     -') +
    '  ' + progressBar(item.done, item.total) +
    '\x1b[K'   // clear to end of line — removes artifacts on resize
  )
}
```

---

## 2. Status cells — icon + color + padded

Status cells show the state of each row. Always pad to the same width so columns stay aligned even as status text changes:

```typescript
type Status = 'waiting' | 'running' | 'done' | 'failed' | 'skipped'

const SPIN = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

function statusCell(status: Status, frame: number): string {
  const s = SPIN[frame % SPIN.length]
  const W = 14
  switch (status) {
    case 'waiting':  return `\x1b[2m○ waiting\x1b[0m`.padEnd(W + 10)
    case 'running':  return `\x1b[36m${s} running\x1b[0m`.padEnd(W + 10)
    case 'done':     return `\x1b[32m✓ done\x1b[0m`.padEnd(W + 10)
    case 'failed':   return `\x1b[31m✗ failed\x1b[0m`.padEnd(W + 10)
    case 'skipped':  return `\x1b[2m– skipped\x1b[0m`.padEnd(W + 10)
  }
}
```

Note: `padEnd()` counts escape code characters as visible — add `+ 10` (or the actual escape code byte count) to keep visual alignment.

---

## 3. Scrollable viewport — clip to visible rows

Never render all rows to stdout. Clip to what fits:

```typescript
class Table {
  private rows:   RowData[] = []
  private scroll = 0
  private frame  = 0

  render(terminalRows = process.stdout.rows ?? 30): void {
    const viewHeight = Math.max(5, terminalRows - 8)   // reserve header + footer
    const maxScroll  = Math.max(0, this.rows.length - viewHeight)
    this.scroll      = Math.min(this.scroll, maxScroll)

    const visible = this.rows.slice(this.scroll, this.scroll + viewHeight)
    const below   = this.rows.length - this.scroll - viewHeight

    const out: string[] = ['\x1b[H']   // cursor home
    out.push(headerRow())
    out.push('\x1b[2m' + '─'.repeat(80) + '\x1b[0m')

    for (const row of visible) {
      out.push(dataRow(row))
    }

    // Scroll indicator
    out.push(below > 0
      ? `\x1b[2m  ↓ ${below} more\x1b[0m\x1b[K`
      : '\x1b[K'
    )

    process.stdout.write(out.join('\n'))
  }

  scrollDown(): void { this.scroll++ }
  scrollUp():   void { this.scroll = Math.max(0, this.scroll - 1) }
}
```

---

## 4. Tab filters — All / Running / Done / Failed

Tabs narrow the visible rows without losing the underlying data:

```typescript
const TABS = ['All', 'Running', 'Done', 'Failed'] as const
type Tab = typeof TABS[number]

function filterRows(rows: RowData[], tab: Tab): RowData[] {
  if (tab === 'All')     return rows
  if (tab === 'Running') return rows.filter(r => r.status === 'running')
  if (tab === 'Done')    return rows.filter(r => r.status === 'done')
  if (tab === 'Failed')  return rows.filter(r => r.status === 'failed')
  return rows
}

function tabBar(active: number, counts: Record<Tab, number>): string {
  return TABS.map((t, i) => {
    const label = `${t} ${counts[t]}`
    return i === active
      ? `\x1b[1;48;5;238m ${label} \x1b[0m`   // bold + dark bg
      : `\x1b[2m ${label} \x1b[0m`
  }).join('  \x1b[2m│\x1b[0m  ')
}
```

Navigate tabs with `←` / `→` keys.

---

## 5. Review list — keep / discard / accept-all

For batch review flows (approve generated items one by one):

```typescript
// src/review.ts
import { createInterface } from 'readline'

export async function reviewItems<T extends { title: string }>(
  items: T[]
): Promise<T[]> {
  const rl  = createInterface({ input: process.stdin, output: process.stdout })
  const ask = (q: string): Promise<string> =>
    new Promise(resolve => rl.question(q, resolve))

  process.stdout.write('\n  \x1b[2mKeys: k keep  d discard  a accept all  q stop\x1b[0m\n\n')
  const kept: T[] = []

  for (let i = 0; i < items.length; i++) {
    process.stdout.write(`  \x1b[1m${i + 1}/${items.length}\x1b[0m  ${items[i].title}\n`)
    const answer = (await ask('  > ')).trim().toLowerCase()

    if (answer === 'a') { kept.push(items[i], ...items.slice(i + 1)); break }
    if (answer === 'q') break
    if (answer !== 'd') kept.push(items[i])   // default: keep on Enter
  }

  rl.close()
  process.stdout.write(`\n  \x1b[2mKept ${kept.length} of ${items.length}\x1b[0m\n`)
  return kept
}
```

---

## Rules

- Define column widths as named constants — never repeat magic numbers
- Add `\x1b[K` at end of every row — clears leftover characters on resize
- Count escape codes in `padEnd()` — they add invisible bytes that throw alignment off
- Clip to viewport — never render all rows for large datasets
- Tab filters work on a copy of the data — never mutate the source array
