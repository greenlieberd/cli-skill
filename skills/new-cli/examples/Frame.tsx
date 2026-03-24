// cli/components/Frame.tsx — wraps every wizard step
// Renders: border, progress dots, step labels, content slot, footer hints
// Based on the pattern from animations/cli/components/Frame.tsx

import React from 'react'
import { Box, Text } from 'ink'

export interface FrameStep {
  label: string   // full label used in step state
  short: string   // ≤5 chars, shown in progress bar
}

interface Props {
  steps:     FrameStep[]
  stepIndex: number
  title?:    string
  footer?:   string
  children:  React.ReactNode
}

export const Frame: React.FC<Props> = ({ steps, stepIndex, title, footer, children }) => {
  return (
    <Box
      flexDirection="column"
      borderStyle="single"
      borderColor="green"
      paddingX={1}
      width={66}
    >
      {/* Header */}
      <Box justifyContent="space-between">
        <Text color="greenBright" bold>{`▶▶ ${title ?? 'CLI WIZARD'}`}</Text>
        <Text color="gray">{`[${stepIndex + 1} / ${steps.length}]  ↑↓ ↵ ←`}</Text>
      </Box>

      {/* Progress dots */}
      <Box marginY={1} paddingLeft={2}>
        {steps.map((s, i) => {
          const done    = i < stepIndex
          const current = i === stepIndex
          const dot   = done ? '✓' : current ? '◉' : '○'
          const color = done || current ? 'greenBright' : 'gray'
          return (
            <React.Fragment key={s.label}>
              <Text color={color}>{dot}</Text>
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

      {/* Divider */}
      <Box marginY={1}>
        <Text color="gray">{'─'.repeat(62)}</Text>
      </Box>

      {/* Content */}
      <Box flexDirection="column" paddingX={1} minHeight={8}>
        {children}
      </Box>

      {/* Footer */}
      <Box marginTop={1}>
        <Text color="gray">{'─'.repeat(62)}</Text>
      </Box>
      <Box>
        <Text color="gray">
          {footer ?? '↑ ↓ navigate   space / ↵ select   ← back   ctrl+c exit'}
        </Text>
      </Box>
    </Box>
  )
}
