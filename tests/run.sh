#!/usr/bin/env bash
# cli-skill test runner
# Usage: ./tests/run.sh [--teardown] [--unit-only]
# Generates tests/REPORT.md after every run.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
REPORT="$SCRIPT_DIR/REPORT.md"
TEARDOWN=false
UNIT_ONLY=false
START_TIME=$(date +%s)

# Parse flags
for arg in "$@"; do
  case $arg in
    --teardown) TEARDOWN=true ;;
    --unit-only) UNIT_ONLY=true ;;
  esac
done

# ─── Colors ───────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

# ─── Counters ─────────────────────────────────────────────────────
PASS=0; FAIL=0; SKIP=0
declare -a FAILURES=()
declare -a RESULTS=()

log_section() { echo -e "\n${CYAN}${BOLD}── $1 ──${RESET}"; }
log_pass()    { echo -e "  ${GREEN}✓${RESET} $1"; ((PASS++)); RESULTS+=("PASS|$1"); }
log_fail()    { echo -e "  ${RED}✗${RESET} $1"; ((FAIL++)); FAILURES+=("$1"); RESULTS+=("FAIL|$1"); }
log_skip()    { echo -e "  ${YELLOW}—${RESET} $1"; ((SKIP++)); RESULTS+=("SKIP|$1"); }
log_info()    { echo -e "  ${YELLOW}ℹ${RESET}  $1"; }

echo -e "${BOLD}cli-skill test suite${RESET} — $(date '+%Y-%m-%d %H:%M')"

# ─── 0. Teardown mode ─────────────────────────────────────────────
if [ "$TEARDOWN" = true ]; then
  log_section "Teardown"
  rm -rf "$SCRIPT_DIR/tmp" "$REPORT"
  echo -e "  ${GREEN}✓${RESET} Cleaned tests/tmp/ and tests/REPORT.md"
  exit 0
fi

# ─── 1. Python availability ───────────────────────────────────────
log_section "Environment"
if command -v python3 &>/dev/null; then
  PY=$(python3 --version)
  log_pass "python3 available ($PY)"
else
  log_fail "python3 not found — hook tests cannot run"
fi

if python3 -c "import pytest" 2>/dev/null; then
  PYTEST=true
  log_pass "pytest available"
else
  PYTEST=false
  log_info "pytest not installed — install with: pip3 install pytest"
  log_info "Running basic tests only"
fi

# ─── 2. Plugin structure ──────────────────────────────────────────
log_section "Plugin structure"

check_file() {
  local f="$1" label="$2"
  if [ -f "$ROOT/$f" ]; then log_pass "$label"; else log_fail "$label (missing: $f)"; fi
}
check_dir() {
  local d="$1" label="$2"
  if [ -d "$ROOT/$d" ]; then log_pass "$label"; else log_fail "$label (missing: $d)"; fi
}

check_file ".claude-plugin/plugin.json" "plugin.json"
check_file ".claude-plugin/marketplace.json" "marketplace.json"
check_file "hooks/hooks.json" "hooks.json"
check_file "hooks/check_conventions.py" "check_conventions.py"
check_file "hooks/error_capture.py" "error_capture.py"
check_file "hooks/session_logger.py" "session_logger.py"

for skill in cli-new cli-plan cli-explore cli-audit cli-learn; do
  check_file "skills/$skill/SKILL.md" "skills/$skill/SKILL.md"
done

for agent in cli-planner cli-explorer cli-architect cli-reviewer cli-learner; do
  check_file "agents/$agent.md" "agents/$agent.md"
done

for asset in hud.ts theme.ts models.ts configure.ts; do
  check_file "skills/cli-new/assets/$asset" "assets/$asset"
done

# ─── 3. JSON validity ─────────────────────────────────────────────
log_section "JSON validity"

for f in ".claude-plugin/plugin.json" ".claude-plugin/marketplace.json" "hooks/hooks.json"; do
  if python3 -c "import json; json.load(open('$ROOT/$f'))" 2>/dev/null; then
    log_pass "$f is valid JSON"
  else
    log_fail "$f is invalid JSON"
  fi
done

