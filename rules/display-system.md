---
name: display-system
description: Encapsulated display class for CLI runs — spin/update/done/skip/fail/section/summary with elapsed time and cost.
metadata:
  tags: display, output, run, progress, summary
---

# Display System

> Platform: macOS (Terminal.app, iTerm2, Warp).

Ad hoc `process.stdout.write()` calls scattered through a run produce inconsistent output. An encapsulated display class centralizes all output: one place to change formatting, one place to accumulate stats, one method to print the final summary. All output goes through it — no direct console calls anywhere else.

## Prerequisites

- `src/colors.ts` with `A` constants and `c` helpers (see `colors.md`)
- `src/models.ts` with `MODEL_PRICING` (see `token-spend.md`)
- Run this class once per pipeline run — instantiate in the command handler, not globally

---

## 1. The Display class

```typescript
// src/display.ts
import { A } from './colors.ts'
import { estimateCost, formatCost, MODELS } from './models.ts'

const FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

export interface RunStats {
  sources: { active: number; skipped: number; errors: number }
  inputTokens:  number
  outputTokens: number
  model:        string
}

export class Display {
  private spinTimer:   ReturnType<typeof setInterval> | null = null
  private spinFrame  = 0
  private spinMsg    = ''
  private isSpinning = false
  private startTime  = Date.now()

  readonly stats: RunStats = {
    sources:      { active: 0, skipped: 0, errors: 0 },
    inputTokens:  0,
    outputTokens: 0,
    model:        MODELS.smart,
  }

  // ── Lifecycle ────────────────────────────────────────────────────────────────

  header(title: string): void {
    process.stdout.write(`\n  ${A.bold}${title}${A.reset}  ${A.dim}${new Date().toLocaleDateString()}${A.reset}\n\n`)
  }

  // ── Spinner ──────────────────────────────────────────────────────────────────

  spin(message: string): void {
    this.spinMsg = message
    if (this.isSpinning) return
    this.isSpinning = true
    process.stdout.write('\x1b[?25l')   // hide cursor
    this.spinTimer = setInterval(() => {
      const f = FRAMES[this.spinFrame++ % FRAMES.length]
      process.stdout.write(`\r  ${A.dim}${f}${A.reset}  ${this.spinMsg}${A.dim}…${A.reset}   `)
    }, 80)
  }

  update(message: string): void {
    this.spinMsg = message   // update without restarting
  }

  // ── Completion lines ──────────────────────────────────────────────────────────

  done(label: string, detail: string): void {
    this.printLine(`  ${A.success}✓${A.reset}  ${label.padEnd(24)}${A.dim}${detail}${A.reset}`)
    this.stats.sources.active++
  }

  skip(label: string, detail: string): void {
    this.printLine(`  ${A.dim}–  ${label.padEnd(24)}${detail}${A.reset}`)
    this.stats.sources.skipped++
  }

  fail(label: string, detail: string): void {
    this.printLine(`  ${A.error}✗${A.reset}  ${label.padEnd(24)}${A.dim}${detail}${A.reset}`)
    this.stats.sources.errors++
  }

  // ── Phase separators ─────────────────────────────────────────────────────────

  section(label: string): void {
    this.stop()
    process.stdout.write(`\n  ${A.dim}${label}${A.reset}\n\n`)
  }

  // ── Token tracking ────────────────────────────────────────────────────────────

  trackTokens(input: number, output: number): void {
    this.stats.inputTokens  += input
    this.stats.outputTokens += output
  }

  // ── Summary ──────────────────────────────────────────────────────────────────

  summary(outputPath?: string): void {
    this.stop()

    const elapsed = Math.round((Date.now() - this.startTime) / 1000)
    const dur     = elapsed >= 60
      ? `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`
      : `${elapsed}s`

    const sep   = `  ${A.dim}${'─'.repeat(48)}${A.reset}`
    const lines: string[] = ['', sep, `  ${A.bold}Done${A.reset}  ${A.dim}·  ${dur}${A.reset}`, '']

    const total  = this.stats.inputTokens + this.stats.outputTokens
    const cost   = estimateCost(this.stats.model, this.stats.inputTokens, this.stats.outputTokens)
    const { active, skipped, errors } = this.stats.sources

    if (total > 0) {
      lines.push(`  ${A.dim}Tokens   ${A.reset}   ${A.bold}${total.toLocaleString()}${A.reset}  ${A.dim}(${this.stats.inputTokens.toLocaleString()} in · ${this.stats.outputTokens.toLocaleString()} out)${A.reset}`)
    }
    if (cost > 0) {
      lines.push(`  ${A.dim}Cost ≈   ${A.reset}   ${A.bold}${formatCost(cost)}${A.reset}`)
    }
    if (active + skipped + errors > 0) {
      const parts: string[] = []
      if (active > 0)  parts.push(`${A.bold}${active}${A.reset} active`)
      if (skipped > 0) parts.push(`${A.dim}${skipped} skipped${A.reset}`)
      if (errors > 0)  parts.push(`${A.error}${errors} errors${A.reset}`)
      lines.push(`  ${A.dim}Sources  ${A.reset}   ${parts.join(`  ${A.dim}·${A.reset}  `)}`)
    }

    if (outputPath) {
      lines.push('')
      lines.push(`  ${A.dim}Saved →  ${A.reset}   ${outputPath}`)
    }

    lines.push(sep, '')
    process.stdout.write(lines.join('\n') + '\n')
  }

  // ── Internal ─────────────────────────────────────────────────────────────────

  stop(): void {
    if (this.spinTimer) clearInterval(this.spinTimer)
    this.spinTimer   = null
    this.isSpinning  = false
    process.stdout.write('\r\x1b[2K')   // clear spinner line
    process.stdout.write('\x1b[?25h')   // restore cursor
  }

  // Pause spinner, print line, restart — safe during parallel completions
  private printLine(line: string): void {
    const wasSpinning = this.isSpinning
    const prevMsg     = this.spinMsg
    this.stop()
    process.stdout.write(line + '\n')
    if (wasSpinning) this.spin(prevMsg)
  }
}
```

