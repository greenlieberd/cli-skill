# cli-skill test report

> Generated: 2026-03-25 19:59:33
> Duration: 2s
> Results: 140 passed · 0 failed · 0 skipped · 140 total

## Summary

✅ All tests passed.

## Results

| Status | Test |
|--------|------|
| ✓ | python3 available (Python 3.9.6) |
| ✓ | pytest available |
| ✓ | plugin.json |
| ✓ | marketplace.json |
| ✓ | hooks.json |
| ✓ | check_conventions.py |
| ✓ | error_capture.py |
| ✓ | session_logger.py |
| ✓ | skills/cli-new/SKILL.md |
| ✓ | skills/cli-plan/SKILL.md |
| ✓ | skills/cli-explore/SKILL.md |
| ✓ | skills/cli-audit/SKILL.md |
| ✓ | skills/cli-learn/SKILL.md |
| ✓ | agents/cli-planner.md |
| ✓ | agents/cli-explorer.md |
| ✓ | agents/cli-architect.md |
| ✓ | agents/cli-reviewer.md |
| ✓ | agents/cli-learner.md |
| ✓ | assets/hud.ts |
| ✓ | assets/theme.ts |
| ✓ | assets/models.ts |
| ✓ | assets/configure.ts |
| ✓ | .claude-plugin/plugin.json is valid JSON |
| ✓ | .claude-plugin/marketplace.json is valid JSON |
| ✓ | hooks/hooks.json is valid JSON |
| ✓ | Versions match (0.2.0) |
| ✓ | cli-new: name present |
| ✓ | cli-new: description present |
| ✓ | cli-new: model present |
| ✓ | cli-new: effort present |
| ✓ | cli-new: allowed-tools present |
| ✓ | cli-new: description is third-person |
| ✓ | cli-plan: name present |
| ✓ | cli-plan: description present |
| ✓ | cli-plan: model present |
| ✓ | cli-plan: effort present |
| ✓ | cli-plan: allowed-tools present |
| ✓ | cli-plan: description is third-person |
| ✓ | cli-explore: name present |
| ✓ | cli-explore: description present |
| ✓ | cli-explore: model present |
| ✓ | cli-explore: effort present |
| ✓ | cli-explore: allowed-tools present |
| ✓ | cli-explore: description is third-person |
| ✓ | cli-audit: name present |
| ✓ | cli-audit: description present |
| ✓ | cli-audit: model present |
| ✓ | cli-audit: effort present |
| ✓ | cli-audit: allowed-tools present |
| ✓ | cli-audit: description is third-person |
| ✓ | cli-learn: name present |
| ✓ | cli-learn: description present |
| ✓ | cli-learn: model present |
| ✓ | cli-learn: effort present |
| ✓ | cli-learn: allowed-tools present |
| ✓ | cli-learn: description is third-person |
| ✓ | cli-planner: uses allowed-tools |
| ✓ | cli-planner: model set |
| ✓ | cli-explorer: uses allowed-tools |
| ✓ | cli-explorer: model set |
| ✓ | cli-architect: uses allowed-tools |
| ✓ | cli-architect: model set |
| ✓ | cli-reviewer: uses allowed-tools |
| ✓ | cli-reviewer: model set |
| ✓ | cli-learner: uses allowed-tools |
| ✓ | cli-learner: model set |
| ✓ | cli-explorer: correctly uses haiku (read-only work) |
| ✓ | cli-learner: correctly uses haiku (read-only work) |
| ✓ | rules/conventions.md |
| ✓ | rules/testing.md |
| ✓ | rules/hud-screens.md |
| ✓ | rules/ascii-art.md |
| ✓ | rules/wizard-steps.md |
| ✓ | rules/source-results.md |
| ✓ | rules/models.md |
| ✓ | rules/environment-setup.md |
| ✓ | rules/colors.md |
| ✓ | rules/display-system.md |
| ✓ | rules/flat-files.md |
| ✓ | rules/error-recovery.md |
| ✓ | Detects hardcoded model ID in non-models file |
| ✓ | Allows model IDs in models.ts |
| ✓ | Detects throwing source file |
| ✓ | All 56 pytest tests passed |

## Token estimates

| Workflow | Estimated tokens |
|----------|-----------------|
| /cli:cli-plan | 2918 |
| /cli:cli-new | 5013 + rules |
| /cli:cli-explore | 1759 |
| /cli:cli-audit | 5743 + rules |

_Token estimates are static (file size / 4). Actual Claude API usage depends on conversation length and context loaded at runtime. Check .cli/sessions/YYYY-MM-DD.jsonl for real token counts after running skills._

## Failures

_No failures._

---

Run `./tests/run.sh --teardown` to clean up test artifacts.
