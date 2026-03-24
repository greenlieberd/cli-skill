---
name: spinners
description: Multi-phase spinners and labeled progress indicators for ANSI HUDs and Ink Wizards.
metadata:
  tags: spinners, progress, loading, feedback
---

# Spinners

> Platform: macOS (Terminal.app, iTerm2, Warp).

A spinner without a label tells the user nothing. A spinner that changes its label as phases complete tells them exactly what's happening. Every operation longer than 300ms deserves a spinner.

## Prerequisites

- ANSI escape constants defined (see `hud-screens.md`)
- For Ink Wizards: `ink-spinner` package (`bun add ink-spinner`)
- For ANSI HUDs: no external dependency — use the pattern in §1

---

## 1. ANSI HUD spinner — interval-based, labeled

```typescript
// src/spinner.ts
const FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

export class Spinner {
  private frame    = 0
  private interval: ReturnType<typeof setInterval> | null = null
  private label    = ''

  start(label: string): void {
    this.label = label
    this.frame = 0
    this.interval = setInterval(() => this.tick(), 80)
    this.tick()
  }

  update(label: string): void {
    this.label = label   // change label mid-spin without restarting
  }

  stop(finalLine?: string): void {
    if (this.interval) clearInterval(this.interval)
    this.interval = null
    process.stdout.write('\r\x1b[K')   // clear spinner line
    if (finalLine) process.stdout.write(finalLine + '\n')
  }

  private tick(): void {
    const char = FRAMES[this.frame % FRAMES.length]
    process.stdout.write(`\r  \x1b[36m${char}\x1b[0m  ${this.label}`)
    this.frame++
  }
}
```

Usage:
```typescript
const spinner = new Spinner()
spinner.start('Fetching Reddit…')
const results = await fetchReddit(query)
spinner.update('Summarizing with Claude…')
const summary = await summarize(results)
spinner.stop(`  \x1b[32m✓\x1b[0m  Done — ${results.length} items`)
```

---

## 2. Multi-phase spinner — label changes with each phase

For operations with known stages, pre-define the phases and advance through them:

```typescript
// Usage
const spinner = new Spinner()
const phases = [
  'Fetching Reddit posts…',
  'Fetching Hacker News…',
  'Running Claude analysis…',
  'Writing output file…',
]

for (const [i, phase] of phases.entries()) {
  spinner.start(phase)
  await runPhase(i)
  spinner.update(`${phase} done`)
  await new Promise(r => setTimeout(r, 100))  // brief pause so user sees completion
}
spinner.stop('  \x1b[32m✓\x1b[0m  All phases complete')
```

---

## 3. Ink Wizard spinner — ink-spinner + Text

```tsx
// cli/components/Loading.tsx
import { Text, Box } from 'ink'
import Spinner from 'ink-spinner'

interface Props {
  label: string
}

export function Loading({ label }: Props) {
  return (
    <Box>
      <Text color="cyan"><Spinner type="dots" /></Text>
      <Text>  {label}</Text>
    </Box>
  )
}
```

Use inside a step component when `isLoading` state is true:

```tsx
// cli/steps/GenerateStep.tsx
const [loading, setLoading] = useState(false)
const [label, setLabel]     = useState('')

if (loading) return <Loading label={label} />
```

---

## 4. Progress bar — for known totals

When you know the total count, a progress bar is more informative than a spinner:

```typescript
// src/spinner.ts
export function progressBar(done: number, total: number, width = 20): string {
  const pct   = Math.min(done / total, 1)
  const filled = Math.round(pct * width)
  const bar   = '█'.repeat(filled) + '░'.repeat(width - filled)
  return `[${bar}] ${done}/${total}`
}

// Output: [████████████░░░░░░░░] 12/20
```

Use inline with `\r` to update in place:
```typescript
for (let i = 0; i < items.length; i++) {
  process.stdout.write(`\r  ${progressBar(i + 1, items.length)}  `)
  await processItem(items[i])
}
process.stdout.write('\n')
```

---

## 5. Timing — when to show what

| Duration      | Show             |
|---------------|------------------|
| < 300ms       | Nothing           |
| 300ms–2s      | Spinner           |
| 2s–30s        | Spinner with label changes |
| > 30s or known total | Progress bar |

---

## Rules

- Every spinner has a label — never spin in silence
- Update the label as phases complete — users feel progress
- Always clear the spinner line on stop (`\r\x1b[K`)
- Never show a spinner for operations under 300ms — it flickers pointlessly
- Stop the interval on `SIGINT` / crash — otherwise it keeps printing after exit
