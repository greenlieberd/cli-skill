import type { SourceResult } from './types'

export async function fetchReddit(subreddit: string): Promise<SourceResult> {
  try {
    const res = await fetch(`https://reddit.com/r/${subreddit}.json`)
    if (!res.ok) return { ok: false, source: 'reddit', error: `HTTP ${res.status}` }
    const data = await res.json()
    return { ok: true, source: 'reddit', data: data.data.children.map((c: any) => c.data) }
  } catch (err) {
    return { ok: false, source: 'reddit', error: String(err) }
  }
}
