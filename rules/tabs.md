---
name: tabs
description: Tab navigation in ANSI HUDs — tab bar rendering, ◄ ► switching, count badges, active underline.
metadata:
  tags: tabs, navigation, hud, filter, ansi
---

# Tabs

> Platform: macOS (Terminal.app, iTerm2, Warp).

Tabs let a single HUD screen show filtered views of the same data: All / Running / Done / Failed. They're more space-efficient than a separate menu screen and keep context visible as users switch.

## Prerequisites

- ANSI HUD with raw mode enabled (see `hud-screens.md`)
- `src/colors.ts` with `A` constants (see `colors.md`)
- Terminal width bounded: `Math.min(process.stdout.columns, 88)`

---

## 1. Tab state

```typescript
// src/hud.ts
const TABS = ['All', 'Running', 'Done', 'Failed'] as const
type Tab = typeof TABS[number]

let activeTab  = 0   // index into TABS
let tabScroll  = 0   // scroll offset within the active tab's rows

// Navigate tabs with ← →
if (key === '\x1b[C') { activeTab = (activeTab + 1) % TABS.length; tabScroll = 0 }
if (key === '\x1b[D') { activeTab = (activeTab - 1 + TABS.length) % TABS.length; tabScroll = 0 }

// Scroll rows within the active tab
if (key === '\x1b[A') tabScroll = Math.max(0, tabScroll - 1)
if (key === '\x1b[B') tabScroll++
```

Reset `tabScroll = 0` when switching tabs — the user shouldn't arrive mid-scroll in a new tab.

---

## 2. Tab bar rendering — count badges + active indicator

```typescript
function drawTabBar(counts: Record<Tab, number>): string {
  const tabs = TABS.map((t, i) => {
    const label = `${t} ${counts[t]}`
    return i === activeTab
      ? `\x1b[1;48;5;238m ${label} \x1b[0m`   // bold + dark grey background
      : `\x1b[2m ${label} \x1b[0m`            // dim
  })

  return '  ' + tabs.join('  \x1b[2m│\x1b[0m  ')
}

function drawTabUnderline(counts: Record<Tab, number>): string {
  const underlines = TABS.map((t, i) => {
    const w = `${t} ${counts[t]}`.length + 2   // +2 for spaces around label
    return i === activeTab
      ? `\x1b[36m${'─'.repeat(w)}\x1b[0m`
      : ' '.repeat(w)
  })
  return '  ' + underlines.join('     ')       // '     ' matches '  │  ' width
}
```

Output:
```
  All 12   Running 3 │  Done 8 │  Failed 1
  ──────
```

---

## 3. Filtering rows — never mutate source data

```typescript
function getTabRows(allRows: RowData[]): RowData[] {
  const tab = TABS[activeTab]
  switch (tab) {
    case 'All':     return allRows
    case 'Running': return allRows.filter(r => r.status === 'running')
    case 'Done':    return allRows.filter(r => r.status === 'done')
    case 'Failed':  return allRows.filter(r => r.status === 'failed')
  }
}

function getTabCounts(allRows: RowData[]): Record<Tab, number> {
  return {
    All:     allRows.length,
    Running: allRows.filter(r => r.status === 'running').length,
    Done:    allRows.filter(r => r.status === 'done').length,
    Failed:  allRows.filter(r => r.status === 'failed').length,
  }
}
```

---

## 4. Full render with tabs + scrollable rows

```typescript
function render(): void {
  const counts  = getTabCounts(rows)
  const visible = getTabRows(rows)
  const height  = Math.max(5, (process.stdout.rows ?? 30) - 10)
  const maxScroll = Math.max(0, visible.length - height)
  tabScroll = Math.min(tabScroll, maxScroll)
  const page  = visible.slice(tabScroll, tabScroll + height)
  const below = visible.length - tabScroll - height

  const out: string[] = ['\x1b[H']   // cursor home
  out.push(drawTabBar(counts))
  out.push(drawTabUnderline(counts))
  out.push(`  \x1b[2m◄ ► switch tabs   ↑↓ scroll   ? help\x1b[0m`)
  out.push('')

  for (const row of page) {
    out.push(dataRow(row))
  }

  out.push(below > 0 ? `  \x1b[2m↓ ${below} more\x1b[0m\x1b[K` : '\x1b[K')
  out.push('\x1b[K')   // ensure last line is cleared

  process.stdout.write(out.join('\n'))
}
```

---

## 5. Ink Wizard — tab equivalent with segmented control

For Ink Wizards, render tabs as a segmented control since Ink manages layout:

```tsx
// cli/components/TabBar.tsx
import { Box, Text } from 'ink'

interface Props {
  tabs:   readonly string[]
  active: number
  counts: number[]
}

export function TabBar({ tabs, active, counts }: Props) {
  return (
    <Box gap={2}>
      {tabs.map((tab, i) => (
        <Box key={tab}>
          {i === active ? (
            <Text bold underline color="cyan">{tab} {counts[i]}</Text>
          ) : (
            <Text dimColor>{tab} {counts[i]}</Text>
          )}
        </Box>
      ))}
    </Box>
  )
}
```

---

## Rules

- Reset `tabScroll = 0` when switching tabs — never carry scroll offset across tabs
- Count badges update live as rows change status — recalculate on every render
- `◄ ►` for tabs, `↑↓` for rows within a tab — always show both in footer hints
- Filter on a copy of the data — never mutate the source array based on active tab
- Tab labels: short, title-case, <= 8 chars (All, Running, Done, Failed, Errors, Queued)
