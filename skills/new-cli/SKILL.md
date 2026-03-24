---
name: new-cli
description: Use this skill when the user wants to build a new CLI tool, says "build a new CLI", "create a CLI", "I need a terminal tool for X", "start a CLI project", or asks to scaffold a Bun/Ink/ANSI command-line application. Also use when extending an existing CLI with new capabilities.
argument-hint: "[project-name or path]"
model: sonnet
effort: high
context: fork
allowed-tools: Read, Write, Edit, Glob, Grep, LS, Bash
---

# New CLI Scaffold

Build a new Propane CLI project from scratch using Bun, with either an Ink wizard UI or an ANSI HUD. Follow these steps exactly — do not skip or combine them.

## Context loaded at runtime

Current directory: !`pwd`

Environment check:
!`echo "bun: $(bun --version 2>/dev/null || echo 'NOT INSTALLED — will offer to install')" && echo "git: $(git rev-parse --is-inside-work-tree 2>/dev/null && echo 'repo exists' || echo 'no git repo')" && echo "package.json: $([ -f package.json ] && cat package.json | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"name\",\"?\"))' 2>/dev/null || echo none)"`

Guide files: !`ls "${CLAUDE_SKILL_DIR}/../../guides/" 2>/dev/null`
Example files: !`ls "${CLAUDE_SKILL_DIR}/examples/" 2>/dev/null`

---

## Step 0 — Handle arguments + environment check

**Arguments:** If `$ARGUMENTS` contains a name (e.g. `/new-cli my-tool`), use it to pre-fill question 1 and skip asking it. If `$ARGUMENTS` is a path to an existing project, run the `cli-explorer` agent on it first (Step 1), then return here.

**Environment check:** Before asking anything else, check the runtime context above and handle any blockers:

- **Bun not installed** → Tell the user and ask: "Bun is required. Should I install it? (runs `curl -fsSL https://bun.sh/install | bash`)" — wait for confirmation before running.
- **No git repo** → After confirming the project name, ask: "No git repo found here. Should I run `git init` and create a `.gitignore`?"
- **Existing package.json found** → Flag it: "There's already a `package.json` here for `[name]`. Are we extending this project or starting in a new subfolder?"

---

## Step 1 — Explore (only if extending an existing project)

If the user mentions an existing CLI or passes a path, launch the `cli-explorer` agent:
- Pass the path
- Ask for: entry points, existing patterns, key dependencies, what already works
- Use findings to skip questions the existing code already answers

If starting fresh, skip to Step 2.

---

## Step 2 — Planning interview (one message, all questions at once)

Ask only the questions not already answered by `$ARGUMENTS` or Step 1 findings. Use plain language — assume the user is not an AI expert:

```
Let's plan this out. Answer whatever applies:

1. Name — what's this CLI called? (lowercase, hyphens ok, e.g. "my-tool")
2. Purpose — one sentence: what problem does it solve? What triggers someone to run it?

3. Interface style — pick one:
   a) Dashboard — always-on screen you navigate with arrow keys (good for: monitoring, browsing output, running tasks)
   b) Wizard — step-by-step questions one at a time (good for: setup flows, generation tasks, anything with choices)
   c) Commands only — run specific commands like `bun run export` (good for: scripting, automation, no interactive UI)

4. Does it use AI?
   a) No — pure utility, no Claude calls
   b) Yes, via API key — needs ANTHROPIC_API_KEY in .env
   c) Yes, via Claude Code — no API key needed, runs inside this session (best for personal tools)
   d) Both fast + slow — fast calls for quick tasks (cheap), smart calls for complex ones (tell me what each does)

5. External data — where does it get information?
   a) Local files only
   b) Specific web APIs (list them: Reddit, Firecrawl, Perplexity, etc.)
   c) Web scraping
   d) None

6. Output — where does it put results?
   a) Terminal only
   b) Files (markdown, HTML, JSON) to an output/ folder
   c) A browser view that opens automatically
   d) Multiple of the above

7. Distribution — how will it be used?
   a) Personal — I run it from the project folder
   b) Team — others clone the repo and run it locally
   c) Global — installed system-wide with `bun install -g`

8. Claude Desktop integration — should Claude be able to query this tool's output in a chat?
   (This adds an MCP server — useful if you generate reports, content, or structured data)
```

Wait for all answers before proceeding.

---

## Step 2b — Dependency setup

After the user answers the questions from Step 2, check which packages will be needed and offer to set them up:

