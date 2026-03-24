---
name: layouts
description: Terminal layout patterns — sidebar, split-pane, modal, pinned footer — and macOS constraints.
metadata:
  tags: layouts, sidebar, split-pane, modal, footer
---

# Layouts

> Platform: macOS (Terminal.app, iTerm2, Warp). Tested at 80–220 column widths.
>
> Terminal layout is constrained by what ANSI escape sequences and Ink's flexbox model support on macOS. This rule documents what's actually possible — not theoretical layouts.

---

## What's possible in a macOS terminal

The terminal is a grid of fixed-width characters. Layouts are built by:
1. **Printing characters at exact positions** using cursor movement (`\x1b[row;colH`)
2. **Using box-drawing characters** to draw borders (`─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼`)
3. **Using Ink's `Box` flexbox** for reactive layouts that handle wrapping

You cannot overlap elements (no z-index). You cannot use fonts or images in the terminal itself (only in terminal emulators that support sixel/iTerm2 inline images). Everything is monospace.

**Reliable terminal width:** assume 80 columns minimum. Target 66-column content areas with 2-column margins on each side. Support up to 220 columns by adapting, not hard-coding.

---

## Layout 1 — Sidebar + main content

Split the screen vertically: narrow left sidebar (menu/navigation), wide right content area.

```
┌─────────────┬───────────────────────────────────┐
│  Navigation │  Content                          │
│             │                                   │
│  ▶ Reports  │  2024-01-15 Daily Report          │
│    Sources  │  ─────────────────────────────    │
│    Settings │  Summary: 3 topics, 12 sources    │
│    Exit     │  ...                              │
│             │                                   │
└─────────────┴───────────────────────────────────┘
  hints line here
```

