// VIOLATION: source throws instead of returning SourceResult
export async function fetchReddit(subreddit: string) {
  const res = await fetch(`https://reddit.com/r/${subreddit}.json`)
  if (!res.ok) throw new Error(`Reddit fetch failed: ${res.status}`) // should return sourceError()
  const data = await res.json()
  return data.data.children.map((c: any) => c.data)
}
