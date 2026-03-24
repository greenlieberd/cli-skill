# Guide 02 — UI Patterns

Propane CLIs have two display modes: **terminal** (always present) and **browser** (optional, launched on demand). The browser view is a disposable HTML file — never a separate app.

## When to open a browser view

Open a browser view when the output is better read than navigated:
- Long generated documents (reports, battlecards, content drafts)
- Side-by-side comparisons (before/after, competitor vs Propane)
- Streamed AI output that benefits from markdown rendering
- Any output with tables, charts, or images

Do NOT open a browser view for:
- Simple success/fail status
- Short text output (< 20 lines)
- Config editing
- File selection

## The chat-style UI

The default browser view is a **chat layout** — input at the bottom, output scrolling up. This pattern maps cleanly to the CLI's stream of events: each event is a message bubble.

```html
<!-- ui/index.html — complete, self-contained, no dependencies -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CLI_NAME</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0 }
    body {
      font-family: 'Berkeley Mono', 'JetBrains Mono', monospace;
      background: #0a0a0a; color: #e0e0e0;
      display: flex; flex-direction: column; height: 100vh;
    }
    header {
      padding: 12px 20px; border-bottom: 1px solid #222;
      display: flex; align-items: center; gap: 12px;
    }
    header h1 { font-size: 14px; color: #f0a500; letter-spacing: 0.1em }
    #status { font-size: 12px; color: #555 }
    #messages {
      flex: 1; overflow-y: auto; padding: 20px;
      display: flex; flex-direction: column; gap: 12px;
    }
    .msg {
      max-width: 80%; padding: 10px 14px; border-radius: 8px;
      font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word;
    }
    .msg.system  { background: #111; color: #888; font-size: 12px; align-self: center }
    .msg.ai      { background: #1a1a1a; border: 1px solid #333; align-self: flex-start }
    .msg.user    { background: #1e3a1e; border: 1px solid #2a5a2a; align-self: flex-end }
    .msg.error   { background: #1a0a0a; border: 1px solid #5a2a2a; color: #ff6b6b }
    #input-bar {
      padding: 16px 20px; border-top: 1px solid #222;
      display: flex; gap: 10px;
    }
    #input {
      flex: 1; background: #111; border: 1px solid #333; border-radius: 6px;
      padding: 10px 14px; color: #e0e0e0; font-family: inherit; font-size: 13px;
      outline: none; resize: none;
    }
    #input:focus { border-color: #f0a500 }
    #send {
      background: #f0a500; color: #0a0a0a; border: none; border-radius: 6px;
      padding: 10px 18px; font-size: 13px; font-weight: 600; cursor: pointer;
    }
    #send:hover { background: #ffc020 }
  </style>
</head>
<body>
  <header>
    <h1>&#9658;&#9658; CLI_NAME</h1>
    <span id="status">connecting...</span>
  </header>
  <div id="messages"></div>
  <div id="input-bar">
    <textarea id="input" rows="1" placeholder="Type a message or command..."></textarea>
    <button id="send">Send</button>
  </div>

  <script>
    const messages = document.getElementById('messages')
    const status   = document.getElementById('status')
    const input    = document.getElementById('input')
    const sendBtn  = document.getElementById('send')

    // Always use textContent — never innerHTML — for user/AI content
    function addMsg(text, type) {
      const el = document.createElement('div')
      el.className = 'msg ' + (type || 'ai')
      el.textContent = text
      messages.appendChild(el)
      messages.scrollTop = messages.scrollHeight
      return el
    }

    // ── SSE: receive events from CLI ──────────────────────────────────
    const es = new EventSource('/events')
    es.addEventListener('open',    () => { status.textContent = 'connected' })
    es.addEventListener('error',   () => { status.textContent = 'disconnected' })
    es.addEventListener('message', e => {
      const event = JSON.parse(e.data)
      if (event.type === 'start')    { status.textContent = event.label; addMsg(event.label, 'system') }
      if (event.type === 'progress') { status.textContent = event.label }
      if (event.type === 'log')      addMsg(event.message, 'system')
      if (event.type === 'result')   addMsg(typeof event.data === 'string' ? event.data : JSON.stringify(event.data, null, 2), 'ai')
      if (event.type === 'error')    addMsg(event.message, 'error')
      if (event.type === 'done')     { status.textContent = 'done'; es.close() }
    })

    // ── File watch: re-render when the output file changes ────────────
    const fileEs = new EventSource('/file-watch')
    fileEs.addEventListener('message', e => {
      const event = JSON.parse(e.data)
      addMsg(event.content, 'ai')
    })

    // ── Send: POST text back to CLI ───────────────────────────────────
    async function send() {
      const text = input.value.trim()
      if (!text) return
      addMsg(text, 'user')
      input.value = ''
      input.style.height = 'auto'
      try {
        await fetch('/message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        })
      } catch (err) {
        addMsg('Failed to send: ' + err.message, 'error')
      }
    }

    sendBtn.addEventListener('click', send)
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
    })
    input.addEventListener('input', () => {
      input.style.height = 'auto'
      input.style.height = Math.min(input.scrollHeight, 160) + 'px'
    })
  </script>
</body>
</html>
```

## Document viewer variant

For read-only rendered content (markdown reports, battlecards) — polls for file updates:

```html
<div id="doc"></div>
<script>
  let lastContent = null
  async function poll() {
    const res = await fetch('/api/content')
    const { text } = await res.json()
    if (text !== lastContent) {
      lastContent = text
      // Set as plain text — use a server-side markdown→HTML conversion
      // if rich rendering is needed, and set via textContent on pre-rendered safe HTML
      document.getElementById('doc').textContent = text
    }
  }
  setInterval(poll, 2000)
  poll()
</script>
```

For markdown rendering: convert markdown → HTML **on the server** (in Bun), send pre-rendered safe HTML, and set it via `textContent` on a `<pre>` or return it as a complete page response.

## Rules

- One HTML file. Inline CSS. Inline JS. No `<script src>`, no `<link rel="stylesheet">`.
- No npm packages in the browser. No React, Vue, or bundler.
- Max 300 lines per HTML file. If it grows beyond that, simplify — don't add code.
- Always use `textContent` for dynamic content. Never `innerHTML` with user or AI output.
- Dark background (`#0a0a0a`), monospace font, gold accent (`#f0a500`) — matches terminal palette.
- Always include a `/health` endpoint so the UI can show connection status.
- Replace `CLI_NAME` in the template with the actual project name at scaffold time.
