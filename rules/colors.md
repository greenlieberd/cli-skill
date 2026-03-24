---
name: colors
description: ANSI color system — the A helper object, semantic palette, 256-color support, and consistency rules.
metadata:
  tags: colors, ansi, terminal, palette, styling
---

# Colors

> Platform: macOS (Terminal.app, iTerm2, Warp — all support 256-color and truecolor).

Every CLI should define its color system once and reference it everywhere. Ad hoc `\x1b[32m` strings scattered across files make palette changes painful and inconsistent.

## Prerequisites

- No external dependencies — ANSI escape codes are built into every macOS terminal
- For Ink Wizards: use Ink's `color` prop instead (see §4) — never raw escapes inside JSX

---

## 1. The A object — define once, import everywhere

Create a single `src/colors.ts` that exports all escape sequences as named constants:

```typescript
// src/colors.ts
export const A = {
  // ── Text styles ──────────────────────────────────────────────
  reset:    '\x1b[0m',
  bold:     '\x1b[1m',
  dim:      '\x1b[2m',
  italic:   '\x1b[3m',

  // ── Semantic colors (use these, not raw colors) ───────────────
  success:  '\x1b[32m',      // green  — ✓ done, confirmed
  error:    '\x1b[31m',      // red    — ✗ failed, missing
  warning:  '\x1b[33m',      // yellow — ⚠ retrying, optional
  info:     '\x1b[36m',      // cyan   — headers, labels, spinners
  muted:    '\x1b[2m',       // dim    — secondary info, hints

  // ── Brand color (tool-specific — pick one) ───────────────────
  brand:    '\x1b[38;5;214m', // amber/gold — for logo + accents

  // ── Reset alias (for readability in templates) ────────────────
  end:      '\x1b[0m',
} as const

// Helpers — wrap a string in a color and always reset
export const c = {
  success: (s: string) => `${A.success}${s}${A.reset}`,
  error:   (s: string) => `${A.error}${s}${A.reset}`,
  warning: (s: string) => `${A.warning}${s}${A.reset}`,
  info:    (s: string) => `${A.info}${s}${A.reset}`,
  muted:   (s: string) => `${A.muted}${s}${A.reset}`,
  bold:    (s: string) => `${A.bold}${s}${A.reset}`,
  dim:     (s: string) => `${A.dim}${s}${A.reset}`,
  brand:   (s: string) => `${A.brand}${s}${A.reset}`,
}
```

Usage:
```typescript
import { c } from './colors.ts'

process.stdout.write(`  ${c.success('✓')}  ${c.muted('Reddit')}  12 results\n`)
process.stdout.write(`  ${c.error('✗')}  ${c.muted('Twitter')}  API key missing\n`)
```

---

## 2. Semantic palette — what each color means

Use colors semantically, not decoratively:

| Color | Use for | Don't use for |
|-------|---------|---------------|
| `success` (green) | ✓ completed, saved, confirmed | Headers, accents |
| `error` (red) | ✗ failed, missing keys, crashes | Warnings |
| `warning` (yellow) | ⚠ retrying, optional, slow | Errors |
| `info` (cyan) | Section headers, labels, spinners | Body text |
| `muted` (dim) | Secondary info, hints, timestamps | Primary content |
| `brand` | Logo, tool name, one key accent | Everything else |

---

## 3. 256-color and truecolor

macOS Terminal, iTerm2, and Warp all support 256-color (`\x1b[38;5;Nm`) and truecolor (`\x1b[38;2;R;G;Bm`). Use these for the brand color only — stick to the 16 standard colors for semantic meanings, which survive light/dark mode and color-blindness better.

```typescript
// 256-color — good for brand accents (pick one at setup)
'\x1b[38;5;214m'  // amber/gold
'\x1b[38;5;39m'   // electric blue
'\x1b[38;5;135m'  // purple
'\x1b[38;5;208m'  // orange

// Truecolor — use only when exact hex match matters
'\x1b[38;2;255;165;0m'  // #FFA500 orange
```

Check support:
```typescript
const supportsTruecolor = process.env.COLORTERM === 'truecolor'
```

---

## 4. Ink — use color prop, not escape codes

Inside Ink components, never use raw ANSI escapes. Use Ink's `color` and `dimColor` props:

```tsx
import { Text, Box } from 'ink'

// These named colors map to the standard 16 terminal colors
<Text color="green">✓  Done</Text>
<Text color="red">✗  Failed</Text>
<Text color="yellow">⚠  Retrying</Text>
<Text color="cyan">→  {label}</Text>
<Text dimColor>Press ? for help</Text>

// For 256-color/hex (Ink v5+):
<Text color="#FFA500">brand text</Text>
```

---

## 5. Disabling color — respect NO_COLOR

Some users pipe output to files or run in environments without color support. Respect the `NO_COLOR` convention:

```typescript
// src/colors.ts — add at the top
const USE_COLOR = !process.env.NO_COLOR && process.stdout.isTTY

// Updated A object
export const A = USE_COLOR ? {
  reset:   '\x1b[0m',
  bold:    '\x1b[1m',
  // ... rest of colors
} : Object.fromEntries(
  Object.keys({ reset: '', bold: '', dim: '', italic: '', success: '', error: '', warning: '', info: '', muted: '', brand: '', end: '' })
    .map(k => [k, ''])
) as typeof A_WITH_COLOR
```

---

## 6. Status icons — pair with semantic colors

Use consistent icon–color pairings across all output:

```typescript
export const ICONS = {
  done:    `${A.success}✓${A.reset}`,
  fail:    `${A.error}✗${A.reset}`,
  warn:    `${A.warning}⚠${A.reset}`,
  skip:    `${A.muted}–${A.reset}`,
  run:     `${A.info}→${A.reset}`,
  wait:    `${A.muted}○${A.reset}`,
  update:  `${A.warning}↑${A.reset}`,
}

// Output line pattern: icon + label padded to 24 + detail dimmed
export function statusLine(icon: string, label: string, detail: string): string {
  return `  ${icon}  ${label.padEnd(24)}${A.dim}${detail}${A.reset}\n`
}
```

---

## Rules

- Define all colors in `src/colors.ts` — never inline `\x1b[32m` elsewhere
- Use semantic names (`success`, `error`) not color names (`green`, `red`) at call sites
- One brand color per tool — use it for logo and one accent only
- Ink components: use `color` prop, not escape codes
- Respect `NO_COLOR` env var when piping output
