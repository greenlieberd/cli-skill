# Guide 01 — Folder Structure

Every Propane CLI follows this layout. Deviation requires a reason written in CLAUDE.md.

## Canonical structure

```
<name>/
  package.json         bun + scripts (hud, run, test, mcp)
  .env                 API keys — gitignored, never committed
  .gitignore           see "What to ignore" below
  CLAUDE.md            agent instructions for this project (references .cli/)

  .cli/                planning and architecture context — committed, Claude Code reads this
    CONTEXT.md         loaded by Claude Code: purpose, architecture, conventions, do-nots
    DECISIONS.md       why each architecture choice was made (interface, AI tier, sources)
    PLAN.md            living build plan with checkboxes — /fix-cli reads and updates this

  manifest.json        machine-readable capability declaration (see Guide 05)

  src/
    cli.ts             entry point + command router (switch statement)
    hud.ts             ANSI HUD screen loop (HUD-style only)
    models.ts          ALL model IDs — one place, never elsewhere
    configure.ts       loadEnv() + maskValue()
    mcp.ts             MCP stdio server (if Claude Desktop integration needed)
    server.ts          Bun HTTP server for browser view (if needed)

    sources/           one file per external data source
      types.ts         SourceResult interface — all sources import from here
      <name>.ts        one source per file

    lib/               pure utility functions, no side effects
      prompts.ts       prompt template filling: fill(template, vars)
      format.ts        output formatters (markdown, html, etc.)

    core/              shared business logic (if multi-interface)
      runner.ts        async generator emitting RunEvent
      types.ts         RunEvent type union

  cli/                 Ink wizard components (wizard-style only)
    index.tsx          entry: render(<App />)
    App.tsx            step state machine
    components/
      Frame.tsx        border, progress dots, footer hints
      SelectList.tsx   single-select with arrow keys
      MultiSelectList.tsx
      TextInput.tsx    wraps ink-text-input

  ui/                  browser view (if server.ts exists)
    index.html         single file, vanilla JS, no framework
    style.css          optional — inline styles preferred for portability

  tests/
    *.test.ts          bun:test — one file per domain

  .propane/            runtime state — gitignored
    index.json         toggle/on-off state
    styles/            saved JSON presets
    logs/
      errors.jsonl     append-only error log

  output/              generated files — gitignored
  .cache/              HTTP response cache — gitignored
  .fonts/              cached font buffers — gitignored
```

## Naming rules

- Directories: lowercase, no hyphens except in `cli-skill` (that's the plugin name)
- Source files: `camelCase.ts`
- Components: `PascalCase.tsx`
- Config files: lowercase (`config.ts`, `models.ts`, `topics.ts`)
- Guide files: `01-name.md` (numbered, kebab-case)
- Output files: `YYYY-MM-DD-<slug>.<ext>` (datestamped)

## What to gitignore

```gitignore
node_modules/
.env
output/
.cache/
.fonts/
.propane/index.json
.propane/logs/
bun.lockb        # only if not sharing with team
```

Always commit:
- `config.ts`, `topics.ts`, `competitors.json`, `voice.md` — source-controlled config
- `manifest.json` — capability declaration
- `CLAUDE.md`, `PLAN.md`
- `tests/` — all test files

## File size rules

- `cli.ts` — under 80 lines. Router only. No business logic.
- `hud.ts` — under 300 lines. Split into screen functions if growing.
- `App.tsx` — under 150 lines. Extract step components when adding steps.
- `server.ts` — under 100 lines. One file, no routing framework.
- `ui/index.html` — under 300 lines. Inline CSS and JS. No build step.

## When to add `core/`

Add `src/core/` only when the CLI has two or more interfaces (terminal + browser, or terminal + MCP). The `runner.ts` async generator is the shared computation layer — it should know nothing about how results are displayed.

## package.json scripts

```json
{
  "scripts": {
    "hud":    "bun src/cli.ts",
    "run":    "bun src/cli.ts run",
    "test":   "bun test",
    "mcp":    "bun src/mcp.ts",
    "serve":  "bun src/server.ts"
  }
}
```

Always include `hud` as the default entry. Never use `start` or `dev` — this is not a web app.
