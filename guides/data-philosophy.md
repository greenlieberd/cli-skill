# Guide 04 — Data Philosophy

Propane CLIs do not have local databases. They do not have schemas, ORMs, migrations, or query layers. When you feel the urge to reach for SQLite, a JSON store, or any persistence abstraction — stop. Read this guide.

## The rule

> **Flat files are the database. Skills and agents are the query layer.**

Every piece of state a CLI needs fits into one of four categories:

| Category | Format | Location | Committed? |
|----------|--------|----------|------------|
| Config (user-set) | `.ts` or `.json` or `.yml` | root or `.propane/` | Yes |
| Output (generated) | `.md`, `.html`, `.json`, `.png` | `output/` | No |
| Runtime state | `.json` (simple key/value toggles) | `.propane/index.json` | No |
| Logs | `.jsonl` (append-only) | `.propane/logs/` | No |

That's it. No other persistence layer.

## Why no database

**Speed.** Adding a database adds: a schema design session, a migration system, a query language, a connection lifecycle, and an ORM. That's a week of scaffolding before you've built anything.

**Portability.** Flat files can be opened in any text editor, committed to git, shared over Slack, read by other CLIs, and fed directly into Claude without an adapter layer.

**Agents as queries.** If you need to "query" data — find the top 5 competitors by score, summarize last week's output, extract insights across 30 files — that's a Claude call, not a SQL query. A Haiku call over 30 markdown files is cheaper, faster, and more flexible than building a query layer.

## Patterns that replace databases

### Replace: "store user preferences in a DB table"
```typescript
// Just a JSON file
const PREFS_FILE = join(CONFIG_DIR, 'prefs.json')
type Prefs = { theme: string; defaultTopic: string; enabledSources: string[] }
function readPrefs(): Prefs { return JSON.parse(readFileSync(PREFS_FILE, 'utf8')) }
function writePrefs(p: Prefs) { writeFileSync(PREFS_FILE, JSON.stringify(p, null, 2)) }
```

### Replace: "query recent runs for the last 7 days"
```typescript
// Glob output files by date prefix, sort, slice
const files = readdirSync(OUTPUT_DIR)
  .filter(f => f.endsWith('.md'))
  .sort()
  .slice(-7)
// Feed to Claude Haiku for summary — no SQL needed
```

### Replace: "full-text search across all reports"
```typescript
// Bun's Grep or simple string search across files
// Or: pass all files to Claude with a search prompt
// For large corpora: use Perplexity or a Claude tool call
```

### Replace: "track which competitors have been processed"
```typescript
// .propane/index.json — simple set of IDs
type IndexState = { processed: string[]; disabled: string[] }
```

### Replace: "cache API responses to avoid re-fetching"
```typescript
// .cache/<source>/<key>.json — file-per-response cache
const cacheFile = join(CACHE_DIR, source, `${hashKey(key)}.json`)
if (existsSync(cacheFile)) return JSON.parse(readFileSync(cacheFile, 'utf8'))
const result = await fetchFromApi(key)
writeFileSync(cacheFile, JSON.stringify(result))
return result
```

## The append-only log

The one structured data store every CLI gets is an append-only `.jsonl` error log:

```typescript
// src/lib/log.ts
import { appendFileSync, mkdirSync, existsSync } from 'fs'
import { join } from 'path'

const LOG_FILE = join(process.cwd(), '.propane', 'logs', 'errors.jsonl')

export function logError(source: string, err: unknown) {
  const entry = JSON.stringify({ ts: new Date().toISOString(), source, error: String(err) })
  try {
    mkdirSync(join(process.cwd(), '.propane', 'logs'), { recursive: true })
    appendFileSync(LOG_FILE, entry + '\n')
  } catch { /* never crash on logging */ }
}
```

Read it back as an array when needed:
```typescript
function readErrors(): Array<{ ts: string; source: string; error: string }> {
  if (!existsSync(LOG_FILE)) return []
  return readFileSync(LOG_FILE, 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l))
}
```

## Skills and agents as the intelligence layer

When you need to do anything intelligent with stored data, use a Claude call — not a query:

```typescript
// "Give me a summary of the last 5 reports"
const reports = getRecentFiles('output', 5).map(f => readFileSync(f, 'utf8'))
const summary = await anthropic.messages.create({
  model: MODELS.fast.id,
  max_tokens: MODELS.fast.maxTokens,
  messages: [{
    role: 'user',
    content: `Summarize these ${reports.length} reports in 5 bullet points:\n\n${reports.join('\n\n---\n\n')}`
  }]
})
```

This is cheaper than building a query layer. It's also smarter — Claude can extract intent, not just data.

## What about large output corpora?

If `output/` grows past ~500 files:
1. Archive old files to `output/archive/YYYY-MM/`
2. Add a `manifest.jsonl` index: `{ file, date, topic, size }` — one line per file
3. Use the manifest for listing/filtering; use Claude for analysis

Still no database.
