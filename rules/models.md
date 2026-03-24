---
name: models
description: Model tier selection (Haiku/Sonnet/Opus), src/models.ts convention, streaming, caching, and two-tier patterns.
metadata:
  tags: models, claude, haiku, sonnet, streaming, tokens
---

# Models

> Prerequisites: `@anthropic-ai/sdk` installed, `ANTHROPIC_API_KEY` in `.env`, `src/models.ts` and `src/configure.ts` in the project.

---

## models.ts — the only place model IDs live

```typescript
// src/models.ts
// Add only the tiers your project uses. Remove what you don't need.
export const MODELS = {
  fast:  { id: 'claude-haiku-4-5-20251001', maxTokens: 2048  },
  smart: { id: 'claude-sonnet-4-6',         maxTokens: 8000  },
  // write: { id: 'claude-opus-4-6',         maxTokens: 4000  },
} as const

export type ModelKey = keyof typeof MODELS
```

**When to use each tier:**
- `fast` — routing, classification, 1-sentence extraction, yes/no decisions. Cheap. Sub-second.
- `smart` — content generation, analysis, long context, complex reasoning. Default.
- `write` — final copy, creative output, highest quality needed. Use sparingly.

Never hardcode model ID strings anywhere else. The hook will warn if you do.

---

## Basic call

```typescript
import Anthropic from '@anthropic-ai/sdk'
import { MODELS } from './models.ts'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

const msg = await anthropic.messages.create({
  model:      MODELS.smart.id,
  max_tokens: MODELS.smart.maxTokens,
  messages: [{ role: 'user', content: 'Summarize this in 3 bullets:\n\n' + text }],
})

const result = msg.content[0].type === 'text' ? msg.content[0].text : ''
```

---

## System prompt with caching

Use prompt caching for stable system prompts (the same system prompt re-used across calls). Reduces cost and latency on repeated calls.

```typescript
const msg = await anthropic.messages.create({
  model:      MODELS.smart.id,
  max_tokens: MODELS.smart.maxTokens,
  system: [
    {
      type: 'text',
      text: SYSTEM_PROMPT,  // the stable part — cached
      cache_control: { type: 'ephemeral' },
    },
  ],
  messages: [{ role: 'user', content: userQuery }],  // the variable part
})
```

When to cache: system prompts over ~1000 tokens that you use more than twice per session.

---

## Streaming output to terminal

```typescript
const stream = await anthropic.messages.stream({
  model:      MODELS.smart.id,
  max_tokens: MODELS.smart.maxTokens,
  messages: [{ role: 'user', content: prompt }],
})

process.stdout.write('\n  ')  // indent
for await (const event of stream) {
  if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
    process.stdout.write(event.delta.text)
  }
}
process.stdout.write('\n')

const final = await stream.finalMessage()
// final.usage.input_tokens, final.usage.output_tokens
```

---

## Streaming to Ink (wizard step)

```tsx
const StepGenerating: React.FC<{ prompt: string; onDone: (text: string) => void }> = ({ prompt, onDone }) => {
  const [text, setText] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    async function run() {
      const anthropic = new Anthropic()
      const stream = await anthropic.messages.stream({
        model: MODELS.smart.id,
        max_tokens: MODELS.smart.maxTokens,
        messages: [{ role: 'user', content: prompt }],
      })
      for await (const event of stream) {
        if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
          setText(t => t + event.delta.text)
        }
      }
      setDone(true)
      onDone(text)
    }
    run()
  }, [])

  return (
    <Box flexDirection="column">
      {!done && <Text color="yellow">Generating...</Text>}
      <Text>{text}</Text>
    </Box>
  )
}
```

---

## Two-tier call pattern

Use fast for decisions, smart for output:

```typescript
// Step 1: fast model classifies the input (cheap)
const category = await anthropic.messages.create({
  model:      MODELS.fast.id,
  max_tokens: 50,
  messages: [{
    role: 'user',
    content: `Classify this as one of: bug_report, feature_request, question, other.\nRespond with just the category.\n\n${input}`,
  }],
})
const type = category.content[0].text?.trim()

// Step 2: smart model generates the response (only for complex types)
if (type === 'feature_request') {
  const analysis = await anthropic.messages.create({
    model:      MODELS.smart.id,
    max_tokens: MODELS.smart.maxTokens,
    messages: [{ role: 'user', content: ANALYSIS_PROMPT + input }],
  })
}
```

---

## Error handling

```typescript
async function callClaude(prompt: string): Promise<string> {
  try {
    const msg = await anthropic.messages.create({ ... })
    return msg.content[0].type === 'text' ? msg.content[0].text : ''
  } catch (err: any) {
    if (err.status === 401) throw new Error('ANTHROPIC_API_KEY is invalid — check .env')
    if (err.status === 429) throw new Error('Rate limited — wait 60s and retry')
    if (err.status === 529) throw new Error('Claude API is overloaded — retry in a few seconds')
    throw new Error(`Claude API error: ${err.message}`)
  }
}
```

---

## Piped mode (no API key — runs inside Claude Code)

When `distribution: piped` — the tool runs inside a Claude Code session and doesn't need its own API key. Structure output as text that Claude Code reads directly:

```typescript
// Instead of calling the API, write structured output to stdout
// Claude Code (the parent session) reads this and acts on it
process.stdout.write(JSON.stringify({ type: 'analysis', data: analysisResults }) + '\n')
process.stdout.write(JSON.stringify({ type: 'recommendation', text: 'Here are 3 improvements...' }) + '\n')
```

This mode has no `src/models.ts` or `@anthropic-ai/sdk` dependency.
