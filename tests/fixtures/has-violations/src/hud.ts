// VIOLATION: hardcoded model ID in non-models.ts file
// VIOLATION: no resize handler (process.stdout.on('resize', ...))
import Anthropic from '@anthropic-ai/sdk'

const MODEL = 'claude-sonnet-4-6' // should import from src/models.ts

export function runHud() {
  const cols = process.stdout.columns ?? 80
  process.stdout.write('\x1b[2J\x1b[H')
  process.stdout.write(`Dashboard — ${cols} cols wide\n`)
  // Missing: process.stdout.on('resize', redraw)
}
