# How to Build a Wizard Step

> Platform: macOS. Uses Ink (React for CLI) and `useInput` from the Ink library.

A wizard is a series of focused screens — one decision per screen. Each step is a React component. `App.tsx` manages the state machine. `Frame.tsx` handles all the chrome.

---

## The step pattern

Every step component has exactly this signature:

```tsx
interface StepProps {
  onNext: (value: AnswerType) => void  // advance + store answer
  onBack: () => void                   // go to previous step
  // optional: anything pre-populated from earlier steps
}

export const StepMyThing: React.FC<StepProps> = ({ onNext, onBack }) => {
  // logic here
  return (
    <Frame steps={STEPS} stepIndex={2} title="MY TOOL" footer="↑↓ navigate  ↵ select  ← back">
      {/* content here */}
    </Frame>
  )
}
```

Rules:
- Steps never manage their own borders or footers — that's `Frame`'s job
- `onNext` always carries the answer value — never mutates shared state directly
- `onBack` always goes to the previous step — `Frame` shows the `←` hint

---

## Frame component

`Frame` renders the border, progress dots, step labels, and footer on every screen.

```tsx
// cli/components/Frame.tsx
import React from 'react'
import { Box, Text } from 'ink'

export interface FrameStep { label: string; short: string }  // short ≤5 chars

interface Props {
  steps:     FrameStep[]
  stepIndex: number
  title?:    string
  footer?:   string
  children:  React.ReactNode
}

export const Frame: React.FC<Props> = ({ steps, stepIndex, title, footer, children }) => (
  <Box flexDirection="column" borderStyle="single" borderColor="green" paddingX={1} width={66}>
    {/* Title + counter */}
    <Box justifyContent="space-between">
      <Text color="greenBright" bold>{`▶▶ ${title ?? 'CLI WIZARD'}`}</Text>
      <Text color="gray">{`[${stepIndex + 1} / ${steps.length}]`}</Text>
    </Box>

    {/* Progress dots: ✓ done  ◉ current  ○ future */}
    <Box marginY={1} paddingLeft={2}>
      {steps.map((s, i) => {
        const symbol = i < stepIndex ? '✓' : i === stepIndex ? '◉' : '○'
        const color  = i <= stepIndex ? 'greenBright' : 'gray'
        return (
          <React.Fragment key={s.label}>
            <Text color={color}>{symbol}</Text>
            {i < steps.length - 1 && <Text color="gray">{' ─── '}</Text>}
          </React.Fragment>
        )
      })}
    </Box>

    {/* Step labels */}
    <Box paddingLeft={2}>
      {steps.map((s, i) => (
        <React.Fragment key={s.label}>
          <Text color={i <= stepIndex ? 'greenBright' : 'gray'} bold={i === stepIndex}>
            {s.short.padEnd(5)}
          </Text>
          {i < steps.length - 1 && <Text>{'  '}</Text>}
        </React.Fragment>
      ))}
    </Box>

    <Box marginY={1}><Text color="gray">{'─'.repeat(62)}</Text></Box>

    {/* Content slot */}
    <Box flexDirection="column" paddingX={1} minHeight={8}>{children}</Box>

    <Box marginTop={1}><Text color="gray">{'─'.repeat(62)}</Text></Box>
    <Box>
      <Text color="gray">{footer ?? '↑ ↓ navigate   space / ↵ select   ← back   ctrl+c exit'}</Text>
    </Box>
  </Box>
)
```

Step labels: max 5 characters. Examples: `goal`, `name`, `menu`, `ai`, `apis`, `web`, `mcp`, `ok`. Maximum 8 steps — more than 8 means the flow needs to be redesigned.

---

## Selection list

```tsx
// cli/components/SelectList.tsx
import React, { useState } from 'react'
import { Box, Text, useInput } from 'ink'

interface Option<T extends string> { value: T; label: string; desc?: string }

export function SelectList<T extends string>({
  options, onSelect, onBack,
}: { options: Option<T>[]; onSelect: (v: T) => void; onBack?: () => void }) {
  const [idx, setIdx] = useState(0)

  useInput((input, key) => {
    if (key.upArrow)    setIdx(i => Math.max(0, i - 1))
    if (key.downArrow)  setIdx(i => Math.min(options.length - 1, i + 1))
    if (key.return || input === ' ') onSelect(options[idx].value)
    if (key.leftArrow && onBack) onBack()
  })

  return (
    <Box flexDirection="column">
      {options.map((o, i) => (
        <Box key={o.value}>
          <Text color={i === idx ? 'greenBright' : 'gray'} bold={i === idx}>
            {i === idx ? '▶ ' : '  '}{o.label}
          </Text>
          {o.desc && <Text color="gray" dimColor>{'  '}{o.desc}</Text>}
        </Box>
      ))}
    </Box>
  )
}
```

