# PLAN — cli-skill plugin

> Status: v0.3 in progress
> Started: 2026-03-24
> Goal: Distributable Claude Code plugin for building production-quality CLI tools with great UX

---

## v0.1 — shipped ✓

- [x] **5 skills** — cli-new, cli-plan, cli-explore, cli-audit, cli-learn
- [x] **5 agents** — cli-planner, cli-explorer, cli-architect, cli-reviewer, cli-learner
- [x] **42 rules** — subject-named rules covering all major CLI patterns
- [x] **Hook system** — check_conventions.py, error_capture.py, session_logger.py, SessionStart
- [x] **Asset library** — hud.ts, theme.ts, models.ts, configure.ts, App.tsx, Frame.tsx
- [x] **Plugin registration** — plugin.json + marketplace.json
- [x] **Wizard interview** — 5-step planner with [●●●○○] progress
- [x] **Conditional rule loading** — rules by interface type, not all at once
- [x] **Conditional asset loading** — assets based on PLAN_COMPLETE interface field
- [x] **Model tier strategy** — haiku for read/extract, sonnet for decisions
- [x] **SessionStart tightened** — triggers on .cli/ folder only
- [x] **Skill naming** — cli-new, cli-plan, etc. (discoverable in picker)
- [x] **Plan path fix** — all files write to .cli/plan/ not .cli/ root
- [x] **CONTRIBUTING.md** — contributing guide with required tool workflow
- [x] **README.md** — install, system overview, conventions
- [x] **LICENSE** — MIT, Dennis Green-Lieber / Propane
- [x] **CLAUDE.md** — plugin context for future sessions
- [x] **.cli/plan/** — plugin's own planning docs

---

## v0.2 — shipped ✓

- [x] **Test bed** — 56 unit tests for hooks, fixture projects, shell runner, REPORT.md
- [x] **Token spend logging** — session_logger.py logs input/output/cache tokens + USD cost
- [x] **Validator clean pass** — plugin-validator + skill-reviewer recommendations applied
- [x] **Rule coverage** — all 42 rules wired into conditional groups in cli-new + full taxonomy in cli-audit

---

## v0.3 — shipped ✓

- [x] **CHANGELOG.md** — version history from v0.1 through v0.3
- [x] **GALLERY.md** — design gallery with ASCII renders of HUD, wizard, tabs, tables, loading states
- [x] **README before/after** — boring console.log output vs full designed HUD
- [x] **Marketing rewrite** — founder voice, product positioning, "design studio" framing
- [x] **Version bump to 0.3.0** — plugin.json, marketplace.json
- [ ] **Deployment tests** — structural + CI-safe tests for open source contributors

---

## v0.4 — parked

Build in this order:

- [x] **Plugin update checker** `feat` — non-blocking SessionStart notice: version diff + exact update command; cached 24h; silent on network failure; 16 unit tests
- [ ] **Audit redesign** `refactor` — `/cli:audit` becomes strategic+retrospective: loads everything (logs, learnings, plan, code), spawns architect+reviewer mindset, proposes multiple directions with trade-offs, user picks one, produces PLAN.md; SessionStart suggests audit after N sessions or returning to old project
- [ ] **Auto-learning compression** `feat` — no reflect skill; runs automatically after N sessions; compresses global `~/.cli/learnings/SUMMARY.md` (frequency-promotes-silence-fades, stays tight); injects passively into SessionStart; invisible to user
- [ ] **Integration tests** `test` — contract/schema validation via `claude` subprocess (no API key); checks: PLAN.md structure, folder layout, CONTEXT.md required fields, rule references match plan decisions, agent output contracts; lives in `tests/integration/`
- [ ] **Repo dev environment** `chore` — `.claude/settings.json` with auto-hooks: plugin-validator on plugin.json/SKILL.md save, test suite on hook script save; one contributor rule file; solo-contributor scale, nothing more

---

## Ideas

Not tasks yet.

- **cli:migrate** — bring existing CLIs (pulse, animations, images) into the .cli/ convention
- **Audit score** — convention compliance tracked over time
