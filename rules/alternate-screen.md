---
name: alternate-screen
description: Full-screen buffer — entering the alternate screen, restoring on exit, and when to use it versus clearScreen.
metadata:
  tags: alternate-screen, fullscreen, buffer, terminal, ansi
---

# Alternate Screen

> Platform: macOS (Terminal.app, iTerm2, Warp — all support the alternate screen buffer).

The alternate screen buffer is a separate canvas. When you enter it, the user's previous terminal output disappears. When you exit, it's fully restored — as if your app was never there. This is what tools like `vim`, `less`, and `htop` use.

Use alternate screen for full-screen UIs. Use `clearScreen()` for simple apps that don't need to fully hide the previous terminal history.

## Prerequisites

- Raw mode for ANSI HUDs (see `hud-screens.md`)
- `restoreTerminal()` from `error-recovery.md` must also exit the alternate screen
- Always restore on SIGINT / uncaught exception — never leave the user stuck in the buffer

---

## 1. Enter and exit

```typescript
// src/hud.ts
function enterFullScreen(): void {
  process.stdout.write('\x1b[?1049h')   // switch to alternate screen buffer
  process.stdout.write('\x1b[2J')       // clear the buffer
  process.stdout.write('\x1b[H')        // cursor home
  process.stdout.write('\x1b[?25l')     // hide cursor
}

function exitFullScreen(): void {
  process.stdout.write('\x1b[?25h')     // restore cursor
  process.stdout.write('\x1b[?1049l')   // switch back to normal screen buffer
}
```

Always pair them — an unclosed `\x1b[?1049h` leaves the terminal in alternate screen after exit, which is very disorienting.

---

## 2. Register exit handlers before entering

```typescript
// src/hud.ts
export function runHud(): void {
  // Register cleanup BEFORE entering full screen
  process.on('exit',   exitFullScreen)
  process.on('SIGINT', () => { exitFullScreen(); process.exit(0) })
  process.on('SIGTERM',() => { exitFullScreen(); process.exit(0) })
  process.on('uncaughtException', (err) => {
    exitFullScreen()
    logError('uncaughtException', err)
    process.stderr.write(`  ✗  ${err.message}\n`)
    process.exit(1)
  })

  // Now safe to enter
  enterFullScreen()
  if (process.stdin.isTTY) {
    process.stdin.setRawMode(true)
    process.stdin.resume()
  }

  render()
  startInputLoop()
}
```

---

## 3. Redraw on resize — SIGWINCH

When in alternate screen, terminal resize doesn't reflow — you must redraw:

```typescript
process.stdout.on('resize', () => {
  process.stdout.write('\x1b[2J\x1b[H')   // clear + cursor home
  render()
})
```

---

## 4. When to use alternate screen vs clearScreen

| Use alternate screen | Use clearScreen |
|---------------------|-----------------|
| Full-screen table, HUD, crawl monitor | Simple spinner + progress |
| User returns to their terminal history after exit | App output should stay visible after exit |
| `vim`/`less`/`htop` style experience | Run once, leave output in scroll buffer |
| Long-lived interactive session | Short-lived command |

`clearScreen()` (just `\x1b[2J\x1b[H`) is simpler and leaves output in the scroll buffer. Use it for most Propane CLIs. Alternate screen is for tools where a full-screen UI is the primary experience (byline's CrawlTable, vim-style navigation).

---

## 5. Checking support

Alternate screen is supported on macOS Terminal, iTerm2, Warp, tmux, and screen. Always check:

```typescript
const SUPPORTS_ALTERNATE = process.stdout.isTTY && !process.env.NO_COLOR
```

If not a TTY (piped output), fall back to plain text — no screen manipulation at all.

---

## 6. Ink + alternate screen

Ink v5 automatically uses the alternate screen buffer when running. You don't need to manage it manually in Ink components — just ensure your `unmount()` cleanup is registered:

```typescript
import { render } from 'ink'
import { createElement } from 'react'
import { App } from './cli/App.tsx'

const { unmount, waitUntilExit } = render(createElement(App))

process.on('SIGINT', () => { unmount(); process.exit(0) })
await waitUntilExit()
```

---

## Rules

- Register all exit handlers (exit, SIGINT, SIGTERM, uncaughtException) before `enterFullScreen()`
- Always call `exitFullScreen()` before `process.exit()` — never leave the user in the buffer
- Redraw on `process.stdout.on('resize')` — resize doesn't reflow alternate screen content
- Use alternate screen only for full-screen UIs — most CLIs should use `clearScreen()` instead
- Check `process.stdout.isTTY` before entering — fall back to plain output when piped
