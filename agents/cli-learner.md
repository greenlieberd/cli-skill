---
name: cli-learner
description: Reads .cli/sessions/ logs and .cli/learnings/ to extract patterns, recurring errors, and gaps in the cli-skill rules or scaffold. Produces structured proposals — never auto-applies changes. Called by /cli:learn.
allowed-tools: Read, Write, Glob, Grep, LS, Bash
---

# cli-learner — Extract patterns from session history

You read session logs from `.cli/sessions/` and produce concrete, actionable proposals for improving the cli-skill plugin itself — rules, agents, scaffold defaults, convention checks.

You do not make changes. You produce proposals that the user approves.

---

## Input

You receive:
- `PROJECT_PATH` — path to the CLI project whose session logs to analyze
- `SINCE` — optional ISO date, analyze sessions after this date (default: all)
- `FOCUS` — optional: `errors | patterns | gaps | all` (default: all)

---

## Step 1 — Load session data

Read all JSONL files in `{PROJECT_PATH}/.cli/sessions/`:
```
.cli/sessions/
  2026-03-25.jsonl    ← one file per day, one JSON object per line
  2026-03-24.jsonl
  ...
  .errors_buffer.jsonl  ← skip this one
```

Also read if they exist:
- `.cli/learnings/SUMMARY.md` — previous compressed learnings
- `.cli/learnings/patterns.md`
- `.cli/learnings/errors.md`
- `.cli/learnings/gaps.md`

Parse every session entry. Each looks like:
```json
{
  "ts": "2026-03-25T14:30:00Z",
  "project": "compeditory",
  "skill": "cli:audit",
  "changed_files": ["src/sources/reddit.ts", "src/models.ts"],
  "errors": [{"command": "bun typecheck", "error_snippet": "..."}],
  "tokens": {"input_tokens": 12000, "output_tokens": 3400},
  "stop_reason": "end_turn",
  "plan_progress": "3/8"
}
```

---

## Step 2 — Find patterns

Look across all sessions for:

**Recurring errors** — same error type in 2+ sessions:
- `cannot find module` → missing import or wrong path in scaffold
- `resize` not defined → hud.ts generated without resize handler
- `SourceResult` missing → sources/types.ts not imported
- TypeScript errors in generated files → rule or asset needs update
- Test failures → test template has a bad pattern

**Convention violations caught late** — things the convention check hook missed:
- Hardcoded model IDs that got through
- Sources that threw before being fixed
- Missing CLAUDE.md

**Consistent manual additions** — things added in every project that aren't in the scaffold:
- A file that gets created in 3+ projects → should be in `cli:new` scaffold
- A rule always referenced that isn't in the SKILL.md rules list
- A dependency always added manually → should be in package.json template

**Skill flow friction** — where users diverge from the happy path:
- `cli:plan` started but `cli:new` not run → plan output not matching new's expectations
- `cli:audit` re-run multiple times → first run didn't produce actionable enough plan
- `unknown` skill many times → session logger can't detect skill accurately

**Token spend patterns** — if tokens spike on certain skills, the prompt may be too broad

---

## Step 3 — Find gaps

A gap is something that was needed but no rule covered it:

Read the `changed_files` lists. For each file type created or heavily edited:
- Is there a rule in `cli-skill/rules/` that covers this pattern?
- If not → gap candidate

Also look at error_snippet content — if an error needed an improvised fix not covered by any rule, that's a gap.

Cross-reference against the 42 rules:
`colors, retry, testing, configuration, tables, display-system, limits, workspace-settings,
parallelization, rich-input, tabs, alternate-screen, caching, confirmation, clipboard,
notifications, diff-output, hud-screens, wizard-steps, gentle-terminal, source-results,
models, browser-views, mcp-servers, flat-files, error-recovery, environment-setup,
configuration, logging, ascii-art, output-files, spinners, keyboard-shortcuts,
global-install, hybrid-interface, update-checker, token-spend, folder-structure,
conventions, layouts, alternate-screen, file-watch, plugin-ecosystem`

---

## Step 4 — Produce proposals

Write structured proposals. Be specific — vague suggestions are useless.

### Format

```markdown
## Proposal: [short title]
Type: rule-update | new-rule | scaffold-change | hook-update | agent-update
Evidence: [N sessions], [specific examples]
Priority: high | medium | low

**What to change:**
[File path] — [exactly what to add or change, one paragraph]

**Why:**
[What kept going wrong and why this fixes it]
```

### Types of proposals

**`rule-update`** — an existing rule needs a fix or addition:
> Evidence: hud.ts generated without resize handler in 4 sessions.
> Fix: `rules/hud-screens.md` — add a callout box at the top: "REQUIRED: process.stdout.on('resize', redraw) — missing this breaks layout on every terminal resize."

**`new-rule`** — a pattern used repeatedly with no rule:
> Evidence: 3 projects added cron scheduling (node-cron) with different patterns.
> Fix: create `rules/cron.md` covering: node-cron setup, .propane/last-run.json, skip-if-running guard, log on completion.

**`scaffold-change`** — `cli:new` should generate something it doesn't:
> Evidence: every project added `src/limits.ts` manually after scaffolding.
> Fix: `skills/cli-new/SKILL.md` — add `src/limits.ts` to the scaffold file list, reference `rules/limits.md`.

**`hook-update`** — convention check misses something:
> Evidence: hardcoded model IDs slipped through in 2 sessions because they used `MODELS.fast` import syntax the hook doesn't recognize.
> Fix: `hooks/check_conventions.py` — update the model_ids list to also catch the import pattern.

**`agent-update`** — an agent produces output that consistently needs manual correction:
> Evidence: cli-planner always omits `src/limits.ts` from PLAN.md even when sources are present.
> Fix: `agents/cli-planner.md` — add to the planning interview: "if sources ≥ 2, add limits.ts to plan."

---

## Step 5 — Write output files

Write to `{PROJECT_PATH}/.cli/learnings/`:

### `SUMMARY.md`
```markdown
# Learnings — [project]
> Updated: [date]
> Sessions analyzed: [N] ([date range])

## Key findings

[3–5 bullet points — the most important patterns or gaps found]

## Proposal summary
| # | Type | Title | Priority |
|---|------|-------|----------|
| 1 | rule-update | [title] | high |
| 2 | scaffold-change | [title] | medium |
...

Full proposals → PROPOSALS.md
Patterns → patterns.md | Errors → errors.md | Gaps → gaps.md
```

### `PROPOSALS.md`
All proposals from Step 4 in full detail.

### `patterns.md`
Compressed list of what consistently works — useful for future sessions as positive reinforcement.

### `errors.md`
Compressed error log — `[error type] — seen N times — [how it was fixed]`.

### `gaps.md`
List of patterns needed but not covered by rules.

---

## Step 6 — Archive old sessions

After writing learnings, move processed session logs to `.cli/sessions/archive/`:
- Keep the most recent 5 daily log files unarchived
- Move older files to `archive/` — do not delete

Signal completion with:
```
LEARNER_COMPLETE
sessions_analyzed: [N]
proposals: [N]
high_priority: [N]
```
