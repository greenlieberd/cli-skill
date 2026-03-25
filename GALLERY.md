# CLI Gallery

> Everything below is what cli-skill designs. A CLI isn't just a script that runs — it's a space someone enters. These are examples of what that space can look like.

---

## The HUD — a persistent home screen

A HUD stays open while you work. It holds its shape. It adapts when the terminal resizes. It tells you what's ready, what's running, what needs attention — without having to ask.

```
╭──────────────────────────────────────────────────────────╮
│                                                          │
│   ██████╗ ██╗   ██╗██╗     ███████╗███████╗             │
│   ██╔══██╗██║   ██║██║     ██╔════╝██╔════╝             │
│   ██████╔╝██║   ██║██║     ███████╗█████╗               │
│   ██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝               │
│   ██║     ╚██████╔╝███████╗███████║███████╗             │
│   ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝             │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   ▶  Generate today's briefing        ready             │
│      Review queue                     14 items          │
│      Source status                    4 / 4 ok          │
│      Archive                          347 entries        │
│      Settings                                           │
│                                                          │
│   ─────────────────────────────────────────────────     │
│   reddit ✓   hn ✓   twitter ✓   youtube ✓               │
│                                                          │
│   ↑↓ navigate   enter select   ? help   ctrl+c exit     │
╰──────────────────────────────────────────────────────────╯
```

The ASCII logo is generated from the project name. The status row at the bottom updates live as sources come in. Resize the terminal — everything reflows.

---

## The Wizard — guided step-by-step flows

For tools where users make decisions in sequence. Progress dots track where you are. Every step has a way forward and a way back. No dead ends.

**Step 1 — the opening question:**

```
╭──────────────────────────────────────────────────────────╮
│                                                          │
│   [●○○○○]  What are you generating?                     │
│                                                          │
│   ▶  Social captions for video clips                    │
│      Recipe variations from a pantry list               │
│      Ad copy from a product brief                       │
│      Blog posts from rough notes                        │
│      Something else                                     │
│                                                          │
│   ─────────────────────────────────────────────────     │
│   ↑↓ select   enter confirm                             │
╰──────────────────────────────────────────────────────────╯
```

**Step 3 — deeper in the flow:**

```
╭──────────────────────────────────────────────────────────╮
│                                                          │
│   [●●●○○]  Tone                                         │
│                                                          │
│   ▶  Marketing — confident, polished, on-brand          │
│      Internal — clear, direct, no fluff                 │
│      Playful — humor ok, keep it informal               │
│      Minimal — short, factual, no personality           │
│                                                          │
│   ─────────────────────────────────────────────────     │
│   ↑↓ select   enter confirm   ← back                   │
╰──────────────────────────────────────────────────────────╯
```

**Step 5 — confirm before running:**

```
╭──────────────────────────────────────────────────────────╮
│                                                          │
│   [●●●●●]  Ready. Here's what will run:                 │
│                                                          │
│   ┌──────────────┬──────────────────────────────────┐   │
│   │ Type         │ Social captions                  │   │
│   │ Source       │ 14 clips in /footage/march-15/   │   │
│   │ Tone         │ Marketing                        │   │
│   │ Length       │ Short (< 150 chars)              │   │
│   │ Output       │ output/2024-03-15/               │   │
│   └──────────────┴──────────────────────────────────┘   │
│                                                          │
│   ─────────────────────────────────────────────────     │
│   enter run   ← change something                        │
╰──────────────────────────────────────────────────────────╯
```

---

## Tabs — filtering without leaving the screen

Tab bars let users switch views in place. Counts update live. The active tab is underlined. Arrow keys switch between them.

```
╭──────────────────────────────────────────────────────────╮
│                                                          │
│   All (47)   ▼ Ready (12)   Reviewed (31)   Skipped (4) │
│   ──────────────                                        │
│                                                          │
│   ▶  Morning routine clip     3 captions ready          │
│      Product demo reel        5 captions ready          │
│      Office tour              2 captions ready          │
│      Behind the scenes        2 captions ready          │
│                                                          │
│   ─────────────────────────────────────────────────     │
│   ◄► switch tab   enter open   d delete   ctrl+c exit   │
╰──────────────────────────────────────────────────────────╯
```

---

## Loading states — honest feedback at every phase

A spinner for each step, not one spinner for everything. You always know what's happening.

```
   ✓  Reddit               23 posts    0.9s
   ✓  Hacker News          18 posts    1.1s
   ⠋  Twitter              fetching...
   –  Summarizing          waiting
```

When it's done:

```
   ✓  Reddit               23 posts    0.9s
   ✓  Hacker News          18 posts    1.1s
   ✓  Twitter              31 posts    2.4s
   ✓  Summarizing          14 themes   4.1s

   Ready — press enter to review.
```

---

## Data tables — output you can act on