# Version consistency
P_VER=$(python3 -c "import json; print(json.load(open('$ROOT/.claude-plugin/plugin.json'))['version'])" 2>/dev/null || echo "?")
M_VER=$(python3 -c "import json; print(json.load(open('$ROOT/.claude-plugin/marketplace.json'))['plugins'][0]['version'])" 2>/dev/null || echo "?")
if [ "$P_VER" = "$M_VER" ] && [ "$P_VER" != "?" ]; then
  log_pass "Versions match ($P_VER)"
else
  log_fail "Version mismatch: plugin.json=$P_VER, marketplace.json=$M_VER"
fi

# ─── 4. Skill frontmatter ─────────────────────────────────────────
log_section "Skill frontmatter"

check_skill_field() {
  local skill="$1" field="$2"
  local f="$ROOT/skills/$skill/SKILL.md"
  if grep -q "^$field:" "$f" 2>/dev/null; then
    log_pass "$skill: $field present"
  else
    log_fail "$skill: missing $field"
  fi
}

for skill in cli-new cli-plan cli-explore cli-audit cli-learn; do
  for field in name description model effort allowed-tools; do
    check_skill_field "$skill" "$field"
  done
  # Check third-person description
  DESC=$(grep "^description:" "$ROOT/skills/$skill/SKILL.md" | head -1)
  if echo "$DESC" | grep -qi "^description: use this skill"; then
    log_fail "$skill: description is second-person (must start with 'This skill should be used when...')"
  else
    log_pass "$skill: description is third-person"
  fi
done

# ─── 5. Agent frontmatter ─────────────────────────────────────────
log_section "Agent frontmatter"

for agent in cli-planner cli-explorer cli-architect cli-reviewer cli-learner; do
  f="$ROOT/agents/$agent.md"
  if grep -q "^allowed-tools:" "$f" 2>/dev/null; then
    log_pass "$agent: uses allowed-tools"
  elif grep -q "^tools:" "$f" 2>/dev/null; then
    log_fail "$agent: uses tools: (silently ignored — must be allowed-tools:)"
  else
    log_fail "$agent: no tool configuration found"
  fi
  grep -q "^model:" "$f" 2>/dev/null && log_pass "$agent: model set" || log_fail "$agent: no model set"
done

# Read-only agents should use haiku
for agent in cli-explorer cli-learner; do
  MODEL=$(grep "^model:" "$ROOT/agents/$agent.md" | awk '{print $2}' | tr -d '\r')
  if [ "$MODEL" = "haiku" ]; then
    log_pass "$agent: correctly uses haiku (read-only work)"
  else
    log_fail "$agent: uses $MODEL — should be haiku for read-only work"
  fi
done

# ─── 6. Critical rules exist ──────────────────────────────────────
log_section "Rules"

for rule in conventions.md testing.md hud-screens.md ascii-art.md \
            wizard-steps.md source-results.md models.md environment-setup.md \
            colors.md display-system.md flat-files.md error-recovery.md; do
  check_file "rules/$rule" "rules/$rule"
done

RULE_COUNT=$(ls "$ROOT/rules/"*.md 2>/dev/null | wc -l | tr -d ' ')
log_info "Total rules: $RULE_COUNT"

# ─── 7. Token size analysis ───────────────────────────────────────
log_section "Token estimates (static)"
log_info "Approximate token cost per skill invocation (chars/4 ≈ tokens)"

estimate_tokens() {
  local file="$1"
  local chars
  chars=$(wc -c < "$file" 2>/dev/null || echo 0)
  echo $((chars / 4))
}

echo ""
printf "  %-20s %8s %s\n" "File" "Tokens" "Notes"
printf "  %-20s %8s %s\n" "────────────────────" "───────" "─────"

for skill in cli-new cli-plan cli-explore cli-audit cli-learn; do
  f="$ROOT/skills/$skill/SKILL.md"
  [ -f "$f" ] && printf "  %-20s %8d %s\n" "skills/$skill" "$(estimate_tokens "$f")" "skill SKILL.md"
done

for agent in cli-planner cli-explorer cli-architect cli-reviewer cli-learner; do
  f="$ROOT/agents/$agent.md"
  [ -f "$f" ] && printf "  %-20s %8d %s\n" "agents/$agent" "$(estimate_tokens "$f")" "agent file"
