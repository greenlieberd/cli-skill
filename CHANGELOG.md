# Changelog

All notable changes to cli-skill are documented here.

---

## [0.3.0] — 2026-03-25

### Added
- **GALLERY.md** — standalone design gallery with full ASCII renders of every major UI pattern: HUD home screen, wizard steps 1/3/5, tab navigation, loading states, data tables, the planning interview, the design brief, and the learnings memory
- **README before/after** — visual hook at the top of the README showing a boring console.log CLI vs. a fully designed HUD with the same functionality
- **Health review** framing added to roadmap — not a numeric score but a structured "what's working / what's not / here's the roadmap" review mode

### Changed
- **README rewritten** — founder voice and product positioning throughout; new sections for "Who it's for" and "Many small CLIs, not one big one"
- **Tagline** — "A Claude Code plugin for building CLI tools..." → "Build CLIs worth running every morning."
- **marketplace.json** — descriptions rewritten across plugin + all 5 skills; UX design system positioning, not code generator
- **plugin.json** — description aligned with new positioning
- **PLAN.md** — cleaned and versioned; removed stale items (cli:stats, cli:share, cli:migrate promoted to ideas)
- **All 42 rules now referenced** — 25 previously orphaned rules wired into correct conditional groups in cli-new; full taxonomy by category in cli-audit

### Fixed
- Removed stale GAPS.md/FIXES.md references from README .cli/ folder layout
- cli-audit rules reference expanded from 10 to full 42-rule taxonomy

---

## [0.2.0] — 2026-03-25

### Added
- **Test bed** — 56 Python unit tests covering all three hook scripts (check_conventions.py, error_capture.py, session_logger.py)
- **Fixture projects** — `tests/fixtures/has-violations/` and `tests/fixtures/clean-project/` for convention checker integration tests
- **Shell test runner** — `tests/run.sh` with `--teardown` and `--unit-only` flags, generates `tests/REPORT.md`
- **Token spend logging** — session_logger.py tracks input/output/cache tokens and estimates USD cost per session using Anthropic pricing
- **.cli/plan/** — plugin's own CONTEXT.md, DECISIONS.md, and living PLAN.md

### Changed
- **cli-planner** redesigned as a 5-step wizard with `[●●●○○]` progress header — one question group at a time, not a wall of prompts
- **Phase 5 templates** replaced with compact prose specs (~30 lines vs ~115 lines); major token reduction
- **Conditional rule loading** in cli-new — rules loaded by interface type (HUD, wizard, sources, AI, distribution), not all 17 at once
- **Conditional asset loading** — assets loaded based on PLAN_COMPLETE interface field, not speculatively
- **Model tiers** — cli-explorer and cli-learner agents changed from sonnet → haiku (read-only tasks); cli-planner stays sonnet
- **SessionStart trigger** tightened — now checks `.cli/` folder presence only, not any project with `src/cli.ts` or a `hud` script
- **cli-audit** context loading conditional by goal — fix/improve loads PLAN.md only; add feature adds DECISIONS.md; full audit adds EXPLORE.md
- **plugin.json** version bumped to 0.2.0, homepage and repository fields added
- **marketplace.json** skills array added with per-skill command + description entries
- **CLAUDE.md** updated — removed load_context.sh reference, added cli-learner.md, documented tests/ directory and agent usage

### Fixed
- check_conventions.py crash on malformed stdin — top-level try/except added
- Broken rule reference: `data-philosophy.md` → `flat-files.md`
- cli-audit GAPS.md/FIXES.md references removed — cli-planner doesn't produce these files
- cli-learn duplicate archive step removed — cli-learner agent handles archiving
- cli-plan EXPLORE.md now loads content (cat head-60) not just existence check
- Skill descriptions converted to third-person ("This skill should be used when...")

---

## [0.1.0] — 2026-03-24

### Added
- **5 skills**: `/cli:cli-new`, `/cli:cli-plan`, `/cli:cli-explore`, `/cli:cli-audit`, `/cli:cli-learn`
- **5 agents**: cli-planner, cli-explorer, cli-architect, cli-reviewer, cli-learner
- **42 rules** covering all major CLI patterns: HUD screens, wizard steps, source results, models, colors, display, testing, retry, caching, layouts, tabs, tables, spinners, keyboard shortcuts, and more
- **Hook system**: check_conventions.py (PreToolUse — warns on hardcoded models, throwing sources, DB imports), error_capture.py (PostToolUse — buffers bash errors to .cli/sessions/.errors_buffer.jsonl), session_logger.py (Stop — writes session summary to .cli/sessions/YYYY-MM-DD.jsonl), SessionStart context injection
- **Asset library** in `skills/cli-new/assets/`: hud.ts, theme.ts, models.ts, configure.ts, App.tsx, Frame.tsx, SelectList.tsx
- **Plugin registration**: plugin.json (name: cli → /cli:* commands) + marketplace.json
- **`.cli/` folder convention** — plan/, audit/, learnings/ committed; sessions/ gitignored
- **README.md** — install instructions, system overview, what gets scaffolded, conventions enforced
- **CONTRIBUTING.md** — contributing guide with required validator workflow
- **LICENSE** — MIT

### Architecture decisions
- Skill name includes plugin prefix (`cli-new` not `new`) for discoverability in the slash command picker
- Skills are thin wrappers: load context + spawn agent via Task tool + show results
- Rules are subject-named files, never `how-to-` prefixed or numbered
- `.cli/plan/` subfolder (not `.cli/` root) for plan files — separates plan from audit and learnings
- Model tier strategy: haiku for read-only extraction, sonnet for decisions and planning
