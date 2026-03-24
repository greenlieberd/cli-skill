---
name: hybrid-interface
description: Combining an ANSI HUD home screen with Ink Wizard sub-flows in the same CLI.
metadata:
  tags: hybrid, hud, wizard, ink, ansi, interface
---

# Hybrid Interface

> Platform: macOS (Terminal.app, iTerm2, Warp).

A hybrid interface uses an ANSI HUD as the persistent home screen for browsing and navigation, and launches an Ink Wizard as a sub-flow for multi-step creation or configuration tasks. When the Wizard exits, control returns to the HUD.

Use this when: your tool both **browses stored state** (needs a HUD) and **has a generation mode** with branching questions (needs a Wizard).

## Prerequisites

- Ink v5 + React 19: `bun add ink react`
- ANSI HUD patterns from `hud-screens.md`
- Ink Wizard patterns from `wizard-steps.md`
- Both `src/hud.ts` and `cli/App.tsx` in the project

---

## 1. Architecture

```
Entry: bun hud → src/cli.ts
  ↓
runHud()           ← ANSI HUD (always-on, raw mode)
  ↓ user presses [n] to generate
suspendHud()       ← restore terminal, clear screen
  ↓
runWizard()        ← spawns Ink App.tsx in same process
  ↓ wizard exits (onComplete callback)
resumeHud()        ← re-enter raw mode, redraw
```

---

## 2. Suspend and resume HUD

The HUD must release stdin before Ink takes over. Ink manages its own input loop.

```typescript
// src/hud.ts
import { render } from 'ink'
import { createElement } from 'react'
import { App } from '../cli/App.tsx'

let rawModeActive = false

function suspendHud(): void {
  if (rawModeActive && process.stdin.isTTY) {
    process.stdin.setRawMode(false)
    rawModeActive = false
  }
  process.stdin.pause()
  clearScreen()
}

function resumeHud(state: State): void {
  process.stdin.resume()
  if (process.stdin.isTTY) {
    process.stdin.setRawMode(true)
    rawModeActive = true
  }
  redraw(state)
}
```

---

## 3. Launch the Wizard from HUD

```typescript
// src/hud.ts — in the keypress handler
if (key === 'n') {
  suspendHud()
  launchWizard((result) => {
    // Wizard completed — result is the wizard's answers
    if (result) {
      state.items.unshift(result)   // add to HUD state
    }
    resumeHud(state)
  })
}

function launchWizard(onDone: (result: WizardResult | null) => void): void {
  const { unmount } = render(
    createElement(App, {
      onComplete: (result: WizardResult) => {
        unmount()
        onDone(result)
      },
      onCancel: () => {
        unmount()
        onDone(null)
      },
    })
  )
}
```

---

## 4. Wizard — emit onComplete / onCancel

```tsx
// cli/App.tsx
interface Props {
  onComplete: (result: WizardResult) => void
  onCancel:   () => void
}

export function App({ onComplete, onCancel }: Props) {
  const [step, setStep]       = useState(0)
  const [answers, setAnswers] = useState<Partial<WizardResult>>({})

  useInput((input, key) => {
    if (key.leftArrow && step === 0) onCancel()
    if (key.leftArrow && step > 0)   setStep(s => s - 1)
  })

  if (step === STEPS.length) {
    // Final step — trigger complete
    onComplete(answers as WizardResult)
    return null
  }

  return <Frame step={step} total={STEPS.length}>{/* ... */}</Frame>
}
```

---

## 5. State handoff — Wizard result updates HUD

After the Wizard completes, the result should appear in the HUD immediately — no refresh needed:

```typescript
// src/hud.ts
function launchWizard(onDone: (result: GeneratedItem | null) => void): void {
  const { unmount } = render(createElement(App, {
    onComplete: async (answers: WizardAnswers) => {
      unmount()
      // Run the generation (may be async — show a spinner in the HUD after)
      const item = await generate(answers)
      onDone(item)
    },
    onCancel: () => { unmount(); onDone(null) },
  }))
}
```

---

## 6. When NOT to use hybrid

- Tool only generates things → pure Wizard is simpler
- Tool only browses stored data → pure HUD is simpler
- Tool has a single generation step → HUD with inline prompt is enough

---

## Rules

- HUD releases stdin before Ink mounts — never two input loops at once
- Wizard always has `onComplete` and `onCancel` props — HUD decides what to do
- `unmount()` before calling the callback — Ink must be fully gone before HUD resumes
- HUD re-enters raw mode in `resumeHud()` — Ink leaves terminal in normal mode
- State updates happen in the HUD after Wizard exits — not inside the Wizard