done

# Per-workflow estimates
echo ""
log_info "Workflow token estimates (skill + agent, before runtime context):"

PLAN_SKILL=$(estimate_tokens "$ROOT/skills/cli-plan/SKILL.md")
PLAN_AGENT=$(estimate_tokens "$ROOT/agents/cli-planner.md")
printf "  /cli:cli-plan    ~%d tokens (skill: %d, planner: %d)\n" "$((PLAN_SKILL + PLAN_AGENT))" "$PLAN_SKILL" "$PLAN_AGENT"

NEW_SKILL=$(estimate_tokens "$ROOT/skills/cli-new/SKILL.md")
printf "  /cli:cli-new     ~%d tokens (skill: %d, + planner + reviewers)\n" "$((NEW_SKILL + PLAN_AGENT))" "$NEW_SKILL"

AUDIT_SKILL=$(estimate_tokens "$ROOT/skills/cli-audit/SKILL.md")
EXPLORE_AGENT=$(estimate_tokens "$ROOT/agents/cli-explorer.md")
printf "  /cli:cli-audit   ~%d tokens (skill: %d, + explorer + planner)\n" "$((AUDIT_SKILL + EXPLORE_AGENT + PLAN_AGENT))" "$AUDIT_SKILL"

EXPLORE_SKILL=$(estimate_tokens "$ROOT/skills/cli-explore/SKILL.md")
printf "  /cli:cli-explore ~%d tokens (skill: %d, explorer: %d)\n" "$((EXPLORE_SKILL + EXPLORE_AGENT))" "$EXPLORE_SKILL" "$EXPLORE_AGENT"

# ─── 8. Hook convention check (fixture-based) ─────────────────────
log_section "Convention checker (fixture tests)"

VIOLATIONS_DIR="$SCRIPT_DIR/fixtures/has-violations"
CLEAN_DIR="$SCRIPT_DIR/fixtures/clean-project"
HOOK="$ROOT/hooks/check_conventions.py"

# Test: hardcoded model in hud.ts should trigger warning
RESULT=$(echo '{"tool_name":"Write","tool_input":{"file_path":"src/hud.ts","content":"const MODEL = '"'"'claude-sonnet-4-6'"'"'"}}' \
  | python3 "$HOOK" 2>/dev/null)
if echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); exit(0 if 'systemMessage' in d else 1)" 2>/dev/null; then
  log_pass "Detects hardcoded model ID in non-models file"
else
  log_fail "Did not detect hardcoded model ID"
fi

# Test: models.ts should not trigger warning
RESULT=$(echo '{"tool_name":"Write","tool_input":{"file_path":"src/models.ts","content":"const id = '"'"'claude-sonnet-4-6'"'"'"}}' \
  | python3 "$HOOK" 2>/dev/null)
if echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); exit(0 if 'systemMessage' not in d else 1)" 2>/dev/null; then
  log_pass "Allows model IDs in models.ts"
else
  log_fail "False positive: flagged models.ts"
fi

# Test: throwing source triggers warning
RESULT=$(echo '{"tool_name":"Write","tool_input":{"file_path":"src/sources/reddit.ts","content":"throw new Error('"'"'failed'"'"')"}}' \
  | python3 "$HOOK" 2>/dev/null)
if echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); exit(0 if 'systemMessage' in d else 1)" 2>/dev/null; then
  log_pass "Detects throwing source file"
else
  log_fail "Did not detect throwing source"
fi