Do not wrap at the ends — stop at first and last item.

---

## Multi-select list

For "pick any of the following" questions:

```tsx
export function MultiSelectList<T extends string>({
  options, onConfirm, onBack, min = 0,
}: { options: Option<T>[]; onConfirm: (vs: T[]) => void; onBack?: () => void; min?: number }) {
  const [idx,  setIdx]  = useState(0)
  const [selected, set] = useState(new Set<T>())

  useInput((input, key) => {
    if (key.upArrow)   setIdx(i => Math.max(0, i - 1))
    if (key.downArrow) setIdx(i => Math.min(options.length - 1, i + 1))
    if (input === ' ') set(prev => {
      const next = new Set(prev)
      next.has(options[idx].value) ? next.delete(options[idx].value) : next.add(options[idx].value)
      return next
    })
    if (key.return && selected.size >= min) onConfirm([...selected])
    if (key.leftArrow && onBack) onBack()
  })

  return (
    <Box flexDirection="column">
      {options.map((o, i) => (
        <Box key={o.value}>
          <Text color={i === idx ? 'white' : 'gray'}>
            {i === idx ? '▶ ' : '  '}
            {selected.has(o.value) ? '◆ ' : '◇ '}
            {o.label}
          </Text>
        </Box>
      ))}
      <Text color="gray" dimColor>space toggle   ↵ confirm{min > 0 ? `   (min ${min})` : ''}</Text>
    </Box>
  )
}
```

---

## Text input step

For open-ended answers:

```tsx
// cli/components/TextInput.tsx — wraps ink-text-input with ← back support
import React from 'react'
import { Box, Text, useInput } from 'ink'
import InkTextInput from 'ink-text-input'

interface Props {
  value:       string
  onChange:    (v: string) => void
  onSubmit:    (v: string) => void
  onBack?:     () => void
  placeholder?: string
}

export const TextInput: React.FC<Props> = ({ value, onChange, onSubmit, onBack, placeholder }) => {
  useInput((_, key) => {
    if (key.leftArrow && !value && onBack) onBack()  // ← on empty input = back
  })
  return (
    <Box>
      <Text color="green">{'> '}</Text>
      <InkTextInput
        value={value}
        onChange={onChange}
        onSubmit={v => { if (v.trim()) onSubmit(v.trim()) }}
        placeholder={placeholder}
      />
    </Box>
  )
}
```

---

## App.tsx state machine

```tsx
// cli/App.tsx
type Step = 'goal' | 'name' | 'confirm' | 'running' | 'done'
interface Answers { goal: string; name: string }

// These maps are the entire navigation structure
const NEXT: Record<Step, Step> = {
  goal: 'name', name: 'confirm', confirm: 'running', running: 'done', done: 'done',
}
const PREV: Record<Step, Step> = {
  goal: 'goal',  // first step: no back
  name: 'goal', confirm: 'name', running: 'confirm', done: 'done',
}

export const App: React.FC = () => {
  const [step, setStep]       = useState<Step>('goal')
  const [answers, setAnswers] = useState<Partial<Answers>>({})

  function advance(key: keyof Answers, value: string) {
    setAnswers(a => ({ ...a, [key]: value }))
    setStep(NEXT[step])
  }

  switch (step) {
    case 'goal':
      return <StepGoal onNext={v => advance('goal', v)} onBack={() => {}} />
    case 'name':
      return <StepName onNext={v => advance('name', v)} onBack={() => setStep(PREV.name)} />
    // ...
  }
}
```

Every step must appear in both NEXT and PREV. There must be no dead ends.

---

## tsconfig.json (required for Ink)

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "jsxImportSource": "react",
    "strict": true,
    "skipLibCheck": true
  }
}
```

---

## Package deps for wizard-style CLI

```json
{
  "dependencies": {
    "@anthropic-ai/sdk": "^0.40.0",
    "ink": "^5.0.0",
    "ink-text-input": "^6.0.0",
    "react": "^19.0.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "typescript": "^5.0.0"
  }
}
```
