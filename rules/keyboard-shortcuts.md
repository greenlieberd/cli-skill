---
name: keyboard-shortcuts
description: Keyboard shortcut design, help overlays, and discoverability patterns for CLI tools.
metadata:
  tags: keyboard, shortcuts, navigation, input, help
---

# Keyboard Shortcuts

> Platform: macOS (Terminal.app, iTerm2, Warp).

Good keyboard shortcuts are discovered, not memorized. Show them in context, not in a manual. The user should never need to leave the tool to find out what keys do.

## Prerequisites

- Raw mode enabled for ANSI HUDs: `process.stdin.setRawMode(true)` (see `hud-screens.md`)
- For Ink: `useInput` from Ink v5
- `error-recovery.md` — restore terminal on exit before registering shortcuts

---

## 1. Core navigation — non-negotiable

Every screen must support these:

```
↑ ↓         move selection
↵ / space   confirm / select
←           back (never ESC)
ctrl+c      exit from anywhere
?           toggle help overlay
```

Rationale:
- `←` for back matches web/file-navigation muscle memory; ESC is too far from home row
- `ctrl+c` must always exit — never intercept it
- `?` for help is universal in terminal tools (git, less, vim)

---

## 2. ANSI HUD — raw input handler

```typescript
// src/hud.ts
process.stdin.setRawMode(true)
process.stdin.resume()
process.stdin.setEncoding('utf8')

process.stdin.on('data', (key: string) => {
  // ctrl+c
  if (key === '\u0003') { restoreTerminal(); process.exit(0) }

  // arrows
  if (key === '\u001b[A') return onUp()
  if (key === '\u001b[B') return onDown()
  if (key === '\u001b[D') return onBack()

  // enter / space / return
  if (key === '\r' || key === ' ')  return onSelect()

  // shortcuts
  if (key === '?')  return toggleHelp()
  if (key === 'r')  return onRefresh()
  if (key === 'o')  return onOpen()
  if (key === 'e')  return onExport()
})
```

---

## 3. Ink — useInput handler

```tsx
// cli/App.tsx
import { useInput } from 'ink'

useInput((input, key) => {
  if (key.upArrow)    setIdx(i => Math.max(0, i - 1))
  if (key.downArrow)  setIdx(i => Math.min(items.length - 1, i + 1))
  if (key.leftArrow || key.backspace) onBack()
  if (key.return)     onSelect()
  if (input === '?')  setShowHelp(h => !h)
})
```

---

## 4. Footer hints — always visible

Show the three most relevant keys at the bottom of every screen. Never list more than five — it becomes noise.

```typescript
function drawFooter(hints: string[]): void {
  const cols  = Math.min(process.stdout.columns, 66)
  const line  = hints.map(h => `\x1b[2m${h}\x1b[0m`).join('   ')
  process.stdout.write(`\n  ${line}\n`)
}

// Home screen
drawFooter(['↑↓ navigate', '↵ select', '? help', 'ctrl+c exit'])

// Result screen (after content loads)
drawFooter(['↑↓ scroll', '← back', 'o open', 'e export'])
```

---

## 5. Help overlay — ? toggles it

A full-screen help overlay lists all shortcuts. It sits on top of the current screen and dismisses with any key.

```typescript
// src/hud.ts
let helpVisible = false

function toggleHelp(): void {
  helpVisible = !helpVisible
  redraw()
}

function drawHelp(): void {
  const shortcuts = [
    ['↑ / ↓',    'Move selection'],
    ['↵ / space', 'Confirm'],
    ['←',        'Back'],
    ['r',        'Refresh data'],
    ['o',        'Open output file'],
    ['e',        'Export to Markdown'],
    ['?',        'Toggle this help'],
    ['ctrl+c',   'Exit'],
  ]

  process.stdout.write('\n  \x1b[1mKeyboard shortcuts\x1b[0m\n\n')
  for (const [key, desc] of shortcuts) {
    process.stdout.write(`  \x1b[36m${key.padEnd(14)}\x1b[0m${desc}\n`)
  }
  process.stdout.write('\n  \x1b[2mPress any key to close\x1b[0m\n')
}

function redraw(): void {
  clearScreen()
  if (helpVisible) {
    drawHelp()
  } else {
    drawCurrentScreen()
  }
}
```

For Ink, render an overlay component:

```tsx
// cli/components/HelpOverlay.tsx
import { Box, Text } from 'ink'

const SHORTCUTS = [
  ['↑/↓',     'Move selection'],
  ['↵',       'Confirm'],
  ['←',       'Back'],
  ['?',       'Toggle help'],
  ['ctrl+c',  'Exit'],
]

export function HelpOverlay() {
  return (
    <Box flexDirection="column" borderStyle="round" borderColor="cyan" padding={1}>
      <Text bold>Keyboard shortcuts</Text>
      {SHORTCUTS.map(([key, desc]) => (
        <Box key={key}>
          <Text color="cyan">{key.padEnd(12)}</Text>
          <Text>{desc}</Text>
        </Box>
      ))}
      <Text dimColor>Press any key to close</Text>
    </Box>
  )
}
```

---

## 6. Shortcut design rules

- Use single lowercase letters for shortcuts: `r` refresh, `o` open, `e` export
- Never override `ctrl+c` — that's the universal "kill this process"
- Never use `q` for quit when `ctrl+c` is available — it conflicts with text input
- Avoid letter shortcuts that could collide with typed search input
- Show new shortcuts only when they're relevant (export hint appears only after content loads)

---

## Rules

- `ctrl+c` exits from every screen — no exceptions
- `←` for back, not ESC
- `?` opens help overlay on every screen
- Footer hints update per-screen — show what's relevant now, not everything ever
- Help overlay lists every shortcut; footer hints show only the 3–5 most used