Results displayed in-place. Color communicates status. Review, approve, skip — without opening anything else.

```
╭──────────────────────────────────────────────────────────╮
│   Ready to review — 12 items                            │
│                                                          │
│   #    Title                         Source    Status   │
│   ───  ────────────────────────────  ───────  ───────   │
│ ▶ 1    The End of App Stores         HN        ready    │
│   2    Quiet Quitting Was Real       Reddit    ready    │
│   3    Claude 4 Ships                Twitter   ready    │
│   4    Rome Wasn't Built article ×3  HN        skip     │
│   5    AI Takes Designer Jobs        Reddit    ready    │
│                                                          │
│   enter review   s skip   a approve all   ctrl+c exit   │
╰──────────────────────────────────────────────────────────╯
```

---

## The design interview — planning before building

Before any code gets written, cli-skill interviews you. One question at a time. Here's what that looks like:

```
  [●○○○○]  What's the name of your CLI?

  > brew


  [●●○○○]  What does it do — one sentence.

  > Generates recipe variations from whatever's in my fridge.
    Pulls from a pantry list I keep in Notion.


  [●●●○○]  Is this something you run and leave open,
           or run once and walk away?

  ▶  Leave it running   (HUD — persistent home screen)
     Run and exit       (Commands — fast, scriptable)


  [●●●●○]  Does it use AI?

  ▶  Yes — Claude generates the recipes
     No — just data transformation


  [●●●●●]  Here's your design:

  ┌──────────────┬────────────────────────────────────┐
  │ Name         │ brew                               │
  │ Interface    │ HUD                                │
  │ AI           │ Claude — smart tier                │
  │ Sources      │ Notion pantry, Spoonacular API     │
  │ Output       │ markdown files in output/          │
  │ Theme        │ Grove (green + sand)               │
  └──────────────┴────────────────────────────────────┘

  Build this? (enter yes   ← change something)
```

---

## The design brief — what travels with the code

After the interview, three files land in `.cli/plan/`. They travel with the repo. Every future session starts by reading them.

**CONTEXT.md** — what the project is and what it isn't:

```markdown
# brew — context

A recipe variation generator. Given what's in your fridge
(pulled from a Notion pantry list), suggests 3–5 recipes.
Claude generates the variations. Spoonacular validates
ingredient combinations.

Interface: HUD — stays open, updates in place.
Entry: bun hud

What this is NOT:
- Not a meal planner — no weekly scheduling
- Not a shopping list tool
- Not a calorie tracker
```

**PLAN.md** — v0.1 tasks vs. parked work:

```markdown
# brew — plan

> Status: 4 of 7 tasks complete

## v0.1 — shipping now

- [x] HUD home screen with ASCII logo
- [x] Notion pantry source (returns SourceResult)
- [x] Spoonacular validation source
- [ ] Recipe generation with Claude (smart tier)
- [ ] Output to output/YYYY-MM-DD/ with manifest

## v0.2+ — parked

- [ ] Dietary filters (vegan, gluten-free)
- [ ] Weekly digest to email
```

The plan is live. Every `/cli:audit` session works from it, checks tasks off, and parks new ideas for later.

---

## The memory that compounds

After a few sessions, `/cli:cli-learn` reads the session logs and writes `.cli/learnings/SUMMARY.md`. Every future session starts with it loaded.

```markdown
# brew — learnings
> Updated: 2024-03-15 · 8 sessions analyzed

## Watch out for
- Notion API returns paginated results — always handle
  cursor, never assume one call is enough
- Spoonacular free tier: 150 req/day. Hit it on session 3.
  Use the cache first, fetch only on cache miss.

## Patterns that work
- `loadPantry()` → filter by category → pass to Claude
  is cleaner than passing the raw list
- Users always want to preview before running — add a
  "here's what will generate" confirm step

## Decisions already made
- No database. Pantry list lives in Notion, output in flat
  files. Claude is the query layer. Don't reopen this.
```

You stop re-explaining the same context. The system stops making the same suggestions. The longer you work on a project, the smarter it gets about that project.

---

## Real CLIs built with these patterns

**Pulse** — Daily intelligence dashboard. Reddit, HN, Twitter, YouTube → themed briefing delivered to the terminal every morning. ANSI HUD, 4 live sources, MCP server queryable from Claude Desktop.

**Animations** — Video production system. Remotion scenes, brand token system, AI-assisted scripting. Ink wizard with 8 decision steps — picks format, mood, music style, voiceover, and output path before rendering.

**Images** — Static ad image generator. JSX templates → Satori → PNG. Every ad format (LinkedIn, Meta, Twitter, Google, OG). CLI wizard, 11 output sizes, brand-consistent every time.

---

## Build your own

```
/cli:cli-new
```

Describe what you're building. Answer five questions. Get a CLI that looks and feels like it was designed, not generated. → [Back to README](README.md)