---

## 2. Usage in a command handler

```typescript
// src/commands/run.ts
import { Display } from '../display.ts'

export async function cmdRun(): Promise<void> {
  const display = new Display()
  display.header('My Tool')

  display.spin('Fetching Reddit…')
  const reddit = await runRedditSource(config)
  if (reddit.error)   display.fail('Reddit', reddit.error)
  else if (reddit.skipped) display.skip('Reddit', 'no API key')
  else                display.done('Reddit', `${reddit.links?.length ?? 0} posts`)

  display.section('Synthesizing…')
  display.spin('Running Claude analysis…')
  const result = await synthesize([reddit], config)
  display.trackTokens(result.inputTokens, result.outputTokens)

  const outputPath = await writeOutput('reddit-analysis', 'md', result.content)
  display.summary(outputPath)
}
```

---

## 3. Sample output

```
  My Tool  03/24/2026

  ⠼  Fetching Reddit…
  ✓  Reddit                  12 posts
  –  Twitter                 no API key

  Synthesizing…

  ⠋  Running Claude analysis…

  ────────────────────────────────────────────────
  Done  ·  4s

  Tokens     2,341  (1,890 in · 451 out)
  Cost ≈     $0.043
  Sources    1 active  ·  1 skipped

  Saved →    output/2026-03-24-reddit-analysis.md
  ────────────────────────────────────────────────
```

---

## Rules

- One `Display` instance per run — instantiate fresh each time
- All output goes through the Display — no `console.log` or raw `process.stdout.write` in command handlers
- `printLine()` handles the spinner-pause-print-resume cycle — never call `stop()` just to print
- `section()` stops the spinner and prints a phase label — use between major phases
- `summary()` is always the last call — it stops the spinner and prints the final block
