---
name: token-spend
description: Tracking token usage and estimating cost for Anthropic API calls in CLI tools.
metadata:
  tags: tokens, cost, usage, anthropic, logging
---

# Token Spend

> Platform: macOS (Terminal.app, iTerm2, Warp).

Every Claude call returns token counts. Capture them. Users want to know what each run costs — especially batch tools that call Claude dozens of times.

## Prerequisites

- Anthropic SDK: `bun add @anthropic-ai/sdk`
- `src/models.ts` with model IDs (see `models.md`)
- `src/logger.ts` with `logUsage()` (see `logging.md`)

---

## 1. Capture tokens from every response

The Anthropic SDK returns usage in every response. Always capture it:

```typescript
// src/ai.ts
import Anthropic from '@anthropic-ai/sdk'
import { MODELS } from './models.ts'
import { logUsage } from './logger.ts'

const anthropic = new Anthropic()

export interface CallResult {
  content:      string
  inputTokens:  number
  outputTokens: number
}

export async function callClaude(
  prompt: string,
  model: string = MODELS.smart
): Promise<CallResult> {
  const response = await anthropic.messages.create({
    model,
    max_tokens: 4096,
    messages: [{ role: 'user', content: prompt }],
  })

  const { input_tokens, output_tokens } = response.usage
  logUsage({ type: 'ai', model, inputTokens: input_tokens, outputTokens: output_tokens })

  return {
    content:      response.content[0].type === 'text' ? response.content[0].text : '',
    inputTokens:  input_tokens,
    outputTokens: output_tokens,
  }
}
```

---

## 2. Cost estimation — pricing table

```typescript
// src/models.ts
export const MODEL_PRICING: Record<string, { inputPer1M: number; outputPer1M: number }> = {
  'claude-haiku-4-5-20251001': { inputPer1M: 0.80,  outputPer1M: 4.00 },
  'claude-sonnet-4-6':         { inputPer1M: 3.00,  outputPer1M: 15.00 },
  'claude-opus-4-6':           { inputPer1M: 15.00, outputPer1M: 75.00 },
}

export function estimateCost(model: string, inputTokens: number, outputTokens: number): number {
  const pricing = MODEL_PRICING[model]
  if (!pricing) return 0
  return (inputTokens / 1_000_000) * pricing.inputPer1M
       + (outputTokens / 1_000_000) * pricing.outputPer1M
}

export function formatCost(usd: number): string {
  if (usd < 0.01) return `<$0.01`
  if (usd < 1)    return `$${usd.toFixed(3)}`
  return `$${usd.toFixed(2)}`
}
```

Note: update pricing from the Anthropic pricing page when models change.

---

## 3. Run summary — show cost after each run

After a batch run, show a one-line cost summary:

```typescript
// src/runner.ts
interface RunStats {
  calls:        number
  inputTokens:  number
  outputTokens: number
  totalCost:    number
}

export function printRunSummary(stats: RunStats, model: string): void {
  const cost = formatCost(stats.totalCost)
  process.stdout.write(
    `\n  \x1b[2m${stats.calls} Claude calls · `
    + `${(stats.inputTokens + stats.outputTokens).toLocaleString()} tokens · `
    + `${cost}\x1b[0m\n`
  )
}
```

Example output:
```
  12 Claude calls · 48,234 tokens · $0.143
```

---

## 4. Accumulate across a batch run

```typescript
// src/runner.ts
const stats: RunStats = { calls: 0, inputTokens: 0, outputTokens: 0, totalCost: 0 }

for (const item of items) {
  const result = await callClaude(buildPrompt(item))
  stats.calls++
  stats.inputTokens  += result.inputTokens
  stats.outputTokens += result.outputTokens
  stats.totalCost    += estimateCost(MODELS.smart, result.inputTokens, result.outputTokens)
}

printRunSummary(stats, MODELS.smart)
```

---

## 5. HUD config screen — cumulative spend

Show total spend from `usage.jsonl` in the config/keys screen:

```typescript
// In HUD config screen
import { readFileSync, existsSync } from 'fs'

function readCumulativeSpend(): number {
  const USAGE_FILE = join(import.meta.dir, '..', '.propane', 'logs', 'usage.jsonl')
  if (!existsSync(USAGE_FILE)) return 0

  let total = 0
  for (const line of readFileSync(USAGE_FILE, 'utf8').trim().split('\n').filter(Boolean)) {
    try {
      const e = JSON.parse(line)
      if (e.type === 'ai') {
        total += estimateCost(e.model, e.inputTokens ?? 0, e.outputTokens ?? 0)
      }
    } catch { /* skip malformed lines */ }
  }
  return total
}

const spend = readCumulativeSpend()
process.stdout.write(`  Estimated spend        ${formatCost(spend)}\n`)
```

---

## 6. Streaming — capture usage from final event

Streaming responses return usage in the `message_stop` event, not during the stream:

```typescript
const stream = anthropic.messages.stream({ model, max_tokens: 4096, messages })

for await (const event of stream) {
  if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
    process.stdout.write(event.delta.text)
  }
}

// Usage is on the final message object
const finalMessage = await stream.finalMessage()
const { input_tokens, output_tokens } = finalMessage.usage
logUsage({ type: 'ai', model, inputTokens: input_tokens, outputTokens: output_tokens })
```

---

## Rules

- Capture tokens from every API call — don't estimate from prompt length
- Log usage to `usage.jsonl` via `logUsage()` — same pattern as other events
- Show cost per run, not just token counts — users think in dollars
- Update `MODEL_PRICING` when Anthropic changes rates — it's the single source of truth
- Never block on cost calculations — compute from logged data, not live API calls