# ─── 9. Unit tests (pytest) ───────────────────────────────────────
if [ "$PYTEST" = true ] && [ "$UNIT_ONLY" = false ] || [ "$UNIT_ONLY" = true ]; then
  log_section "Unit tests (pytest)"
  PYTEST_OUT=$(python3 -m pytest "$SCRIPT_DIR/unit/" -v --tb=short 2>&1 || true)
  PYTEST_PASS=$(echo "$PYTEST_OUT" | grep -c "PASSED" || true)
  PYTEST_FAIL=$(echo "$PYTEST_OUT" | grep -c "FAILED" || true)
  PYTEST_ERROR=$(echo "$PYTEST_OUT" | grep -c "ERROR" || true)

  PASS=$((PASS + PYTEST_PASS))
  FAIL=$((FAIL + PYTEST_FAIL + PYTEST_ERROR))

  if [ "$PYTEST_FAIL" -eq 0 ] && [ "$PYTEST_ERROR" -eq 0 ]; then
    log_pass "All $PYTEST_PASS pytest tests passed"
  else
    log_fail "$PYTEST_FAIL failed, $PYTEST_ERROR errors (from $((PYTEST_PASS + PYTEST_FAIL + PYTEST_ERROR)) tests)"
    # Show first failure
    echo "$PYTEST_OUT" | grep -A 5 "FAILED\|ERROR" | head -20 | sed 's/^/    /'
  fi
elif [ "$PYTEST" = false ]; then
  log_skip "pytest not available — install: pip3 install pytest"
fi

# ─── 10. Generate REPORT.md ───────────────────────────────────────
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
TOTAL=$((PASS + FAIL + SKIP))

log_section "Results"
echo -e "  Passed: ${GREEN}${PASS}${RESET}  Failed: ${RED}${FAIL}${RESET}  Skipped: ${YELLOW}${SKIP}${RESET}  Total: ${TOTAL}  (${DURATION}s)"

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo -e "\n  ${RED}Failures:${RESET}"
  for f in "${FAILURES[@]}"; do
    echo -e "    ${RED}✗${RESET} $f"
  done
fi

# Write REPORT.md
cat > "$REPORT" << REPORT_EOF
# cli-skill test report

> Generated: $(date '+%Y-%m-%d %H:%M:%S')
> Duration: ${DURATION}s
> Results: ${PASS} passed · ${FAIL} failed · ${SKIP} skipped · ${TOTAL} total

## Summary

$([ "$FAIL" -eq 0 ] && echo "✅ All tests passed." || echo "❌ ${FAIL} test(s) failed.")

## Results

| Status | Test |
|--------|------|
REPORT_EOF

for r in "${RESULTS[@]}"; do
  STATUS="${r%%|*}"
  NAME="${r#*|}"
  case "$STATUS" in
    PASS) echo "| ✓ | $NAME |" >> "$REPORT" ;;
    FAIL) echo "| ✗ | **$NAME** |" >> "$REPORT" ;;
    SKIP) echo "| — | ~~$NAME~~ |" >> "$REPORT" ;;
  esac
done

cat >> "$REPORT" << REPORT_EOF2

## Token estimates

| Workflow | Estimated tokens |
|----------|-----------------|
| /cli:cli-plan | $(($(wc -c < "$ROOT/skills/cli-plan/SKILL.md") / 4 + $(wc -c < "$ROOT/agents/cli-planner.md") / 4)) |
| /cli:cli-new | $(($(wc -c < "$ROOT/skills/cli-new/SKILL.md") / 4 + $(wc -c < "$ROOT/agents/cli-planner.md") / 4)) + rules |
| /cli:cli-explore | $(($(wc -c < "$ROOT/skills/cli-explore/SKILL.md") / 4 + $(wc -c < "$ROOT/agents/cli-explorer.md") / 4)) |
| /cli:cli-audit | $(($(wc -c < "$ROOT/skills/cli-audit/SKILL.md") / 4 + $(wc -c < "$ROOT/agents/cli-explorer.md") / 4 + $(wc -c < "$ROOT/agents/cli-planner.md") / 4)) + rules |

_Token estimates are static (file size / 4). Actual Claude API usage depends on conversation length and context loaded at runtime. Check .cli/sessions/YYYY-MM-DD.jsonl for real token counts after running skills._

## Failures

REPORT_EOF2

if [ "${#FAILURES[@]}" -gt 0 ]; then
  for f in "${FAILURES[@]}"; do
    echo "- ✗ $f" >> "$REPORT"
  done
else
  echo "_No failures._" >> "$REPORT"
fi

cat >> "$REPORT" << REPORT_EOF3

---

Run \`./tests/run.sh --teardown\` to clean up test artifacts.
REPORT_EOF3

echo -e "\n  Report → ${CYAN}tests/REPORT.md${RESET}"

# Exit with failure code if any tests failed
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
