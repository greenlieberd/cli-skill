# PLAN — cli-skill plugin

> Status: 21 of 22 tasks complete
> Started: 2026-03-25
> Goal: Distributable Claude Code plugin for building production-quality CLI tools with great UX
> v0.1 scope: 5 skills, 5 agents, 42 rules, hook system, lean context loading

---

## v0.1 — shipped ✓

- [x] **5 skills** `feat` — cli-new, cli-plan, cli-explore, cli-audit, cli-learn
- [x] **5 agents** `feat` — cli-planner, cli-explorer, cli-architect, cli-reviewer, cli-learner
- [x] **42 rules** `feat` — subject-named rules covering all major CLI patterns
- [x] **Hook system** `feat` — check_conventions.py (PreToolUse), error_capture.py (PostToolUse), session_logger.py (Stop), SessionStart context inject
- [x] **Asset library** `feat` — hud.ts, theme.ts, models.ts, configure.ts, App.tsx, Frame.tsx in skills/cli-new/assets/
- [x] **Plugin registration** `chore` — plugin.json + marketplace.json
- [x] **Wizard interview** `feat` — cli-planner redesigned as 5-step wizard with [●●●○○] progress
- [x] **Conditional rule loading** `refactor` — rules loaded by interface type, not all 17 at once
- [x] **Conditional asset loading** `refactor` — assets loaded based on PLAN_COMPLETE interface field
- [x] **Model tier strategy** `fix` — haiku for read/extract, sonnet for decisions/planning
- [x] **SessionStart tightened** `fix` — triggers on .cli/ folder presence only, not any hud project
- [x] **Skill naming** `fix` — cli-new, cli-plan, etc. (discoverable in slash command picker)
- [x] **Plan path fix** `fix` — all files write to .cli/plan/ not .cli/ root
- [x] **CONTRIBUTING.md** `docs` — contributing guide with required tool workflow
- [x] **README.md** `docs` — full story: why CLI UX matters, system cycle, install/update/uninstall
- [x] **LICENSE** `docs` — MIT, Dennis Green-Lieber / Propane
- [x] **CLAUDE.md** `docs` — plugin context for future sessions
- [x] **.cli/plan/** `chore` — plugin's own planning docs (this file)

---

## v0.2 — in progress

- [x] **Test bed** `test` — tests/ directory: Python unit tests for hooks, fixture projects, shell runner, REPORT.md generator (140/140 tests passing)
- [x] **Token spend logging** `feat` — session_logger.py: log input/output/cache tokens + estimated USD cost per session
- [x] **Validator clean pass** `fix` — apply all plugin-dev:plugin-validator and skill-reviewer recommendations (validators running)
- [ ] **Rule coverage** `docs` — 25 of 42 rules are not explicitly referenced in skill files; add explicit references or archive unused ones

---

## v0.3 — parked

Use `/cli:cli-audit .` to add these when v0.2 ships.

- [ ] **Integration tests** `test` — Claude API calls to verify agents produce expected output shapes (needs API key, runs separately)
- [ ] **cli:stats skill** `feat` — reads .cli/sessions/ to show token spend, cost estimates, task velocity across sessions
- [ ] **Changelog** `docs` — CHANGELOG.md tracking version history
- [ ] **Plugin update checker** `feat` — SessionStart warns if installed version is behind marketplace
- [ ] **Rule triage** `chore` — decide which of the 25 orphaned rules to archive vs. reference explicitly

---

## Ideas

Not tasks yet — needs discussion.

- **cli:share** — generate a shareable project brief from .cli/plan/ (for onboarding new team members)
- **cli:migrate** — migrate existing Propane CLI projects (pulse, animations, images) to use .cli/ convention
- **Multi-project learnings** — aggregate patterns across projects, not just per-project
- **Audit score** — convention compliance score (0-100) tracked over time
