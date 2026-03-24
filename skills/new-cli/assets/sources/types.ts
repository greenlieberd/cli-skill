// src/sources/types.ts — SourceResult interface
// Every external data source returns this type. Never throw — always return.
// The caller decides how to handle errors (log, skip, show in UI).

export interface SourceResult {
  source:   string      // machine ID: 'reddit', 'firecrawl', etc.
  label:    string      // human display: 'Reddit r/saas'
  content:  string      // fetched text (empty string on error/skip)
  links?:   string[]    // URLs found in the content
  error?:   string      // error message if fetch failed
  skipped?: boolean     // true if source was toggled off in config
}

// Helpers — use these instead of constructing error objects manually

export function sourceError(source: string, label: string, err: unknown): SourceResult {
  return { source, label, content: '', error: String(err) }
}

export function sourceSkip(source: string, label: string): SourceResult {
  return { source, label, content: '', skipped: true }
}

// Example source stub — copy this pattern for each external API:
//
// import type { SourceResult } from './types.ts'
// import { sourceError } from './types.ts'
//
// export async function fetchReddit(query: string): Promise<SourceResult> {
//   try {
//     const res = await fetch(`https://www.reddit.com/search.json?q=${encodeURIComponent(query)}`)
//     if (!res.ok) return sourceError('reddit', 'Reddit', `HTTP ${res.status}`)
//     const data = await res.json() as any
//     const posts = data.data.children.map((c: any) => c.data.title).join('\n')
//     return { source: 'reddit', label: 'Reddit', content: posts }
//   } catch (err) {
//     return sourceError('reddit', 'Reddit', err)
//   }
// }
