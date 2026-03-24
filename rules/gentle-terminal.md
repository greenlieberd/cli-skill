---
name: gentle-terminal
description: Progressive output, streaming Claude tokens, and keeping the terminal from flooding or flickering.
metadata:
  tags: terminal, output, streaming, ux, progressive
---

# Gentle Terminal

> Platform: macOS (Terminal.app, iTerm2, Warp).

"Gentle" means the terminal never floods, flickers, jumps, or confuses. Output appears progressively. Long operations give continuous feedback. Errors say what to do. The screen is always in a predictable state.

---

## 1. Progressive output — don't dump everything at once

Bad: clear screen → wait 3 seconds → show 200 lines.
Good: show each result as it arrives, one line at a time.

```typescript
// Append lines progressively — don't buffer
for (const result of sources) {
  process.stdout.write(`  ${A.green}✓${A.reset}  ${result.label}\n`)
  await processOne(result)
}
// Then show the summary
process.stdout.write(`\n  ${A.gold}Done — ${count} items processed${A.reset}\n`)
```

For streaming Claude output (token by token):
```typescript
const stream = await anthropic.messages.stream({ ... })
process.stdout.write(`\n  `)  // indent
for await (const event of stream) {
  if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
    process.stdout.write(event.delta.text)  // write each token immediately
  }
}
process.stdout.write('\n')  // clean newline at end
```

---

## 2. Screen zones — keep regions stable

A "gentle" terminal has predictable regions that don't jump:

```
┌──────────────────────────────────────────────────┐
│  ASCII ART / TITLE                               │  ← static header
├──────────────────────────────────────────────────┤
│                                                  │
│  CONTENT AREA                                    │  ← scrolls or updates
│  (results appear here progressively)             │
│                                                  │
├──────────────────────────────────────────────────┤
│  STATUS: currently running...                    │  ← status line (bottom)
│  ↑↓ navigate   ↵ select   ctrl+c exit           │  ← hint line (fixed)
└──────────────────────────────────────────────────┘
```

The header and footer are static — they never change during a run. Only the content area updates.