```
Based on your answers, here's what this project needs:

✓ bun (runtime)                         [already installed / needs install]
✓ @anthropic-ai/sdk                     always required
[if wizard] ✓ ink ^5  + react ^19       Ink terminal UI
[if wizard] ✓ ink-text-input ^6         text fields in wizard
[if wizard] ✓ @types/react + typescript dev deps
[if mcp]    ✓ @modelcontextprotocol/sdk MCP server

Should I create the project folder and run `bun install` now?
(I'll write package.json first, then install — you can review before I run anything)
```

Wait for confirmation. Then:
1. Create the project folder: `mkdir -p <name> && cd <name>`
2. Write `package.json` (Step 4 item 4)
3. Run `bun install` in the project folder
4. Run `git init` if the user confirmed it in Step 0
5. Continue generating remaining files

**Do not run `bun install` without explicit user confirmation.**

---

## Step 3 — Architecture decision

For non-trivial CLIs (3+ commands or 2+ external APIs), launch two `cli-architect` agents in parallel:
- Agent A argument: `minimal` — fewest files, fastest to ship
- Agent B argument: `modular` — clean separation, easy to extend

Present both approaches with a recommendation. Wait for the user to choose.

For simple CLIs (1-2 commands, no external APIs), pick minimal and proceed.

---

## Step 4 — Generate files in order

Write each file completely before moving to the next. Show the filename before writing.

**Required files (always):**
1. `PLAN.md` — 3–5 bullets on what we're building and why
2. `CLAUDE.md` — architecture notes (use template in Step 8)
3. `.gitignore` — node_modules, .env, output/, .propane/, .cache/
4. `package.json` — scripts: hud, run, test; deps based on answers
5. `src/models.ts` — only the tiers this project uses (see Step 5)
6. `src/configure.ts` — always identical (see Step 6)
7. `src/cli.ts` — command router, under 80 lines (see Step 7)

**If HUD style:**
- `src/hud.ts` — ANSI screen loop with ASCII art header (see guides/02-ui-patterns.md)

**If Wizard style:**
- `cli/index.tsx` — `render(<App />)`
- `cli/App.tsx` — step state machine with NEXT/PREV maps
- `cli/components/Frame.tsx` — border, ✓/◉/○ progress dots, footer hints
- `cli/components/SelectList.tsx` — arrow-key navigation with space/enter select
- `cli/components/TextInput.tsx` — wraps ink-text-input, ← goes back

**If external APIs:**
- `src/sources/types.ts` — SourceResult interface (see Step 9)
- `src/sources/<api>.ts` — one stub per API, returns SourceResult (never throws)

**If browser view:**
- `src/server.ts` — Bun.serve with /events SSE + /health
- `ui/index.html` — self-contained HTML (see guides/02-ui-patterns.md template)

**If MCP:**
- `src/mcp.ts` — stdio MCP server (see guides/05-mcp-patterns.md)

**Always last:**
- `tests/cli.test.ts` — bun:test suite (configure, models, at least one source)

---

## Step 5 — models.ts pattern

Only include the tiers this project uses. Name by purpose, not model name:

```typescript
// src/models.ts — single source of truth for all model IDs
// Tiers: fast (cheap, quick tasks) | smart (capable, complex tasks)
export const MODELS = {
  fast:  { id: 'claude-haiku-4-5-20251001', maxTokens: 2048 },
  smart: { id: 'claude-sonnet-4-6',         maxTokens: 8000 },
} as const
export type ModelKey = keyof typeof MODELS
```

Rules:
- Never hardcode model strings anywhere else in the project
- Use prompt caching (`cache_control: { type: 'ephemeral' }`) for stable system prompts
- Add a third tier only if there's a distinct use case (e.g. `write` → Opus for final copy)

---

## Step 6 — configure.ts (always identical)

```typescript
// src/configure.ts — reads .env file into process.env
import { readFileSync, existsSync } from 'fs'
import { join } from 'path'

export function loadEnv(): void {
  const path = join(import.meta.dir, '..', '.env')
  if (!existsSync(path)) return
  for (const line of readFileSync(path, 'utf8').split('\n')) {
    const eq = line.indexOf('=')
    if (eq < 1) continue
    const key = line.slice(0, eq).trim()
    const val = line.slice(eq + 1).trim()
    if (key && !process.env[key]) process.env[key] = val
  }
}

export function maskValue(v: string): string {
  if (!v) return '(not set)'
  return v.slice(0, 4) + '•'.repeat(Math.min(v.length - 8, 20)) + v.slice(-4)
}
```

Copy this verbatim. Do not modify it.

