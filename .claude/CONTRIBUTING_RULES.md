# Contributor rules — cli-skill

Solo contributor. These rules keep the plugin consistent between sessions.

## Before touching anything

1. Read `CLAUDE.md` — it has the full architecture
2. Read `.cli/plan/CONTEXT.md` — what this is and what NOT to do
3. Read `.cli/plan/DECISIONS.md` — decisions already made, don't re-open

## Required workflow

| When | Tool |
|------|------|
| After editing any SKILL.md | run `/plugin-dev:skill-reviewer` |
| After any structural change | run `/plugin-dev:plugin-validator` |
| After editing a hook script | `python3 -m pytest tests/ -q` |

These are not optional. The settings.json hooks will remind you.

## Key rules

- Skill descriptions: third-person (`This skill should be used when...`), not second-person
- Agent frontmatter: `allowed-tools:` not `tools:` (tools: is silently ignored)
- Read-only agents (cli-explorer, cli-learner): must use `model: haiku`
- Decision agents (cli-planner, cli-architect, cli-reviewer): must use `model: sonnet`
- Rules: subject-named files (`hud-screens.md`) — never `how-to-` prefix or numbers
- Skills are thin wrappers — interview logic belongs in agents, not skills
- Never load all rules at once — load conditionally based on plan fields

## Version bumps

1. Update `.claude-plugin/plugin.json` → `version`
2. Update `.claude-plugin/marketplace.json` → `plugins[0].version`
3. Add entry to `CHANGELOG.md`
4. Run `./tests/run.sh` — all tests must pass before commit

## Commit format

Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
One logical change per commit.
