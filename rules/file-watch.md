---
name: file-watch
description: Watching files with Bun fs.watch and pushing updates to a browser via SSE.
metadata:
  tags: file-watch, sse, browser, live-reload, bun
---

# File Watch

The pattern: the CLI writes a local file, the browser watches it via SSE, and the browser can write back via HTTP POST. No database. No shared memory. **The file is the truth.**

```
CLI writes file
  └─ Bun fs.watch() detects change
       └─ SSE pushes new content to browser
            └─ Browser renders it
                 └─ User edits or sends a message
                      └─ Browser POSTs to /message
                           └─ Bun handler writes file or invokes CLI action
                                └─ CLI fs.watch() picks up the change
```

## server.ts — the bridge

```typescript
// src/server.ts
import { watch } from 'fs'
import { readFileSync, writeFileSync, existsSync } from 'fs'
import { join } from 'path'
import { fileURLToPath } from 'url'

const __dir = fileURLToPath(new URL('.', import.meta.url))
const WATCHED_FILE = join(__dir, '..', 'output', 'current.md')
const UI_FILE      = join(__dir, 'ui', 'index.html')

// SSE client registry
const sseClients = new Set<ReadableStreamDefaultController<Uint8Array>>()
const fileClients = new Set<ReadableStreamDefaultController<Uint8Array>>()
const encoder = new TextEncoder()

function broadcast(clients: Set<ReadableStreamDefaultController<Uint8Array>>, data: unknown) {
  const msg = encoder.encode(`data: ${JSON.stringify(data)}\n\n`)
  for (const ctrl of clients) {
    try { ctrl.enqueue(msg) } catch { clients.delete(ctrl) }
  }
}

// Watch the output file and broadcast changes
if (existsSync(WATCHED_FILE)) {
  watch(WATCHED_FILE, () => {
    const content = readFileSync(WATCHED_FILE, 'utf8')
    broadcast(fileClients, { content })
  })
}

// Message queue — CLI polls this
const messageQueue: string[] = []

export const server = Bun.serve({
  port: Number(process.env.PORT ?? 3333),

  async fetch(req) {
    const url = new URL(req.url)

    // ── Serve UI ────────────────────────────────────────────────────
    if (url.pathname === '/') {
      return new Response(Bun.file(UI_FILE), {
        headers: { 'Content-Type': 'text/html' }
      })
    }

    // ── Health ──────────────────────────────────────────────────────
    if (url.pathname === '/health') {
      return Response.json({ ok: true })
    }

    // ── SSE: CLI → browser event stream ────────────────────────────
    if (url.pathname === '/events') {
      let ctrl: ReadableStreamDefaultController<Uint8Array>
      const stream = new ReadableStream<Uint8Array>({
        start(c) { ctrl = c; sseClients.add(c) },
        cancel()  { sseClients.delete(ctrl) }
      })
      return new Response(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        }
      })
    }

    // ── SSE: file-watch stream ──────────────────────────────────────
    if (url.pathname === '/file-watch') {
      let ctrl: ReadableStreamDefaultController<Uint8Array>
      const stream = new ReadableStream<Uint8Array>({
        start(c) { ctrl = c; fileClients.add(c) },
        cancel()  { fileClients.delete(ctrl) }
      })
      return new Response(stream, {
        headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' }
      })
    }

    // ── GET current file content ────────────────────────────────────
    if (url.pathname === '/api/content' && req.method === 'GET') {
      const text = existsSync(WATCHED_FILE)
        ? readFileSync(WATCHED_FILE, 'utf8')
        : ''
      return Response.json({ text })
    }

    // ── POST: browser → CLI message ─────────────────────────────────
    if (url.pathname === '/message' && req.method === 'POST') {
      const body = await req.json() as { text: string }
      if (typeof body.text === 'string' && body.text.length < 10000) {
        messageQueue.push(body.text)
      }
      return Response.json({ ok: true })
    }

    // ── POST: browser writes back to file ───────────────────────────
    if (url.pathname === '/api/save' && req.method === 'POST') {
      const body = await req.json() as { content: string }
      if (typeof body.content === 'string') {
        writeFileSync(WATCHED_FILE, body.content, 'utf8')
      }
      return Response.json({ ok: true })
    }

    return new Response('Not found', { status: 404 })
  }
})

// ── Exported helpers for CLI to use ────────────────────────────────────
export function broadcastEvent(event: unknown) {
  broadcast(sseClients, event)
}

export function pollMessages(): string[] {
  return messageQueue.splice(0)
}
```

## CLI reading browser messages

The CLI polls `pollMessages()` while running to handle mid-run user input:

```typescript
// In the main run loop
import { broadcastEvent, pollMessages } from './server.ts'

for await (const event of run(config)) {
  broadcastEvent(event)            // push to browser
  spinStart(event.label ?? '')     // show in terminal

  // Check for browser messages every iteration
  for (const msg of pollMessages()) {
    console.log(`Browser: ${msg}`)
    // handle: abort, inject context, adjust config, etc.
  }
}
```

## CLI writing a file the browser watches

```typescript
// In any CLI command
import { writeFileSync } from 'fs'
import { join } from 'path'

const outFile = join(process.cwd(), 'output', 'current.md')
writeFileSync(outFile, content, 'utf8')
// The browser's /file-watch SSE stream will fire automatically via fs.watch()
```

## Opening the browser

```typescript
// src/server.ts or cli.ts — open after server starts
import { execFileSync } from 'child_process'

const PORT = server.port
process.stdout.write(`\x1b[32m✓\x1b[0m UI at http://localhost:${PORT}\n`)
try {
  // macOS
  execFileSync('open', [`http://localhost:${PORT}`])
} catch {
  // Linux / WSL fallback — just print the URL
}
```

## What this does NOT replace

- The terminal is still the primary interface. The browser is a viewer.
- The CLI always works without the browser open.
- Closing the browser does not stop the CLI.
- The browser never holds state that isn't also in a file — if the browser closes, nothing is lost.