---

## Step 7 — cli.ts (command router)

Keep under 80 lines. All logic lives in imported modules:

```typescript
// src/cli.ts — command router
import { loadEnv } from './configure.ts'
loadEnv()

const args = process.argv.slice(2)
switch (args[0]) {
  case undefined:
  case 'hud':  await import('./hud.ts').then(m => m.runHud()); break
  case 'run':  await import('./run.ts').then(m => m.cmdRun(args.slice(1))); break
  default:
    process.stderr.write(`Unknown command: ${args[0]}\nUsage: bun hud\n`)
    process.exit(1)
}
```

For wizard-style CLIs, replace the hud import with:
```typescript
case 'hud': {
  const { render } = await import('ink')
  const { default: React } = await import('react')
  const { App } = await import('../cli/App.tsx')
  render(React.createElement(App))
  break
}
```

---

## Step 8 — CLAUDE.md template

```markdown
# CLAUDE.md

## What this is
[ONE_LINE_PURPOSE]

## Run it
\`\`\`
bun hud          # main interface
bun test         # run tests
bun run mcp      # MCP server (if applicable)
\`\`\`

## Architecture
- Entry: `src/cli.ts` → switch router
- [HUD: `src/hud.ts` — ANSI screen loop | Wizard: `cli/App.tsx` — Ink step machine]
- `src/models.ts` — all model IDs (never hardcode strings elsewhere)
- `src/configure.ts` — loads .env, masks keys for display
- `src/sources/` — one file per external data source, all return SourceResult (never throws)
- [Optional: `src/server.ts` + `ui/` — browser view via Bun.serve + SSE]
- [Optional: `src/mcp.ts` — MCP stdio server for Claude Desktop]
- `.propane/` — runtime state, gitignored
- `output/` — generated files, gitignored

## No database
Flat files only. Claude is the query layer. See cli-skill/guides/04-data-philosophy.md.
```

---

## Step 9 — SourceResult pattern

Every external data fetch must return this type — never throw:

```typescript
// src/sources/types.ts
export interface SourceResult {
  source:   string        // machine ID, e.g. 'reddit'
  label:    string        // human label, e.g. 'Reddit r/saas'
  content:  string        // fetched text
  links?:   string[]      // URLs found
  error?:   string        // set if fetch failed — don't throw
  skipped?: boolean       // set if source was toggled off
}

export function sourceError(source: string, label: string, err: unknown): SourceResult {
  return { source, label, content: '', error: String(err) }
}

export function sourceSkip(source: string, label: string): SourceResult {
  return { source, label, content: '', skipped: true }
}
```

Stub pattern for each source file:
```typescript
// src/sources/reddit.ts
import type { SourceResult } from './types.ts'

export async function fetchReddit(query: string): Promise<SourceResult> {
  try {
    const res = await fetch(`https://www.reddit.com/search.json?q=${encodeURIComponent(query)}&limit=10`)
    if (!res.ok) return sourceError('reddit', 'Reddit', `HTTP ${res.status}`)
    const data = await res.json() as any
    const posts = data.data.children.map((c: any) => `${c.data.title}\n${c.data.selftext}`).join('\n\n')
    return { source: 'reddit', label: 'Reddit', content: posts }
  } catch (err) {
    return sourceError('reddit', 'Reddit', err)
  }
}
```

---

## Step 10 — HUD pattern (ANSI style)

Key elements of `src/hud.ts`:

```typescript
// ANSI helpers
const A = {
  clear: '\x1b[2J\x1b[H', hideCursor: '\x1b[?25l', showCursor: '\x1b[?25h',
  reset: '\x1b[0m', bold: '\x1b[1m', dim: '\x1b[2m',
  gold: '\x1b[33m', green: '\x1b[32m', red: '\x1b[31m',
  gray: '\x1b[90m', white: '\x1b[97m', cyan: '\x1b[36m',
} as const
const w = (s: string) => process.stdout.write(s)

// ASCII art header — 6 lines of block letters using Unicode box-drawing
const ASCII_ART = [
  '  ██████╗ ██████╗  ██████╗      ██╗███████╗ ██████╗████████╗',
  '  ██╔══██╗██╔══██╗██╔═══██╗     ██║██╔════╝██╔════╝╚══██╔══╝',
  // ... generate for actual project name
]

// Spinner for async work
const FRAMES = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']

// Key reading (raw mode)
async function readKey(): Promise<string> {
  process.stdin.setRawMode(true)
  return new Promise(resolve => {
    process.stdin.once('data', buf => {
      process.stdin.setRawMode(false)
      resolve(buf.toString())
    })
  })
}

