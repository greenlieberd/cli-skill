// cli/App.tsx — Ink wizard step state machine
// Each "step" is its own component. App manages transitions.
// Replace Step types and answers shape with your actual steps.

import React, { useState } from 'react'

// ── Types ──────────────────────────────────────────────────────────────────────

type Step = 'goal' | 'name' | 'confirm' | 'running' | 'done'

interface Answers {
  goal: string
  name: string
}

// ── Step maps ─────────────────────────────────────────────────────────────────
// NEXT and PREV define the wizard flow. Extend as you add steps.

const NEXT: Record<Step, Step> = {
  goal:    'name',
  name:    'confirm',
  confirm: 'running',
  running: 'done',
  done:    'done',
}

const PREV: Record<Step, Step> = {
  goal:    'goal',      // first step: back goes nowhere
  name:    'goal',
  confirm: 'name',
  running: 'confirm',
  done:    'done',
}

// ── Step components (import from cli/steps/) ──────────────────────────────────
// Each step receives: onNext (advance + store answer) and onBack (go to prev step)
// These are placeholders — replace with real step components.

const StepGoal: React.FC<{ onNext: (v: string) => void; onBack: () => void }> = ({ onNext }) => {
  // Use TextInput from cli/components/TextInput.tsx
  return null // placeholder
}

const StepName: React.FC<{ suggested: string; onNext: (v: string) => void; onBack: () => void }> = ({ onNext }) => {
  return null // placeholder
}

const StepConfirm: React.FC<{ answers: Answers; onConfirm: () => void; onBack: () => void }> = ({ onConfirm }) => {
  return null // placeholder
}

const StepRunning: React.FC<{ answers: Answers; onDone: () => void; onError: (e: string) => void }> = () => {
  return null // placeholder
}

const StepDone: React.FC<{ answers: Answers; onRestart: () => void }> = () => {
  return null // placeholder
}

// ── App ───────────────────────────────────────────────────────────────────────

export const App: React.FC = () => {
  const [step, setStep]       = useState<Step>('goal')
  const [answers, setAnswers] = useState<Partial<Answers>>({})
  const [error, setError]     = useState('')

  function next(key: keyof Answers, value: string) {
    setAnswers(a => ({ ...a, [key]: value }))
    setStep(NEXT[step])
  }

  if (error) {
    // Simple error screen — ctrl+c to exit
    const { Box, Text } = require('ink')
    return (
      <Box padding={1} flexDirection="column">
        <Text color="red" bold>Error</Text>
        <Text>{error}</Text>
        <Text color="gray">ctrl+c to exit</Text>
      </Box>
    )
  }

  switch (step) {
    case 'goal':
      return <StepGoal onNext={v => next('goal', v)} onBack={() => {}} />
    case 'name':
      return (
        <StepName
          suggested={answers.goal?.toLowerCase().replace(/\s+/g, '-').slice(0, 20) ?? ''}
          onNext={v => next('name', v)}
          onBack={() => setStep(PREV.name)}
        />
      )
    case 'confirm':
      return (
        <StepConfirm
          answers={answers as Answers}
          onConfirm={() => setStep(NEXT.confirm)}
          onBack={() => setStep(PREV.confirm)}
        />
      )
    case 'running':
      return (
        <StepRunning
          answers={answers as Answers}
          onDone={() => setStep('done')}
          onError={setError}
        />
      )
    case 'done':
      return (
        <StepDone
          answers={answers as Answers}
          onRestart={() => { setStep('goal'); setAnswers({}) }}
        />
      )
  }
}