```typescript
const SIDEBAR_W = 16

function drawSidebarLayout(selected: number, content: string[]): void {
  const cols     = Math.min(process.stdout.columns ?? 80, 100)
  const mainW    = cols - SIDEBAR_W - 3  // 3 for borders + gap

  const menuItems = ['Reports', 'Sources', 'Settings', 'Exit']

  process.stdout.write('\x1b[2J\x1b[H')  // clear + home

  // Top border
  process.stdout.write(`┌${'─'.repeat(SIDEBAR_W)}┬${'─'.repeat(mainW)}┐\n`)

  // Rows
  const rows = Math.min(process.stdout.rows - 4, 20)
  for (let row = 0; row < rows; row++) {
    const menuLine = menuItems[row]
      ? `${row === selected ? '▶ ' : '  '}${menuItems[row]}`
      : ''
    const contentLine = content[row] ?? ''

    const sidebarCell = menuLine.slice(0, SIDEBAR_W).padEnd(SIDEBAR_W)
    const mainCell    = contentLine.slice(0, mainW).padEnd(mainW)

    process.stdout.write(`│${sidebarCell}│${mainCell}│\n`)
  }

  // Bottom border
  process.stdout.write(`└${'─'.repeat(SIDEBAR_W)}┴${'─'.repeat(mainW)}┘\n`)
  process.stdout.write(`  ${'\x1b[90m'}↑↓ navigate  ↵ select  ctrl+c exit\x1b[0m\n`)
}
```

**Resize handling:**
```typescript
process.stdout.on('resize', () => {
  drawSidebarLayout(selectedIdx, currentContent)
})
```

---

## Layout 2 — Full-width content with pinned status bar

Content scrolls in the upper area. Status and hints are always visible at the bottom.

```
  ██████╗ ██╗  ██╗                  ← ASCII art header (static)
  ──────────────────────────────
  2024-01-15 Daily Report           ← content area (scrolls/updates)
  Summary: ...
  Topics: ...
  ──────────────────────────────
  Running: Fetching Reddit...       ← status line (updates in place)
  ↑↓ navigate  ↵ select  ctrl+c   ← hint line (static)
```

```typescript
const HEADER_ROWS = 8   // ASCII art + divider
const FOOTER_ROWS = 2   // status + hints

function getContentRows(): number {
  return Math.max(5, (process.stdout.rows ?? 24) - HEADER_ROWS - FOOTER_ROWS)
}

function updateStatus(msg: string): void {
  const statusRow = (process.stdout.rows ?? 24) - FOOTER_ROWS + 1
  process.stdout.write(`\x1b[${statusRow};0H\x1b[2K  \x1b[90m${msg}\x1b[0m`)
}
```

---

## Layout 3 — Split pane (two content columns)

Side-by-side content, useful for comparisons (before/after, two sources).

```
┌───────────────────┬───────────────────┐
│  Before           │  After            │
│  ───────────────  │  ───────────────  │
│  Old content...   │  New content...   │
│                   │                   │
└───────────────────┴───────────────────┘
```

```typescript
function drawSplitPane(left: string[], right: string[]): void {
  const cols  = Math.min(process.stdout.columns ?? 80, 120)
  const half  = Math.floor((cols - 3) / 2)
  const rows  = Math.min(left.length, right.length, process.stdout.rows - 4)

  process.stdout.write('\x1b[2J\x1b[H')
  process.stdout.write(`┌${'─'.repeat(half)}┬${'─'.repeat(half)}┐\n`)

  for (let i = 0; i < rows; i++) {
    const l = (left[i]  ?? '').slice(0, half).padEnd(half)
    const r = (right[i] ?? '').slice(0, half).padEnd(half)
    process.stdout.write(`│${l}│${r}│\n`)
  }

  process.stdout.write(`└${'─'.repeat(half)}┴${'─'.repeat(half)}┘\n`)
}
```

Minimum terminal width for split pane: 60 columns (30 each side). Show a message if narrower:
```typescript
if ((process.stdout.columns ?? 80) < 60) {
  process.stdout.write('  Terminal too narrow for split view (need 60+ cols)\n')
  drawSingleColumn(left.concat(right))  // fallback to single column
  return
}
```

---

## Layout 4 — Modal overlay

A focused dialog that appears over the existing screen, used for confirmations.

```
                   ┌────────────────────────┐
                   │  Confirm               │
                   │                        │
                   │  Write 12 files to     │
                   │  my-tool/ ?            │
                   │                        │
                   │  [Yes]  [No]           │
                   └────────────────────────┘
```

```typescript
function drawModal(title: string, lines: string[], options: string[]): void {
  const cols   = Math.min(process.stdout.columns ?? 80, 80)
  const w      = Math.min(40, cols - 4)
  const left   = Math.floor((cols - w) / 2)
  const pad    = ' '.repeat(left)
  const inner  = w - 2

  process.stdout.write(`${pad}┌${'─'.repeat(inner)}┐\n`)
  process.stdout.write(`${pad}│  ${title.padEnd(inner - 2)}│\n`)
  process.stdout.write(`${pad}│${'─'.repeat(inner)}│\n`)
  lines.forEach(line => {
    process.stdout.write(`${pad}│  ${line.slice(0, inner - 2).padEnd(inner - 2)}│\n`)
  })
  process.stdout.write(`${pad}│${'─'.repeat(inner)}│\n`)
  const opts = options.map(o => `[${o}]`).join('  ')
  process.stdout.write(`${pad}│  ${opts.padEnd(inner - 2)}│\n`)
  process.stdout.write(`${pad}└${'─'.repeat(inner)}┘\n`)
}
```

---

## Ink layouts (Wizard-style)

Ink uses a flexbox model. This is more portable and handles wrapping automatically.

**Two-column in Ink:**
```tsx
<Box width={66}>
  <Box width={16} flexDirection="column" borderRight>
    {menuItems.map((item, i) => (
      <Text key={item} color={i === selected ? 'greenBright' : 'gray'}>
        {i === selected ? '▶ ' : '  '}{item}
      </Text>
    ))}
  </Box>
  <Box flex={1} flexDirection="column" paddingLeft={2}>
    {contentLines.map((line, i) => <Text key={i}>{line}</Text>)}
  </Box>
</Box>
```

**Pinned footer in Ink:**
```tsx
<Box flexDirection="column" height={process.stdout.rows}>
  <Box flex={1} flexDirection="column">
    {/* scrollable content */}
  </Box>
  <Box>
    <Text color="gray">↑↓ navigate   ↵ select   ctrl+c exit</Text>
  </Box>
</Box>
```

---

## Layout rules

**Always:**
- Check `process.stdout.columns` before drawing — never hardcode 80 or 66
- Register `process.stdout.on('resize', redraw)` for any fixed-layout HUD
- Truncate long text: `str.slice(0, maxWidth - 1)` — never let lines wrap unexpectedly
- Test at 80, 120, and 160 columns

**Never:**
- Absolute cursor positioning for content that might vary in length (use `\r\x1b[K` to overwrite a single line instead)
- Assume the terminal supports mouse events or sixel graphics — stick to keyboard + text
- Build layouts deeper than 2 columns — terminal text is linear; complex layouts break at narrow widths

**If the terminal is too narrow:**
```typescript
const MIN_WIDTH = 50
if ((process.stdout.columns ?? 80) < MIN_WIDTH) {
  process.stdout.write(`\x1b[2J\x1b[H  Terminal too narrow (${process.stdout.columns} cols).\n  Resize to ${MIN_WIDTH}+ columns.\n`)
  return
}
```