export async function runHud(): Promise<void> {
  // screen loop: render → readKey → update state → render
}
```

---

## Step 11 — Ink Wizard pattern

Key elements for wizard-style CLIs (from `animations/cli/`):

**Frame.tsx** — wraps every step:
- `borderStyle="single" borderColor="green"` at 66 chars wide
- Progress dots: `✓` (done), `◉` (current), `○` (future)
- Footer with keyboard hints: `↑ ↓ navigate   space select   ← back   ctrl+c exit`

**App.tsx** — step state machine:
```typescript
const NEXT: Record<Step, Step> = { step1: 'step2', step2: 'step3', ... }
const PREV: Record<Step, Step> = { step1: 'step1', step2: 'step1', ... }

export const App: React.FC = () => {
  const [step, setStep] = useState<Step>('step1')
  const [answers, setAnswers] = useState<Partial<Answers>>({})
  // switch (step) { case 'step1': return <StepOne onNext={...} onBack={...} /> }
}
```

**SelectList** — single-select:
- `useInput` from ink for ↑/↓ navigation and enter/space to select
- Show `▶` prefix on selected item

**package.json** for wizard-style:
```json
{
  "dependencies": {
    "ink": "^5.0.0",
    "ink-text-input": "^6.0.0",
    "react": "^19.0.0",
    "@anthropic-ai/sdk": "^0.40.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "typescript": "^5.0.0"
  }
}
```

**tsconfig.json** for wizard-style (required for JSX):
```json
{
  "compilerOptions": {
    "target": "ESNext", "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx", "jsxImportSource": "react",
    "strict": true
  }
}
```

---

## Step 12 — Quality review

After all files are generated, launch two `cli-reviewer` agents in parallel:
- `cli-reviewer correctness` — missing imports, wrong paths, broken types, bad async
- `cli-reviewer completeness` — does it match all answers from Step 2?

Apply all fixes before presenting to the user.

---

## Step 13 — Ship checklist

Do not claim "done" until all items are checked:

- [ ] `bun hud` runs without errors
- [ ] ASCII art (HUD) or Frame title (Wizard) renders correctly
- [ ] At least one menu item or wizard step does something real
- [ ] `.env.example` lists all required keys with descriptions
- [ ] `src/models.ts` has no hardcoded model strings elsewhere in the project
- [ ] All sources return `SourceResult` — none throw
- [ ] At least 3 tests pass with `bun test`
- [ ] `output/` and `.propane/` are in `.gitignore`
- [ ] `CLAUDE.md` accurately describes the architecture
- [ ] If browser view: `bun serve` opens UI and connection status shows
- [ ] If MCP: `src/mcp.ts` runs and `manifest.json` has registration instructions

---

## Reference

**Guides** (conceptual patterns + templates):
- Folder layout: `${CLAUDE_SKILL_DIR}/../../guides/01-folder-structure.md`
- UI patterns & HTML template: `${CLAUDE_SKILL_DIR}/../../guides/02-ui-patterns.md`
- File-browser bridge: `${CLAUDE_SKILL_DIR}/../../guides/03-file-browser-bridge.md`
- Data philosophy: `${CLAUDE_SKILL_DIR}/../../guides/04-data-philosophy.md`
- MCP patterns: `${CLAUDE_SKILL_DIR}/../../guides/05-mcp-patterns.md`
- Claude Code patterns: `${CLAUDE_SKILL_DIR}/../../guides/07-claude-code-patterns.md`

**Examples** (copy-paste starting points — adapt, don't copy blindly):
- `${CLAUDE_SKILL_DIR}/examples/models.ts` — ModelKey + tier setup
- `${CLAUDE_SKILL_DIR}/examples/configure.ts` — loadEnv + maskValue (copy verbatim)
- `${CLAUDE_SKILL_DIR}/examples/hud.ts` — complete ANSI HUD with spinner + screen loop
- `${CLAUDE_SKILL_DIR}/examples/App.tsx` — Ink wizard state machine skeleton
- `${CLAUDE_SKILL_DIR}/examples/Frame.tsx` — progress dots + border component
- `${CLAUDE_SKILL_DIR}/examples/SelectList.tsx` — single + multi-select with arrow keys
- `${CLAUDE_SKILL_DIR}/examples/sources/types.ts` — SourceResult interface + helpers
- `${CLAUDE_SKILL_DIR}/examples/package.json` — annotated deps (remove what you don't use)
