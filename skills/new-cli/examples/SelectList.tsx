// cli/components/SelectList.tsx — arrow-key single and multi-select
// Used in wizard steps for choosing from a fixed list of options.

import React, { useState } from 'react'
import { Box, Text, useInput } from 'ink'

// ── Single-select ─────────────────────────────────────────────────────────────

const NAV_HINT = '↑ ↓ navigate   ↵ select   ← back'

interface SelectOption<T extends string = string> {
  value:   T
  label:   string
  desc?:   string
}

interface SelectListProps<T extends string> {
  options:  SelectOption<T>[]
  onSelect: (value: T) => void
  onBack?:  () => void
}

export function SelectList<T extends string>({ options, onSelect, onBack }: SelectListProps<T>) {
  const [idx, setIdx] = useState(0)

  useInput((input, key) => {
    if (key.upArrow)    setIdx(i => Math.max(0, i - 1))
    if (key.downArrow)  setIdx(i => Math.min(options.length - 1, i + 1))
    if (key.return || input === ' ') onSelect(options[idx].value)
    if (key.leftArrow && onBack) onBack()
  })

  return (
    <Box flexDirection="column">
      {options.map((o, i) => {
        const active = i === idx
        return (
          <Box key={o.value}>
            <Text color={active ? 'greenBright' : 'gray'} bold={active}>
              {active ? '▶ ' : '  '}
              {o.label}
            </Text>
            {o.desc && (
              <Text color="gray" dimColor>{'  '}{o.desc}</Text>
            )}
          </Box>
        )
      })}
      <Box marginTop={1}>
        <Text color="gray" dimColor>{NAV_HINT}</Text>
      </Box>
    </Box>
  )
}

// ── Multi-select ──────────────────────────────────────────────────────────────

const MULTI_HINT = '↑ ↓ navigate   space toggle   ↵ confirm   ← back'

interface MultiSelectListProps<T extends string> {
  options:    SelectOption<T>[]
  onConfirm:  (values: T[]) => void
  onBack?:    () => void
  min?:       number   // minimum selections required (default 0)
}

export function MultiSelectList<T extends string>({ options, onConfirm, onBack, min = 0 }: MultiSelectListProps<T>) {
  const [idx,      setIdx]     = useState(0)
  const [selected, setSelected] = useState<Set<T>>(new Set())

  function toggle(value: T) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(value) ? next.delete(value) : next.add(value)
      return next
    })
  }

  useInput((input, key) => {
    if (key.upArrow)   setIdx(i => Math.max(0, i - 1))
    if (key.downArrow) setIdx(i => Math.min(options.length - 1, i + 1))
    if (input === ' ') toggle(options[idx].value)
    if (key.return) {
      if (selected.size >= min) onConfirm([...selected])
    }
    if (key.leftArrow && onBack) onBack()
  })

  return (
    <Box flexDirection="column">
      {options.map((o, i) => {
        const active  = i === idx
        const checked = selected.has(o.value)
        return (
          <Box key={o.value}>
            <Text color={active ? 'white' : 'gray'}>
              {active ? '▶ ' : '  '}
              {checked ? '◆ ' : '◇ '}
              {o.label}
            </Text>
            {o.desc && <Text color="gray" dimColor>{'  '}{o.desc}</Text>}
          </Box>
        )
      })}
      <Box marginTop={1}>
        <Text color="gray" dimColor>{MULTI_HINT}</Text>
      </Box>
      {min > 0 && selected.size < min && (
        <Text color="yellow" dimColor>{`  select at least ${min}`}</Text>
      )}
    </Box>
  )
}
