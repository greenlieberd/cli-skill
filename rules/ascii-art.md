---
name: ascii-art
description: ASCII block-letter logos and wordmarks for ANSI HUDs and Ink Wizards.
metadata:
  tags: ascii, logo, branding, identity, ansi
---

# ASCII Art

> Platform: macOS (Terminal.app, iTerm2, Warp).

ASCII art in CLIs has one job: establish identity on first launch. Done right it takes up exactly 6 lines, uses the tool's brand color, and disappears after a beat. Done wrong it burns 30 lines and appears on every screen.

## Prerequisites

- ANSI color constants defined (see `hud-screens.md`)
- Terminal width check in place: `Math.min(process.stdout.columns, 66)`

---

## 1. Format — 6-line block letters, no wider than 60 chars

Block letters at this size are readable, don't overflow on 80-col terminals, and compress to nothing on resize. Use single-character block chars, not full Unicode box-drawing.

```
  ██████╗ ██╗   ██╗██╗     ███████╗███████╗
  ██╔══██╗██║   ██║██║     ██╔════╝██╔════╝
  ██████╔╝██║   ██║██║     ███████╗█████╗
  ██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝
  ██║     ╚██████╔╝███████╗███████║███████╗
  ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝
```

Generate these with [Text to ASCII Art Generator](https://patorjk.com/software/taag/) — use **font: ANSI Shadow** for this style.

---

## 2. Where to show it — splash only

Show the logo exactly once: on the first HUD render, before the menu appears. Never show it on every screen redraw.

```typescript
// src/hud.ts
let splashShown = false

function drawScreen(state: State): void {
  clearScreen()
  if (!splashShown) {
    drawLogo()
    splashShown = true
  }
  drawMenu(state)
  drawFooter()
}
```

For Ink Wizards, show in the first step's render, not in Frame.tsx (which renders on every step).

---

## 3. Logo function — color + bounded width

```typescript
// src/hud.ts
const A = {
  gold:  '\x1b[38;5;214m',
  dim:   '\x1b[2m',
  reset: '\x1b[0m',
}

const LOGO_LINES = [
  '  ██████╗ ██╗   ██╗██╗     ███████╗███████╗',
  '  ██╔══██╗██║   ██║██║     ██╔════╝██╔════╝',
  '  ██████╔╝██║   ██║██║     ███████╗█████╗  ',
  '  ██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝  ',
  '  ██║     ╚██████╔╝███████╗███████║███████╗',
  '  ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝',
]

function drawLogo(): void {
  const cols = Math.min(process.stdout.columns, 66)
  if (cols < 48) return   // too narrow — skip logo entirely
  for (const line of LOGO_LINES) {
    process.stdout.write(`${A.gold}${line}${A.reset}\n`)
  }
  process.stdout.write('\n')
}
```

---

## 4. Ink Wizard — show as static text in step 0

```tsx
// cli/components/Logo.tsx
import { Text, Box } from 'ink'

const LOGO = [
  '  ██████╗ ██╗   ██╗██╗     ███████╗███████╗',
  '  ██╔══██╗██║   ██║██║     ██╔════╝██╔════╝',
  '  ██████╔╝██║   ██║██║     ███████╗█████╗  ',
  '  ██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝  ',
  '  ██║     ╚██████╔╝███████╗███████║███████╗',
  '  ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝',
]

export function Logo() {
  return (
    <Box flexDirection="column" marginBottom={1}>
      {LOGO.map((line, i) => (
        <Text key={i} color="yellowBright">{line}</Text>
      ))}
    </Box>
  )
}
```

---

## 5. Minimal alternative — wordmark in single line

For tools where a full block logo is too heavy, use a single styled wordmark:

```typescript
function drawWordmark(name: string, tagline: string): void {
  const cols = Math.min(process.stdout.columns, 66)
  const pad  = '  '
  process.stdout.write(`\n${pad}${A.gold}${A.bold}${name}${A.reset}  ${A.dim}${tagline}${A.reset}\n\n`)
}
// Usage:
drawWordmark('PULSE', 'daily PM intelligence')
```

---

## Rules

- Logo shows once per session, not on every redraw
- If terminal width < 48, skip the logo entirely — never wrap it
- Use the tool's single brand color, not a rainbow
- Never animate the logo — it delays perceived startup
- 6 lines max — more than that wastes screen space
