---
name: output-files
description: Date-stamped file naming, output/ directory structure, manifest tracking, and opening files from the HUD.
metadata:
  tags: output, files, naming, manifest, export
---

# Output Files

> Platform: macOS (Terminal.app, iTerm2, Warp).

Generated files need a predictable, sortable naming convention and a dedicated directory. Users should be able to open the output folder and immediately understand what everything is and when it was created.

## Prerequisites

- `output/` directory in `.gitignore`
- Bun runtime (uses `Bun.file()` and `Bun.write()`)
- `.propane/` for runtime state (distinct from `output/` for generated content)

---

## 1. Directory structure

```
project-root/
  output/               ← generated files (gitignored)
    2025-11-14-reddit-summary.md
    2025-11-14-reddit-summary.html
    2025-11-15-competitor-analysis.md
  .propane/             ← runtime state (gitignored)
    index.json          ← list of output files (manifest)
    logs/
      usage.jsonl
      errors.jsonl
```

Two directories, two purposes:
- `output/` — files the user opens, shares, or archives
- `.propane/` — internal state Claude and the CLI use

---

## 2. Naming convention — date-slug-format

```
YYYY-MM-DD-slug.ext
```

```typescript
// src/output.ts
export function makeFilename(slug: string, ext: string): string {
  const date = new Date().toISOString().slice(0, 10)       // 2025-11-14
  const safe = slug
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')   // spaces and specials → dashes
    .replace(/^-|-$/g, '')          // trim leading/trailing dashes
    .slice(0, 40)                   // max 40 chars for the slug
  return `${date}-${safe}.${ext}`
}

// Example
makeFilename('Reddit: AI tools roundup', 'md')
// → '2025-11-14-reddit-ai-tools-roundup.md'
```

---

## 3. Writing files — Bun.write with mkdir

```typescript
// src/output.ts
import { mkdirSync } from 'fs'
import { join } from 'path'

const OUTPUT_DIR = join(import.meta.dir, '..', 'output')

export async function writeOutput(slug: string, ext: string, content: string): Promise<string> {
  mkdirSync(OUTPUT_DIR, { recursive: true })
  const filename = makeFilename(slug, ext)
  const filepath = join(OUTPUT_DIR, filename)
  await Bun.write(filepath, content)
  updateManifest(filepath, slug)
  return filepath
}
```

---

## 4. Manifest — index.json for fast listing

Writing a `manifest.json` lets the HUD list recent outputs without scanning the directory every time.

```typescript
// src/output.ts
import { join } from 'path'
import { existsSync, readFileSync } from 'fs'

const MANIFEST = join(import.meta.dir, '..', '.propane', 'index.json')

interface ManifestEntry {
  path:     string
  slug:     string
  created:  string   // ISO timestamp
  size:     number   // bytes
}

function updateManifest(filepath: string, slug: string): void {
  const entries: ManifestEntry[] = existsSync(MANIFEST)
    ? JSON.parse(readFileSync(MANIFEST, 'utf8'))
    : []

  const stat = Bun.file(filepath)
  entries.unshift({
    path:    filepath,
    slug,
    created: new Date().toISOString(),
    size:    stat.size,
  })

  // Keep last 100 entries
  const trimmed = entries.slice(0, 100)
  Bun.write(MANIFEST, JSON.stringify(trimmed, null, 2))
}
```

---

## 5. Multiple formats — write once, emit both

When a run produces both Markdown and HTML:

```typescript
const content = buildMarkdown(results)
const html    = markdownToHtml(content)

const mdPath   = await writeOutput(slug, 'md', content)
const htmlPath = await writeOutput(slug, 'html', html)

process.stdout.write(`  ✓  Saved ${A.dim}${mdPath}${A.reset}\n`)
process.stdout.write(`  ✓  Saved ${A.dim}${htmlPath}${A.reset}\n`)
```

Use the same slug for both — they'll sort together by date.

---

## 6. Opening output — macOS `open` command

After writing, offer to open the file:

```typescript
import { spawnSync } from 'child_process'

export function openInFinder(filepath: string): void {
  spawnSync('open', ['-R', filepath])   // -R = reveal in Finder
}

export function openFile(filepath: string): void {
  spawnSync('open', [filepath])          // opens with default app
}
```

In the HUD: after a successful export, add `[o] open file` to the footer hints.

---

## 7. Gitignore — always exclude generated content

```bash
# .gitignore
output/
.propane/
```

Never commit generated output. Users export from the HUD or archive manually.

---

## Rules

- Date-first naming (`YYYY-MM-DD-slug.ext`) — sorts chronologically in Finder and ls
- All output in `output/` — never in root, `src/`, or `.propane/`
- Always `mkdirSync({ recursive: true })` before writing — directory may not exist
- Update `manifest.json` on every write — don't scan directory at HUD startup
- Limit manifest to 100 entries — older entries fall off automatically
