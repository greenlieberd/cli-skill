---
name: global-install
description: Packaging a Bun CLI for global installation so it runs from anywhere as a system command.
metadata:
  tags: install, global, bin, package.json, distribution
---

# Global Install

> Platform: macOS (Terminal.app, iTerm2, Warp).

A CLI that runs only from its project folder is a personal script. A CLI with a global install runs as a system command from anywhere. The difference is a `bin` field in `package.json` and a shebang line.

## Prerequisites

- Bun ≥ 1.0 installed globally
- `package.json` with `name` and `version` fields
- Entry point file compiled or run directly by Bun

---

## 1. package.json — add a bin field

```json
{
  "name": "my-tool",
  "version": "1.0.0",
  "bin": {
    "my-tool": "./cli.ts"
  },
  "scripts": {
    "hud": "bun run cli.ts"
  }
}
```

The `bin` key maps the command name to the entry file. After `bun install -g`, typing `my-tool` anywhere runs `./cli.ts` with Bun.

For single-command tools, shorthand:
```json
{
  "bin": "./cli.ts"
}
```
This uses the `name` field as the command name.

---

## 2. Entry file — shebang required

The entry file must have a shebang so the OS knows to use Bun:

```typescript
#!/usr/bin/env bun
// cli.ts
import { loadEnv } from './src/configure.ts'
loadEnv()
// ... rest of CLI
```

Make it executable:
```bash
chmod +x cli.ts
```

---

## 3. Installing globally

```bash
# From the project directory
bun install -g .

# Or directly from a git repo
bun install -g git+ssh://git@github.com:yourname/my-tool.git

# Or from npm (if published)
bun install -g my-tool
```

After install, the command is available system-wide:
```bash
my-tool           # runs the CLI
my-tool --help    # if you've added a --help flag
```

---

## 4. Verify install path

```bash
which my-tool
# → /Users/username/.bun/bin/my-tool

bun pm ls -g | grep my-tool
# → my-tool@1.0.0
```

---

## 5. Uninstall

```bash
bun remove -g my-tool
```

---

## 6. PATH — ensure ~/.bun/bin is in PATH

Global Bun packages install to `~/.bun/bin`. This must be in `$PATH`:

```bash
# Check
echo $PATH | tr ':' '\n' | grep bun

# Add to ~/.zshrc if missing
export PATH="$HOME/.bun/bin:$PATH"
```

---

## 7. .env resolution — global installs need absolute paths

When installed globally, `import.meta.dir` points to the package's install directory in `~/.bun/`, not the user's project folder. Handle this explicitly in `configure.ts`:

```typescript
// src/configure.ts — global-aware env loading
import { existsSync, readFileSync } from 'fs'
import { join } from 'path'

export function loadEnv(): void {
  // Try current working directory first (local config)
  // Then fall back to package install directory
  const candidates = [
    join(process.cwd(), '.env'),
    join(import.meta.dir, '..', '.env'),
  ]

  for (const path of candidates) {
    if (!existsSync(path)) continue
    for (const line of readFileSync(path, 'utf8').split('\n')) {
      const eq = line.indexOf('=')
      if (eq < 1 || line.startsWith('#')) continue
      const key = line.slice(0, eq).trim()
      const val = line.slice(eq + 1).trim().replace(/^["']|["']$/g, '')
      if (key && !process.env[key]) process.env[key] = val
    }
    return   // stop after first found .env
  }
}
```

This lets users run `my-tool` from any directory and have their local `.env` loaded automatically.

---

## 8. Version flag — required for global tools

Global tools should always support `--version`:

```typescript
// cli.ts
if (process.argv.includes('--version') || process.argv.includes('-v')) {
  const pkg = JSON.parse(readFileSync(join(import.meta.dir, 'package.json'), 'utf8'))
  process.stdout.write(`${pkg.name} ${pkg.version}\n`)
  process.exit(0)
}
```

---

## Rules

- Shebang on the entry file: `#!/usr/bin/env bun`
- Make entry file executable: `chmod +x cli.ts`
- Add `bin` field to `package.json` before running `bun install -g`
- `loadEnv()` checks `process.cwd()` first — lets users configure from their working directory
- Always implement `--version` for global tools
- Document `bun install -g` in the README
