---
name: hud-screens
description: ANSI HUD architecture — navigation, resize handling, screen state machine, UX checklist.
metadata:
  tags: hud, ansi, navigation, resize, raw-mode
---

# HUD Screens

Great CLI tools feel inevitable. Every keypress does what you expect, every wait has a visual anchor, every error tells you what to do next. This guide is the standard. Every generated CLI should pass it.

Study these patterns from production tools: Ink (React for CLIs), Bun's own CLI, Claude Code's interface, and the Propane CLI library (animations/, images/, pulse/).

---

## 1. Navigation

**Arrow keys are the primary input. Never require typing to navigate.**

```
↑ ↓      — move between items
↵ / space — select / confirm
←        — back (never ESC — too far from the home row)
ctrl+c   — exit from anywhere, always
```

Rules:
- Show these hints in a footer on every screen. Users forget.
- Never use HJKL (vim keys) as the default — this is a tool, not an editor.
- Wrap selection: going down from the last item should not jump to the top. Stop at the edge.
- Selected item gets a visible cursor: `▶` for HUD, `◉` for Wizard progress dots.

**Ink implementation:**
```tsx
useInput((input, key) => {
  if (key.upArrow)    setIdx(i => Math.max(0, i - 1))
  if (key.downArrow)  setIdx(i => Math.min(items.length - 1, i + 1))
  if (key.return || input === ' ') onSelect(items[idx])
  if (key.leftArrow)  onBack?.()
})
```

**HUD implementation (raw mode):**
```typescript
// Buffer escape sequences for arrow keys
const UP    = '\x1b[A'
const DOWN  = '\x1b[B'
const ENTER = '\r'
const CTRL_C = '\x03'
```

---

## 2. Visual hierarchy

Terminal has three tools: color, weight, spacing. Use all three deliberately.

