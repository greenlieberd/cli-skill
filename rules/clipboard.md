---
name: clipboard
description: macOS clipboard integration — copying output to pbcopy, reading from pbpaste, and offering copy shortcuts in the HUD.
metadata:
  tags: clipboard, pbcopy, pbpaste, macos, copy
---

# Clipboard

> Platform: macOS only — uses `pbcopy` and `pbpaste` which are built into macOS.

The most useful thing a content-generation CLI can do after generating output is put it on the clipboard. No file to navigate to, no copy-paste from the terminal — one key copies the result and the user pastes it wherever they need it.

## Prerequisites

- macOS (pbcopy/pbpaste are not available on Linux/Windows)
- `src/colors.ts` with `A` constants (see `colors.md`)
- Bun's `Bun.spawn()` for subprocess calls

---

## 1. Copy to clipboard — pbcopy

```typescript
// src/clipboard.ts
import { spawnSync } from 'child_process'

export function copyToClipboard(text: string): boolean {
  if (process.platform !== 'darwin') return false
  try {
    const result = spawnSync('pbcopy', [], {
      input: text,
      encoding: 'utf8',
    })
    return result.status === 0
  } catch {
    return false
  }
}
```

Usage:
```typescript
const ok = copyToClipboard(generatedContent)
if (ok) process.stdout.write('  ✓  Copied to clipboard\n')
else    process.stdout.write('  –  Clipboard not available\n')
```

---

## 2. Read from clipboard — pbpaste

```typescript
// src/clipboard.ts
export function readFromClipboard(): string | null {
  if (process.platform !== 'darwin') return null
  try {
    const result = spawnSync('pbpaste', [], { encoding: 'utf8' })
    return result.status === 0 ? result.stdout ?? null : null
  } catch {
    return null
  }
}
```

Usage — paste clipboard content as input:
```typescript
if (key === 'v' && ctrlHeld) {
  const content = readFromClipboard()
  if (content) processInput(content)
}
```

---

## 3. HUD shortcut — 'c' to copy last result

After a generation run, offer `c` to copy the output:

```typescript
// src/hud.ts
let lastOutput: string | null = null

// After a run completes:
lastOutput = result.content

// In keypress handler:
if (key === 'c' && lastOutput) {
  const ok = copyToClipboard(lastOutput)
  showToast(ok ? '✓ Copied' : '✗ Failed to copy')
}

// Footer hints — only show when output is available:
function getFooterHints(): string[] {
  const hints = ['↑↓ navigate', '↵ select', '? help']
  if (lastOutput) hints.push('c copy')
  return hints
}
```

---

## 4. Toast notification — brief inline message

Show a brief confirmation that disappears after 2 seconds:

```typescript
// src/hud.ts
let toast: string | null = null
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(message: string): void {
  toast = message
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toast = null
    render()
  }, 2000)
  render()
}

function drawToast(): void {
  if (!toast) return
  process.stdout.write(`\n  ${A.info}${toast}${A.reset}\n`)
}
```

---

## 5. Copy formatted vs raw

Some tools need to copy both a formatted version (markdown) and a plain version (for pasting into a field):

```typescript
export type CopyFormat = 'markdown' | 'plain' | 'html'

export function copyAs(content: string, format: CopyFormat): boolean {
  const text = format === 'plain'
    ? content.replace(/[#*`_~\[\]]/g, '')   // strip markdown markers
    : content
  return copyToClipboard(text)
}

// In HUD:
if (key === 'c') copyAs(lastOutput, 'markdown')   // default: markdown
if (key === 'C') copyAs(lastOutput, 'plain')        // shift+C: plain text
```

---

## Rules

- Always check `process.platform === 'darwin'` — silently skip on non-macOS
- Show a toast after copy — the user needs to know it worked
- Only show 'c copy' in footer hints when there's actually something to copy
- `pbcopy` via `spawnSync` is synchronous and blocks briefly — fine for small strings; for large content use `Bun.spawn()` async
- Offer both markdown and plain text copy when the output has formatting
