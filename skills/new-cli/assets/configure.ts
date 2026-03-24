// src/configure.ts — loads .env into process.env, masks API keys for display
// Copy this file verbatim into every new CLI. Never modify it.

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