**Updating the status line without clearing everything:**
```typescript
// Move to the status line and overwrite just that line
// (requires tracking which row it's on, or using a fixed last-N-rows approach)
process.stdout.write(`\x1b[${statusRow};0H`)  // move cursor to row
process.stdout.write(`\x1b[2K`)               // clear line
process.stdout.write(`  ${A.gray}${message}${A.reset}`)
```

For simpler cases — update a single line in place:
```typescript
process.stdout.write(`\r\x1b[K  ${A.gray}${message}${A.reset}`)
// \r = return to start of line, \x1b[K = clear to end of line
```

---

## 3. Spinner with changing labels

Show what's happening right now — not just "loading":

```typescript
const FRAMES = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']

function startSpinner(label: string) {
  let i = 0
  const t = setInterval(() => {
    process.stdout.write(`\r${A.gold}${FRAMES[i++ % FRAMES.length]}${A.reset}  ${label}`)
  }, 80)
  return {
    update: (newLabel: string) => { label = newLabel },
    stop:   (finalMsg?: string) => {
      clearInterval(t)
      process.stdout.write(`\r\x1b[K`)  // clear spinner line
      if (finalMsg) process.stdout.write(`  ${A.green}✓${A.reset}  ${finalMsg}\n`)
    },
  }
}

// Usage:
const s = startSpinner('Fetching Reddit...')
await fetchReddit()
s.update('Calling Claude...')
await callClaude()
s.stop('Done — report written to output/2024-01-15-report.md')
```

---

## 4. Bounded scrolling region (viewport)

When showing a list that might be longer than the screen, use a viewport instead of dumping everything:

```typescript
const VIEWPORT = 20  // lines visible at once

function drawList(items: string[], offset: number): void {
  const cols = Math.min(process.stdout.columns ?? 80, 66)
  const visible = items.slice(offset, offset + VIEWPORT)
  visible.forEach((item, i) => {
    process.stdout.write(`  ${item.slice(0, cols - 4)}\n`)
  })
  if (items.length > VIEWPORT) {
    const more = items.length - offset - VIEWPORT
    if (more > 0) process.stdout.write(`  ${A.gray}... ${more} more  ↓${A.reset}\n`)
    if (offset > 0) process.stdout.write(`  ${A.gray}↑ scroll up${A.reset}\n`)
  }
}
```

---

## 5. Piping output to Claude Code / an agent

When a CLI should output something that an agent (Claude Code, another CLI) can read:

**Option A — structured stdout (for piping):**
```typescript
// Output JSON lines to stdout — agent reads these
process.stdout.write(JSON.stringify({ type: 'result', data: { ... } }) + '\n')
process.stdout.write(JSON.stringify({ type: 'done', count: N }) + '\n')
```

Run: `bun hud export | claude "summarize these results"`

**Option B — write to a file, agent reads it:**
```typescript
// Write a dated output file
const outFile = `output/${new Date().toISOString().slice(0,10)}-results.md`
writeFileSync(outFile, markdownContent)
process.stdout.write(`  Output: ${outFile}\n`)
// Agent can read this file on next invocation
```

**Option C — SSE stream + browser (for interactive piping):**
The browser opens, the CLI streams results to it over SSE, user can interact. See `rules/how-to-browser-view.md`.

**Option D — MCP server (for Claude Desktop):**
The CLI exposes its output directory as MCP tools. Claude Desktop reads results directly. See `rules/how-to-mcp-server.md`.

---

## 6. Loading + analyzing states

Show what phase you're in, not just "loading":

```typescript
// Multi-phase operation pattern
const phases = [
  { label: 'Reading project files...', fn: readFiles },
  { label: 'Analyzing with Claude...',  fn: analyzeWithClaude },
  { label: 'Writing PLAN.md...',        fn: writePlan },
]

for (const phase of phases) {
  const s = startSpinner(phase.label)
  const result = await phase.fn()
  s.stop()
  process.stdout.write(`  ${A.green}✓${A.reset}  ${phase.label.replace('...','')}\n`)
}
```

For Ink (wizard-style), use a running step component:
```tsx
const StepRunning: React.FC<{ onDone: () => void }> = ({ onDone }) => {
  const [status, setStatus] = useState('Starting...')
  const [log, setLog]       = useState<string[]>([])

  useEffect(() => {
    async function run() {
      setStatus('Reading files...')
      await readFiles()
      setLog(l => [...l, '✓ Files read'])

      setStatus('Analyzing...')
      await analyze()
      setLog(l => [...l, '✓ Analysis complete'])

      onDone()
    }
    run()
  }, [])

  return (
    <Frame steps={STEPS} stepIndex={currentIdx}>
      <Text color="yellow">{status}</Text>
      {log.map((line, i) => <Text key={i} color="gray">{line}</Text>)}
    </Frame>
  )
}
```

---

## 7. Error display that doesn't break layout

```typescript
function showError(message: string, fix?: string): void {
  process.stdout.write('\n')
  process.stdout.write(`  ${A.red}✗${A.reset}  ${message}\n`)
  if (fix) process.stdout.write(`     ${A.gray}→ ${fix}${A.reset}\n`)
  process.stdout.write('\n')
}

// Examples:
showError('ANTHROPIC_API_KEY is missing', 'Add it to .env — see .env.example')
showError(`Can't read ${path}`, `Run: touch ${path}`)
showError(`HTTP 429 — rate limited`, 'Wait 60s and try again')
```

For Ink, use a consistent error component:
```tsx
const ErrorBox: React.FC<{ message: string; fix?: string }> = ({ message, fix }) => (
  <Box flexDirection="column" marginY={1}>
    <Text color="red">✗  {message}</Text>
    {fix && <Text color="gray" dimColor>   → {fix}</Text>}
  </Box>
)
```

---

## 8. Clean exits

The terminal must always be left in a clean state:

```typescript
// Register these at startup — not just in one path
process.on('SIGINT', () => {
  process.stdout.write('\x1b[?25h')  // restore cursor
  process.stdout.write('\x1b[0m')   // reset colors
  process.stdout.write('\n')
  process.exit(0)
})

process.on('exit', () => {
  process.stdout.write('\x1b[?25h')  // restore cursor — always
  if (process.stdin.isTTY) {
    process.stdin.setRawMode(false)  // restore stdin if it was in raw mode
  }
})
```

For Ink: the `render()` call from Ink handles cleanup automatically. You only need SIGINT cleanup if you add raw stdin reading alongside Ink.

---

## 9. Rate-limit visual updates

Re-rendering more than ~30fps causes flicker and wastes CPU. The spinner at 80ms (12.5fps) is the right pace for most activity indicators.

```typescript
// For status updates from a tight loop — throttle to 100ms
let lastDraw = 0
function maybeUpdate(msg: string) {
  const now = Date.now()
  if (now - lastDraw > 100) {
    process.stdout.write(`\r\x1b[K  ${msg}`)
    lastDraw = now
  }
}
```

For Ink: React's batching + Ink's reconciler handles this. Don't add artificial delays — let Ink decide when to re-render.

---

## 10. The "dirty screen" checklist

Before shipping any HUD:

- [ ] Full screen clear only happens at deliberate screen transitions — not on every data update
- [ ] Content area appends or updates in place — never re-clears the whole viewport for partial updates
- [ ] Spinner runs on a separate `setInterval` — doesn't block the async operation it's indicating
- [ ] All ANSI sequences terminated — no leftover bold/color bleeding into the next line
- [ ] Long text truncated to `Math.min(process.stdout.columns - 4, 60)` — no wrapping surprises
- [ ] On resize: the entire screen redraws cleanly, not partially