**Color palette (dark background, matches #0a0a0a terminal theme):**

| Role | ANSI | Ink prop | Use for |
|------|------|----------|---------|
| Primary action / brand | `\x1b[33m` gold | `color="yellow"` | Selected item, active state, ASCII art |
| Success | `\x1b[32m` green | `color="green"` | Completed steps, ✓ markers |
| Error | `\x1b[31m` red | `color="red"` | Failures, blockers |
| Muted / hints | `\x1b[90m` gray | `color="gray"` | Footer hints, secondary info |
| Body text | `\x1b[97m` white | `color="white"` | Main content |

Rules:
- **One primary color per screen.** Don't use gold + green + cyan all at once.
- **Bold = importance, not decoration.** Use `bold` only on the currently selected item or a critical warning.
- **Dim for secondary.** `dimColor` in Ink, `\x1b[2m` in ANSI — use for hints, timestamps, anything the user doesn't need to read every time.
- **Width discipline.** Target 66 characters wide (Ink Box `width={66}`). This fits comfortably in a split terminal. Never assume a wide viewport.

---

## 3. Feedback timing

**The user should never wonder if something is happening.**

Under 100ms: no feedback needed — response feels instant.
100ms–2s: show a spinner immediately, before the operation starts.
Over 2s: show a spinner with a label describing what's happening. Update the label as phases change.

**Spinner pattern:**
```typescript
const FRAMES = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
let i = 0
const t = setInterval(() => {
  process.stdout.write(`\r${FRAMES[i++ % FRAMES.length]} ${label}`)
}, 80)
// Stop: clearInterval(t); process.stdout.write('\r\x1b[K')
```

**Multi-phase feedback (for operations with known steps):**
```
⠋ Fetching Reddit...
→
⠋ Calling Claude (smart)...
→
✓ Done — 1,240 words written to output/2024-01-15-report.md
```

Show the previous step's result before moving to the next. Don't replace it.

**Ink streaming output:**
```tsx
// Stream Claude output token by token
const [text, setText] = useState('')
// append to text on each delta event
// render: <Text>{text}</Text> — Ink handles re-render efficiently
```

---

## 4. Error messages

**An error message that doesn't tell you what to do next is broken.**

Bad: `Error: ENOENT`
Good: `Can't read .env — run: cp .env.example .env and fill in your API key`

Bad: `API error 401`
Good: `ANTHROPIC_API_KEY is invalid or missing. Check .env — key should start with "sk-ant-"`

Pattern:
```
[what failed] — [why it likely failed] — [exact command or step to fix it]
```

In code:
```typescript
// Don't: throw new Error('API call failed')
// Do:
return sourceError('anthropic', 'Claude API',
  `Request failed (${status}). Check ANTHROPIC_API_KEY in .env`)
```

For terminal display, use a consistent error format:
```
  ✗  [error summary]
     [detail line if needed]
     → [fix instruction]
```

---

## 5. Empty and loading states

Every screen that loads data needs three states: loading, empty, populated.

**Loading:** spinner with a label (see §3)

**Empty:**
```
  No output yet.
  → Run "bun hud" and select "Run" to generate your first report.
```
Never show a blank screen. Always tell the user what to do next.

**Populated:** show the most recent item first. Date-prefix filenames (`2024-01-15-report.md`) sort naturally.

---

## 6. The Ink wizard pattern

**One decision per screen.** Never put two choices on the same step.

Each step component receives exactly:
- `onNext(value)` — advance and store the answer
- `onBack()` — go to the previous step

The `Frame` component handles all chrome (border, progress dots, footer). Steps never manage their own borders.

**Progress dots tell the user where they are and how far they have to go:**
- `✓` — completed (green)
- `◉` — current (green, bold label)
- `○` — upcoming (gray)

Step label length: ≤5 characters. They run together with ` ─── ` separators. `name`, `goal`, `menu`, `ai`, `apis`, `web`, `mcp`, `ok`.

**Don't show more than 8 dots.** If your wizard has more than 8 steps, you have a design problem — consolidate or split into sub-flows.

---

## 7. HUD screen patterns

**The home screen is the most important screen.** It should:
- Show the ASCII art header (6 lines, gold, `\x1b[33m`)
- Show 4–6 menu items, no more
- Have a visible selection cursor (`▶`)
- Show a one-line description for the selected item

**Sub-screens should feel like modal layers:**
- Clear the screen on entry
- Show a back hint (`← back`) at the bottom
- Return to the exact state the home screen was in (same selected item)

**Don't build a deep navigation tree.** If you're going 3 levels deep, reconsider the feature — most CLI tasks shouldn't require more than two screens.

**HUD screen function pattern:**
```typescript
async function screenBrowse(state: AppState): Promise<void> {
  let selected = 0
  while (true) {
    drawBrowse(state, selected)       // render
    const key = await readKey()      // wait
    if (key === CTRL_C) exit()
    if (key === '\x1b[A') selected = Math.max(0, selected - 1)
    if (key === '\x1b[B') selected = Math.min(state.files.length - 1, selected + 1)
    if (key === '\r')  { await openFile(state.files[selected]); return }
    if (key === '\x1b[D') return     // ← back
  }
}
```

---

## 8. Testing interactive UIs

**You can't test raw terminal interaction — test the logic layer instead.**

Split every screen into: data fetching, data transformation, and rendering. Test the first two. The rendering is visual and should be reviewed manually.

```typescript
// Testable: the data layer
test('loadReports returns sorted files', async () => {
  // write fixture files, call loadReports(), assert order
})

// Not testable via bun:test: the screen render loop
// → test manually: run bun hud and verify visually
```

For wizard steps, test the answer validation logic, not the Ink rendering:
```typescript
// Extract validation from the component
export function validateName(input: string): string | null {
  if (!input.trim()) return 'Name is required'
  if (!/^[a-z0-9-]+$/.test(input)) return 'Use lowercase letters, numbers, and hyphens only'
  return null
}
// Then test:
test('validateName rejects spaces', () => {
  expect(validateName('my tool')).toBeTruthy()
})
```

---

## 9. Accessibility

- **Always support `--no-color`:** check `process.env.NO_COLOR` and strip ANSI codes if set
- **Don't rely on color alone** to convey state — use `✓`, `✗`, `▶` symbols too
- **Keep line lengths under 80 chars** for users with narrow terminals or screen magnification
- **Avoid rapid flicker** — redraw at most ~30fps; the spinner at 80ms is a good benchmark
- **Support ctrl+c everywhere** — process.on('SIGINT') must always exit cleanly and restore cursor

---

## 10. What Claude Code does that we should copy

Claude Code's interface is the reference implementation for a great developer CLI. Study these patterns:

**Streaming output** — output appears token by token, not all at once. Reduces perceived latency dramatically. Use `stream: true` in Anthropic SDK calls and pipe deltas to the screen.

**Status bar** — a persistent one-line status at the bottom of the screen (separate process, reads JSON from stdin). Shows what's running, how many tokens, model in use. See guide 07 for implementation.

**Thinking inline** — when Claude is reasoning, show a subtle indicator (`◌ thinking...`) rather than a blank wait.

**Confirmation before destructive actions** — always show what will be written/deleted before doing it. "About to write 12 files to `my-tool/`. Proceed? [y/N]"

**Exit codes that mean something:**
- `0` — success
- `1` — user cancelled or no-op
- `2` — error (bad input, missing env var)
- `3` — external failure (API down, file not found)

---

## 11. Terminal resize — the most common layout bug

When a user resizes their terminal window, a raw ANSI HUD will break: lines wrap unexpectedly, the cursor ends up in the wrong place, and the display becomes corrupted. This is one of the most common issues with ANSI CLIs and one of the easiest to fix.

**The cause:** ANSI HUDs draw by clearing the screen and rewriting from the top. If the terminal width changes mid-draw, lines that were 66 chars wide now wrap at 50 — but the cursor position math is still based on 66.

**The fix — listen for SIGWINCH and redraw:**

```typescript
// In your main HUD loop, add this once at startup:
process.stdout.on('resize', () => {
  // Re-read terminal dimensions
  const cols  = process.stdout.columns ?? 80
  const rows  = process.stdout.rows    ?? 24
  // Clamp your content width to the new terminal width minus padding
  DRAW_WIDTH = Math.min(66, cols - 4)
  // Trigger a full redraw on the next loop iteration
  needsRedraw = true
})
```

For Ink (React-based): Ink handles this automatically. The `Box` layout system re-renders on resize. You don't need to do anything — this is one of the reasons to prefer Ink over raw ANSI for complex layouts.

**Minimum safe width:** if the terminal is narrower than 50 columns, show a warning instead of a broken layout:

```typescript
function checkWidth(): boolean {
  const cols = process.stdout.columns ?? 80
  if (cols < 50) {
    process.stdout.write(A.clear)
    process.stdout.write(`\n  Terminal too narrow (${cols} cols).\n  Resize to at least 50 columns.\n`)
    return false
  }
  return true
}
// Call checkWidth() at the top of your draw function
```

**Defensive width for all content:** never hardcode absolute column positions. Use relative padding:

```typescript
// Bad: assumes 66 column terminal
const bar = '─'.repeat(62)

// Good: adapts to actual terminal width
const width = Math.min(process.stdout.columns ?? 80, 66)
const bar = '─'.repeat(width - 4)
```

**The full defensive pattern for ANSI HUDs:**

```typescript
let DRAW_WIDTH = Math.min(process.stdout.columns ?? 80, 66)

process.stdout.on('resize', () => {
  DRAW_WIDTH = Math.min(process.stdout.columns ?? 80, 66)
  redraw()   // call your main draw function
})

function redraw(): void {
  const cols = process.stdout.columns ?? 80
  if (cols < 50) {
    process.stdout.write(`${A.clear}\n  Terminal too narrow — resize to 50+ columns\n`)
    return
  }
  // ... normal draw logic using DRAW_WIDTH instead of hardcoded 66
}
```

Add `process.stdout.on('resize', ...)` to the resize checklist — it belongs in every HUD alongside `process.on('SIGINT')` and cursor restoration.

---

## UX review checklist

Run this before calling any CLI "done":

**Navigation**
- [ ] Arrow keys work on every menu/list
- [ ] `←` goes back from every sub-screen
- [ ] `ctrl+c` exits cleanly from every state (cursor restored)
- [ ] Selection wraps off at edges (doesn't jump to opposite end)

**Feedback**
- [ ] Every operation over 100ms shows a spinner
- [ ] Spinner labels describe what's happening, not just "loading..."
- [ ] Success state is visually distinct from error state
- [ ] Error messages include a fix instruction

**Visual**
- [ ] Max 66 chars wide
- [ ] Consistent color palette (one accent color per screen)
- [ ] `bold` used only for active/important items
- [ ] Footer hints visible on every interactive screen

**Resize resilience (ANSI HUD only — Ink handles this automatically)**
- [ ] `process.stdout.on('resize', redraw)` registered at startup
- [ ] All content widths use `Math.min(process.stdout.columns, 66)` — no hardcoded column counts
- [ ] Graceful degradation message if terminal is under 50 columns wide

**Edge cases**
- [ ] Empty state has a helpful message + next action
- [ ] API key missing: clear error + how to set it
- [ ] Output directory doesn't exist: created automatically, not an error
- [ ] `--no-color` respected (or at minimum: doesn't crash)
- [ ] Cursor always restored on exit — `process.stdout.write('\x1b[?25h')` in SIGINT handler
