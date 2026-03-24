---
name: confirmation
description: y/n confirmation prompts for destructive actions, with color-coded warnings and safe defaults.
metadata:
  tags: confirmation, prompt, destructive, readline, ux
---

# Confirmation

> Platform: macOS (Terminal.app, iTerm2, Warp).

A single misplaced keypress shouldn't delete data or overwrite files. Destructive actions get a confirmation prompt — one line, color-coded, with a safe default of "no."

## Prerequisites

- `src/colors.ts` with `A` constants (see `colors.md`)
- For ANSI HUDs: temporarily exit raw mode to use readline for the prompt

---

## 1. Simple y/n prompt — readline

```typescript
// src/confirm.ts
import { createInterface } from 'readline'

export async function confirm(message: string, defaultYes = false): Promise<boolean> {
  const hint = defaultYes ? '[Y/n]' : '[y/N]'

  const rl  = createInterface({ input: process.stdin, output: process.stdout })
  const ask = (): Promise<string> =>
    new Promise(resolve => rl.question(`  \x1b[33m⚠\x1b[0m  ${message} \x1b[2m${hint}\x1b[0m  `, resolve))

  const answer = (await ask()).trim().toLowerCase()
  rl.close()

  if (answer === '') return defaultYes
  return answer === 'y' || answer === 'yes'
}
```

Usage:
```typescript
const ok = await confirm('Delete all cached data?')
if (!ok) { process.stdout.write('  –  Cancelled\n'); return }
clearCache()
process.stdout.write('  ✓  Cache cleared\n')
```

Output:
```
  ⚠  Delete all cached data? [y/N]  _
```

---

## 2. Destructive action pattern — color + consequence

For actions with significant consequences, show what will happen before asking:

```typescript
export async function confirmDestructive(
  action: string,
  consequence: string
): Promise<boolean> {
  process.stdout.write(`\n  \x1b[31m✗  ${action}\x1b[0m\n`)
  process.stdout.write(`  \x1b[2m${consequence}\x1b[0m\n\n`)
  return confirm('Are you sure?', false)   // default: no
}
```

Usage:
```typescript
const ok = await confirmDestructive(
  'Reset all configuration',
  'This will delete .env and all stored data in .propane/'
)
```

Output:
```
  ✗  Reset all configuration
  This will delete .env and all stored data in .propane/

  ⚠  Are you sure? [y/N]  _
```

---

## 3. In ANSI HUD — exit raw mode for the prompt

ANSI HUDs use raw mode, which intercepts all keypresses. To use readline for confirmation, temporarily exit raw mode:

```typescript
// src/hud.ts
async function confirmInHud(message: string): Promise<boolean> {
  // Exit raw mode
  process.stdin.setRawMode(false)

  const result = await confirm(message)

  // Restore raw mode and redraw
  process.stdin.setRawMode(true)
  render()

  return result
}

// In keypress handler:
if (key === 'D') {   // 'D' for destructive delete
  const ok = await confirmInHud('Delete selected item?')
  if (ok) deleteSelectedItem()
}
```

---

## 4. Multi-word confirmation for high-stakes actions

For truly irreversible actions (deleting a year of data, overwriting production config), require typing a specific phrase:

```typescript
export async function confirmTyped(
  phrase: string,
  consequence: string
): Promise<boolean> {
  process.stdout.write(`\n  \x1b[31m⚠  Irreversible action\x1b[0m\n`)
  process.stdout.write(`  ${consequence}\n\n`)
  process.stdout.write(`  Type "\x1b[1m${phrase}\x1b[0m" to confirm, or press Enter to cancel:\n`)

  const rl     = createInterface({ input: process.stdin, output: process.stdout })
  const answer = await new Promise<string>(r => rl.question('  → ', r))
  rl.close()

  return answer.trim() === phrase
}

// Usage:
const ok = await confirmTyped('delete everything', 'All output files and cached data will be removed.')
```

---

## 5. Keyboard shortcut confirmation in HUD

For actions triggered by a single key (like `d` for delete), show a confirmation inline without readline:

```typescript
// src/hud.ts
let pendingConfirm: { message: string; onYes: () => void } | null = null

function drawConfirmBanner(): void {
  if (!pendingConfirm) return
  process.stdout.write(
    `\n  \x1b[33m⚠\x1b[0m  ${pendingConfirm.message}  ` +
    `\x1b[32m[y]\x1b[0m confirm   \x1b[2m[any] cancel\x1b[0m`
  )
}

// In keypress handler:
if (pendingConfirm) {
  if (key === 'y') { pendingConfirm.onYes(); pendingConfirm = null }
  else             { pendingConfirm = null }
  render()
  return
}

// Trigger confirmation:
if (key === 'd') {
  pendingConfirm = { message: 'Delete selected?', onYes: deleteSelected }
  render()
}
```

---

## Rules

- Default is always "no" for destructive actions — users must explicitly choose yes
- Show the consequence before asking, not just the action name
- Exit raw mode before readline in ANSI HUDs — restore it after
- High-stakes actions require typing a phrase, not just `y`
- Single-key HUD confirmation uses a pending state — no readline needed
