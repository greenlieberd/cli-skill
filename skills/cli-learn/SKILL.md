---
name: learn
description: Use this skill to extract learnings from past cli:* sessions and improve the cli-skill plugin itself. Triggers on "learn from sessions", "what have we learned", "improve the skills", "compress session logs", "what keeps going wrong", or after a few sessions on a project when you want to spot patterns. Reads .cli/sessions/, extracts patterns and gaps, proposes rule updates and scaffold changes.
argument-hint: "[path/to/cli-project]"
model: sonnet
effort: medium
context: fork
allowed-tools: Read, Write, Edit, Glob, Grep, LS, Bash
---

# cli:learn — Extract, compress, propose

Reads session history from `.cli/sessions/`, finds patterns and gaps, proposes concrete improvements to rules, agents, and scaffold. Nothing is applied without your approval.

## Context loaded at runtime

Directory: !`pwd`
Target: `$ARGUMENTS`
Sessions found: !`ls "${ARGUMENTS:-.}/.cli/sessions/"*.jsonl 2>/dev/null | grep -v errors_buffer | wc -l | tr -d ' '`
Last learned: !`[ -f "${ARGUMENTS:-.}/.cli/learnings/SUMMARY.md" ] && head -3 "${ARGUMENTS:-.}/.cli/learnings/SUMMARY.md" || echo "never"`

---

## Step 0 — Confirm and orient

If `$ARGUMENTS` is a path, use it. Otherwise use current directory.

Check sessions exist:
```bash
ls .cli/sessions/*.jsonl 2>/dev/null | grep -v errors_buffer
```

If no sessions found:
```
No session logs found at .cli/sessions/.

Sessions are logged automatically when cli:* skills run.
Run /cli:new, /cli:audit, or /cli:explore first, then come back.
```

If sessions exist, show what we're working with:
```
Found [N] session log files covering [date range].
Last learning run: [date or "never"]

I'll analyze these for patterns, errors, and gaps — then propose
improvements to the cli-skill rules and scaffold.

This may take a minute.
```

---

## Step 1 — Run the learner

Launch `cli-learner` agent with:
- `PROJECT_PATH` — the confirmed project path
- `SINCE` — date of last SUMMARY.md update (or all-time if first run)
- `FOCUS` — `all`

Wait for `LEARNER_COMPLETE` before continuing.

---

## Step 2 — Present findings

After the learner finishes, read `.cli/learnings/PROPOSALS.md` and present clearly:

```
Session analysis complete — [N] sessions, [date range]

Proposals ([N] total):

HIGH PRIORITY
  1. [type] [title]
     [one-line description of what to change and why]

  2. [type] [title]
     [one-line description]

MEDIUM
  3. [type] [title]
  ...

LOW
  ...

Full details in .cli/learnings/PROPOSALS.md

Apply all? Or pick which ones to review first.
(yes / pick / skip / show details for #N)
```

---

## Step 3 — Review and apply

For each approved proposal, apply it immediately.

**`rule-update`** — edit the existing rule file:
```
Updating rules/[rule].md — [what's changing]
```
Read the current rule, apply the specific addition or fix, preserve all existing content.

**`new-rule`** — create a new rule file:
Follow the rule template exactly:
```markdown
---
name: [subject]
description: [one line]
metadata:
  tags: [tag1, tag2]
---

# [Subject]

## Prerequisites
- [what's needed]

[content with concrete TypeScript examples]
```

**`scaffold-change`** — edit the relevant SKILL.md:
Read the current skill file, add the new file to the generation list in the correct phase.

**`hook-update`** — edit `hooks/check_conventions.py`:
Read the current script, apply the specific check addition.

**`agent-update`** — edit the relevant agent markdown:
Read the agent file, apply the targeted instruction addition.

After each change:
```
✓ Applied: [proposal title]
  → [file path changed]
```

---

## Step 4 — Confirm the plugin changes are correct

After applying all approved changes, run a quick sanity check:

```bash
# Verify rule files have required frontmatter
grep -rL "^---" rules/*.md 2>/dev/null && echo "missing frontmatter" || echo "all rules have frontmatter"

# Verify hooks script still parses
python3 -c "import json; json.load(open('hooks/hooks.json'))" && echo "hooks.json valid"

# Verify skill files have required frontmatter
grep -rL "^name:" skills/*/SKILL.md 2>/dev/null && echo "missing name" || echo "all skills have name"
```

Fix any issues before finishing.

---

## Step 5 — Compress and archive

After applying proposals:

1. Update `.cli/learnings/SUMMARY.md` — add an entry for this learning run
2. Archive old session logs:
```bash
mkdir -p .cli/sessions/archive
# Keep 5 most recent daily log files, archive the rest
ls -t .cli/sessions/*.jsonl 2>/dev/null | grep -v errors_buffer | tail -n +6 | xargs -I{} mv {} .cli/sessions/archive/ 2>/dev/null || true
echo "archived"
```

3. Tell the user:
```
Learning run complete.

Applied: [N] changes
  [list of files changed]

Archived: [N] old session logs → .cli/sessions/archive/
Active logs: [N] kept

The cli-skill plugin has been updated. Future sessions will use these improvements.

If you're happy with the changes, commit them:
  cd [cli-skill path] && git add -A && git commit -m "learn: [summary of improvements]"
```

---

## Notes

- Proposals are never auto-applied — you always review first.
- Partial approval is fine — skip anything you're not sure about.
- Skipped proposals stay in `PROPOSALS.md` for next time.
- Run `/cli:learn` again after 5–10 more sessions for the next round.
- The learner improves the plugin, not just the project — changes go to `rules/`, `skills/`, `agents/`, `hooks/`.
