---
name: notifications
description: macOS OS notifications from CLI tools using osascript and terminal-notifier, with do-not-disturb awareness.
metadata:
  tags: notifications, macos, osascript, alert, system
---

# Notifications

> Platform: macOS only — uses `osascript` (built-in) or `terminal-notifier` (optional, richer).

A notification is the right choice when a long-running operation finishes and the user has likely switched away from the terminal. Never notify for operations under 30 seconds — that's what the display system is for.

## Prerequisites

- macOS (notifications are macOS-only; skip silently on other platforms)
- `osascript` is built into macOS — no install needed
- `terminal-notifier` is optional but gives richer notifications: `brew install terminal-notifier`

---

## 1. osascript — built-in, zero install

Use Bun.spawn() to call osascript:

```typescript
// src/notify.ts
export interface NotifyOptions {
  title:   string
  message: string
  sound?:  boolean   // default: false
}

export async function notify(opts: NotifyOptions): Promise<void> {
  if (process.platform !== 'darwin') return
  if (process.env.NO_NOTIFY === '1') return

  const { title, message } = opts
  const script = `display notification "${message.replace(/"/g, '\\"')}" with title "${title.replace(/"/g, '\\"')}"`

  const proc = Bun.spawn(['osascript', '-e', script], { stdout: 'ignore', stderr: 'ignore' })
  await proc.exited
}
```

Usage:
```typescript
await notify({ title: 'Pulse', message: 'Report ready — 12 items processed' })
```

---

## 2. terminal-notifier — richer, with click-to-open

If `terminal-notifier` is installed, it supports subtitles and clicking to open a file:

```typescript
// src/notify.ts
async function hasTerminalNotifier(): Promise<boolean> {
  try {
    const proc = Bun.spawn(['which', 'terminal-notifier'], { stdout: 'ignore', stderr: 'ignore' })
    return (await proc.exited) === 0
  } catch { return false }
}

export async function notifyRich(opts: NotifyOptions & {
  subtitle?: string
  open?: string   // file path or URL to open on click
}): Promise<void> {
  if (process.platform !== 'darwin') return
  if (process.env.NO_NOTIFY === '1') return

  const { title, message, subtitle, open } = opts

  if (await hasTerminalNotifier()) {
    const args = ['-title', title, '-message', message]
    if (subtitle) args.push('-subtitle', subtitle)
    if (open)     args.push('-open', `file://${open}`)
    const proc = Bun.spawn(['terminal-notifier', ...args], { stdout: 'ignore', stderr: 'ignore' })
    await proc.exited
  } else {
    await notify(opts)   // fallback to osascript
  }
}
```

Usage:
```typescript
await notifyRich({
  title:    'Pulse',
  subtitle: 'Report complete',
  message:  `${results.length} sources · ${formatCost(cost)}`,
  open:     outputPath,   // click notification to open the file
})
```

---

## 3. When to notify

```typescript
// src/commands/run.ts
const start  = Date.now()
const result = await runPipeline()
const elapsed = Date.now() - start

// Only notify if the run took more than 30 seconds (user likely switched away)
if (elapsed > 30_000) {
  await notifyRich({
    title:   'My Tool',
    message: `Done — ${result.itemCount} items in ${Math.round(elapsed / 1000)}s`,
    open:    result.outputPath,
  })
}
```

---

## 4. Opt-out via env var

Document `NO_NOTIFY` in `.env.example`:

```bash
# Disable OS notifications after long runs (optional)
# NO_NOTIFY=1
```

The `notify()` function already checks `process.env.NO_NOTIFY === '1'` and returns early.

---

## 5. Sound — use sparingly

```typescript
export async function notifyError(message: string): Promise<void> {
  // Use sound for errors only — draws attention across the room
  const script = `display notification "${message.replace(/"/g, '\\"')}" with title "Error" sound name "default"`
  const proc = Bun.spawn(['osascript', '-e', script], { stdout: 'ignore', stderr: 'ignore' })
  await proc.exited
}
```

Don't use sound for normal completion — it's intrusive. Reserve it for errors that require immediate attention.

---

## Rules

- Always check `process.platform === 'darwin'` — skip silently on other platforms
- Only notify after 30+ second operations — shorter runs don't need it
- Use `osascript` as base (zero install); offer `terminal-notifier` for click-to-open
- `open:` in terminal-notifier should point to the output file — the most useful action
- Respect `NO_NOTIFY=1` — document it in `.env.example`
- Sound only for errors, never for normal completions
