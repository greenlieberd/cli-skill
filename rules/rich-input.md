---
name: rich-input
description: Multi-line input, bracketed paste, image input to Claude, stdin piping, and inline text capture within an ANSI HUD.
metadata:
  tags: input, paste, image, stdin, multiline, claude
---

# Rich Input

> Platform: macOS (Terminal.app, iTerm2, Warp — all support bracketed paste mode).

Input in CLIs goes well beyond "press a key." Users want to paste multi-line text, drop image paths, pipe content from other commands, and capture a URL without switching windows. This rule covers all of it.

## Prerequisites

- Raw mode enabled for ANSI HUDs (see `hud-screens.md`)
- For image input to Claude: `@anthropic-ai/sdk` ≥ 0.20 with `vision` support
- `src/configure.ts` with `loadEnv()` (see `environment-setup.md`)

---

## 1. Inline text input in ANSI HUD — modal capture

Press a key to enter input mode, capture text character by character, submit or cancel:

```typescript
// src/hud.ts
interface InputState {
  active:  boolean
  buffer:  string
  prompt:  string
  onSubmit: (value: string) => void
  onCancel: () => void
}

let input: InputState = { active: false, buffer: '', prompt: '', onSubmit: () => {}, onCancel: () => {} }

function startInput(prompt: string, onSubmit: (v: string) => void, onCancel: () => void): void {
  input = { active: true, buffer: '', prompt, onSubmit, onCancel }
}

// In keypress handler:
if (input.active) {
  if (key === '\x03') { input.active = false; input.onCancel(); return }          // ctrl+c
  if (key === '\x1b') { input.active = false; input.onCancel(); return }          // ESC
  if (key === '\r')   { input.active = false; input.onSubmit(input.buffer); return } // Enter
  if (key === '\x7f') { input.buffer = input.buffer.slice(0, -1); return }        // Backspace
  if (key.length === 1 && key >= ' ') { input.buffer += key; return }             // printable
}

// Draw the input line at bottom of screen:
function drawInputLine(): void {
  if (!input.active) return
  process.stdout.write(`\n  ${A.info}${input.prompt}${A.reset} ${A.bold}${input.buffer}${A.reset}▌${A.dim}  (Enter submit · Esc cancel)${A.reset}\x1b[K`)
}
```

Usage:
```typescript
// User presses 'a' to add a URL
if (key === 'a') {
  startInput('Add URL:', (url) => {
    try { new URL(url); addSource(url) }
    catch { showError(`Invalid URL: ${url}`) }
  }, () => {})
}
```

---

## 2. Bracketed paste — capture multi-line clipboard content

Bracketed paste mode wraps pasted content in `\x1b[200~...text...\x1b[201~` so you can detect it and handle newlines correctly (without them firing as Enter):

```typescript
// src/hud.ts — enable at startup
process.stdout.write('\x1b[?2004h')   // enable bracketed paste

// Disable on exit (important)
process.on('exit', () => process.stdout.write('\x1b[?2004l'))
process.on('SIGINT', () => { process.stdout.write('\x1b[?2004l'); process.exit(0) })

// In keypress handler:
let pasteBuffer = ''
let inPaste = false

function handleKey(key: string): void {
  if (key === '\x1b[200~') { inPaste = true; pasteBuffer = ''; return }
  if (key === '\x1b[201~') {
    inPaste = false
    onPastedContent(pasteBuffer)   // handle the full pasted block
    return
  }
  if (inPaste) { pasteBuffer += key; return }
  // ... normal key handling
}
```

---

## 3. Image input to Claude — vision API

Pass image files or URLs directly to Claude's vision API:

```typescript
// src/ai.ts
import Anthropic from '@anthropic-ai/sdk'
import { readFileSync, existsSync } from 'fs'

const anthropic = new Anthropic()

type ImageMediaType = 'image/jpeg' | 'image/png' | 'image/gif' | 'image/webp'

export async function callClaudeWithImage(
  prompt: string,
  imagePath: string
): Promise<string> {
  if (imagePath.startsWith('http')) {
    // URL — pass as url_source
    const response = await anthropic.messages.create({
      model: MODELS.smart,
      max_tokens: 2048,
      messages: [{
        role: 'user',
        content: [
          { type: 'image', source: { type: 'url', url: imagePath } },
          { type: 'text', text: prompt },
        ],
      }],
    })
    return response.content[0].type === 'text' ? response.content[0].text : ''
  }

  // Local file — base64 encode
  if (!existsSync(imagePath)) throw new Error(`Image not found: ${imagePath}`)
  const data      = readFileSync(imagePath).toString('base64')
  const ext       = imagePath.split('.').at(-1)?.toLowerCase() ?? 'jpeg'
  const mediaType = (`image/${ext}` as ImageMediaType)

  const response = await anthropic.messages.create({
    model: MODELS.smart,
    max_tokens: 2048,
    messages: [{
      role: 'user',
      content: [
        { type: 'image', source: { type: 'base64', media_type: mediaType, data } },
        { type: 'text', text: prompt },
      ],
    }],
  })
  return response.content[0].type === 'text' ? response.content[0].text : ''
}
```

---

## 4. Stdin piping — read from another command

When invoked as part of a Unix pipe (`echo "..." | bun hud`), read stdin before starting the UI:

```typescript
// src/cli.ts
async function readStdin(): Promise<string | null> {
  if (process.stdin.isTTY) return null   // no pipe — interactive mode
  const chunks: Buffer[] = []
  for await (const chunk of process.stdin) chunks.push(chunk)
  return Buffer.concat(chunks).toString('utf8').trim() || null
}

const piped = await readStdin()
if (piped) {
  // Use piped content as input instead of fetching from sources
  const result = await callClaude(`Analyze: ${piped}`)
  process.stdout.write(result + '\n')
  process.exit(0)
}
// No pipe — start interactive HUD
runHud()
```

---

## 5. Image drag-and-drop from terminal

Terminal apps let users drag files onto the window, which pastes the file path as text. Detect image file paths in the input buffer:

```typescript
const IMAGE_EXTS = ['.png', '.jpg', '.jpeg', '.gif', '.webp']

function detectImagePath(text: string): string | null {
  const trimmed = text.trim().replace(/^['"]|['"]$/g, '')   // strip quotes
  if (IMAGE_EXTS.some(ext => trimmed.toLowerCase().endsWith(ext))) {
    return trimmed
  }
  return null
}

// In paste handler:
function onPastedContent(content: string): void {
  const imagePath = detectImagePath(content)
  if (imagePath) {
    analyzeImage(imagePath)
  } else {
    processTextInput(content)
  }
}
```

---

## Rules

- Enable bracketed paste mode at startup — disabling it on exit is mandatory
- Inline HUD input uses modal state — keyboard input routes to the buffer, not the HUD
- For local images: base64 encode; for remote images: pass the URL directly (cheaper, no encoding)
- Read stdin before starting the UI — if piped, process and exit; if TTY, run interactively
- Detect image file paths from pasted content — drag-and-drop from Finder pastes the path
