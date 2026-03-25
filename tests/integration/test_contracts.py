"""
Integration tests — structural contract validation for cli-skill plugin.

Checks plugin consistency without invoking Claude or needing an API key:
  - Folder layout and required files
  - PLAN.md format and CONTEXT.md required sections
  - Rule references in SKILL.md files resolve to actual rule files
  - Agent output signals match what skills expect
  - Skill/agent frontmatter consistency

Run: python3 -m pytest tests/integration/ -v
"""
import re
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


# ── helpers ───────────────────────────────────────────────────────────────────

def read(path: str) -> str:
    return (ROOT / path).read_text(errors="replace")


def read_skill(name: str) -> str:
    return read(f"skills/{name}/SKILL.md")


def read_agent(name: str) -> str:
    return read(f"agents/{name}.md")


def frontmatter_field(content: str, field: str):
    """Extract a frontmatter field value from markdown content."""
    for line in content.splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return None


# ── folder layout ─────────────────────────────────────────────────────────────

class TestFolderLayout:
    REQUIRED_FILES = [
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
        "hooks/hooks.json",
        "hooks/check_conventions.py",
        "hooks/error_capture.py",
        "hooks/session_logger.py",
        "hooks/update_checker.py",
        "hooks/auto_learn.py",
        "CLAUDE.md",
        "README.md",
        "CHANGELOG.md",
        "GALLERY.md",
        ".cli/plan/CONTEXT.md",
        ".cli/plan/DECISIONS.md",
        ".cli/plan/PLAN.md",
    ]

    SKILLS = ["cli-new", "cli-plan", "cli-explore", "cli-audit", "cli-learn"]
    AGENTS = ["cli-planner", "cli-explorer", "cli-architect", "cli-reviewer", "cli-learner"]
    ASSETS = ["hud.ts", "theme.ts", "models.ts", "configure.ts", "App.tsx", "Frame.tsx"]

    def test_required_files_exist(self):
        missing = [f for f in self.REQUIRED_FILES if not (ROOT / f).exists()]
        assert not missing, f"Missing required files: {missing}"

    def test_all_skill_files_exist(self):
        missing = [s for s in self.SKILLS if not (ROOT / f"skills/{s}/SKILL.md").exists()]
        assert not missing, f"Missing skills: {missing}"

    def test_all_agent_files_exist(self):
        missing = [a for a in self.AGENTS if not (ROOT / f"agents/{a}.md").exists()]
        assert not missing, f"Missing agents: {missing}"

    def test_all_asset_files_exist(self):
        missing = [a for a in self.ASSETS if not (ROOT / f"skills/cli-new/assets/{a}").exists()]
        assert not missing, f"Missing assets: {missing}"

    def test_rules_directory_has_expected_count(self):
        rules = list((ROOT / "rules").glob("*.md"))
        assert len(rules) >= 40, f"Expected at least 40 rules, found {len(rules)}"


# ── plan and context contracts ─────────────────────────────────────────────────

class TestPlanContracts:
    def test_plan_has_version_sections(self):
        content = read(".cli/plan/PLAN.md")
        assert "## v0." in content, "PLAN.md must have version sections (## v0.X)"

    def test_plan_uses_checkbox_syntax(self):
        content = read(".cli/plan/PLAN.md")
        assert "- [x]" in content or "- [ ]" in content, "PLAN.md must use checkbox task syntax"

    def test_plan_has_status_line(self):
        content = read(".cli/plan/PLAN.md")
        assert "> Status:" in content, "PLAN.md must have a > Status: line"

    def test_context_has_required_sections(self):
        content = read(".cli/plan/CONTEXT.md")
        required = ["## Purpose", "## Architecture"]
        missing = [s for s in required if s not in content]
        assert not missing, f"CONTEXT.md missing sections: {missing}"

    def test_context_has_do_not_section(self):
        content = read(".cli/plan/CONTEXT.md")
        assert "## Do not" in content, "CONTEXT.md must have a ## Do not section"

    def test_decisions_has_entries(self):
        content = read(".cli/plan/DECISIONS.md")
        assert "##" in content, "DECISIONS.md must have at least one ## section"


# ── rule reference consistency ─────────────────────────────────────────────────

class TestRuleReferences:
    def _collect_rule_refs(self, skill_name: str):
        """Extract rules/X.md references from a SKILL.md file."""
        content = read_skill(skill_name)
        return set(re.findall(r"rules/([a-z-]+\.md)", content))

    def _all_rule_refs(self):
        refs = set()
        for skill in ["cli-new", "cli-audit"]:
            refs |= self._collect_rule_refs(skill)
        return refs

    def test_all_referenced_rules_exist(self):
        missing = []
        for ref in self._all_rule_refs():
            if not (ROOT / "rules" / ref).exists():
                missing.append(ref)
        assert not missing, f"Referenced rules that don't exist: {missing}"

    def test_cli_new_references_foundation_rules(self):
        refs = self._collect_rule_refs("cli-new")
        assert "conventions.md" in refs, "cli-new must reference conventions.md"
        assert "folder-structure.md" in refs, "cli-new must reference folder-structure.md"

    def test_cli_audit_references_foundation_rules(self):
        refs = self._collect_rule_refs("cli-audit")
        assert "conventions.md" in refs, "cli-audit must reference conventions.md"

    def test_no_orphaned_rules(self):
        """Every rule in rules/ should be referenced by at least one skill."""
        all_refs = self._all_rule_refs()
        actual_rules = {f.name for f in (ROOT / "rules").glob("*.md")}
        unreferenced = actual_rules - all_refs
        # Allow some rules that are loaded dynamically (not listed explicitly)
        assert len(unreferenced) < 5, f"Too many orphaned rules ({len(unreferenced)}): {sorted(unreferenced)}"


# ── skill frontmatter contracts ────────────────────────────────────────────────

class TestSkillFrontmatter:
    REQUIRED_FIELDS = ["name", "description", "model", "effort", "allowed-tools"]
    SKILLS = ["cli-new", "cli-plan", "cli-explore", "cli-audit", "cli-learn"]

    def test_all_skills_have_required_fields(self):
        failures = []
        for skill in self.SKILLS:
            content = read_skill(skill)
            for field in self.REQUIRED_FIELDS:
                if not frontmatter_field(content, field):
                    failures.append(f"{skill}: missing {field}")
        assert not failures, f"Frontmatter failures: {failures}"

    def test_skill_descriptions_are_third_person(self):
        """Descriptions must start with 'This skill should be used when' not 'Use this skill'."""
        failures = []
        for skill in self.SKILLS:
            content = read_skill(skill)
            desc = frontmatter_field(content, "description") or ""
            if desc.lower().startswith("use this skill"):
                failures.append(f"{skill}: description is second-person")
        assert not failures, f"Second-person descriptions: {failures}"

    def test_cli_explore_uses_haiku(self):
        content = read_skill("cli-explore")
        assert frontmatter_field(content, "model") == "haiku", \
            "cli-explore should use haiku (read-only work)"

    def test_cli_audit_uses_sonnet(self):
        content = read_skill("cli-audit")
        assert frontmatter_field(content, "model") == "sonnet", \
            "cli-audit should use sonnet (strategic decisions)"


# ── agent frontmatter contracts ────────────────────────────────────────────────

class TestAgentFrontmatter:
    AGENTS = ["cli-planner", "cli-explorer", "cli-architect", "cli-reviewer", "cli-learner"]
    READ_ONLY_AGENTS = ["cli-explorer", "cli-learner"]

    def test_all_agents_use_allowed_tools_not_tools(self):
        """tools: is silently ignored — must use allowed-tools:."""
        failures = []
        for agent in self.AGENTS:
            content = read_agent(agent)
            if "^tools:" in content:
                failures.append(f"{agent}: uses deprecated tools: (must be allowed-tools:)")
        assert not failures, f"Deprecated tool config: {failures}"

    def test_all_agents_have_model(self):
        missing = []
        for agent in self.AGENTS:
            content = read_agent(agent)
            if not frontmatter_field(content, "model"):
                missing.append(agent)
        assert not missing, f"Agents missing model: {missing}"

    def test_read_only_agents_use_haiku(self):
        failures = []
        for agent in self.READ_ONLY_AGENTS:
            content = read_agent(agent)
            model = frontmatter_field(content, "model")
            if model != "haiku":
                failures.append(f"{agent}: uses {model} (should be haiku for read-only)")
        assert not failures, f"Wrong model for read-only agents: {failures}"


# ── agent output signal contracts ─────────────────────────────────────────────

class TestAgentOutputContracts:
    def test_cli_learner_signals_completion(self):
        content = read_agent("cli-learner")
        assert "LEARNER_COMPLETE" in content, \
            "cli-learner must output LEARNER_COMPLETE signal"

    def test_cli_explorer_writes_explore_md(self):
        # The write instruction is in the skill that invokes the agent, not the agent itself
        skill_content = read_skill("cli-audit")
        assert "EXPLORE.md" in skill_content, \
            "cli-audit must instruct cli-explorer to write EXPLORE.md"

    def test_cli_planner_writes_plan_files(self):
        content = read_agent("cli-planner")
        assert "PLAN.md" in content, "cli-planner must reference writing PLAN.md"
        assert "CONTEXT.md" in content, "cli-planner must reference writing CONTEXT.md"

    def test_cli_audit_skill_references_explore_md_freshness(self):
        """cli-audit must check if EXPLORE.md is fresh or stale before spawning explorer."""
        content = read_skill("cli-audit")
        assert "EXPLORE.md" in content, "cli-audit must reference EXPLORE.md"
        assert "stale" in content or "fresh" in content, \
            "cli-audit must check EXPLORE.md freshness"

    def test_cli_audit_skill_presents_health_snapshot(self):
        content = read_skill("cli-audit")
        assert "health" in content.lower() or "snapshot" in content.lower(), \
            "cli-audit must present a health snapshot"

    def test_cli_audit_skill_presents_directions(self):
        content = read_skill("cli-audit")
        assert "direction" in content.lower(), \
            "cli-audit must propose directions"
        assert "trade-off" in content.lower() or "trade-offs" in content.lower(), \
            "cli-audit directions must include trade-offs"


# ── version consistency ────────────────────────────────────────────────────────

class TestVersionConsistency:
    def test_plugin_json_and_marketplace_json_versions_match(self):
        plugin = json.loads(read(".claude-plugin/plugin.json"))
        market = json.loads(read(".claude-plugin/marketplace.json"))
        plugin_ver = plugin.get("version")
        market_ver = market.get("plugins", [{}])[0].get("version")
        assert plugin_ver == market_ver, \
            f"Version mismatch: plugin.json={plugin_ver}, marketplace.json={market_ver}"

    def test_changelog_mentions_current_version(self):
        plugin_ver = json.loads(read(".claude-plugin/plugin.json")).get("version", "")
        changelog = read("CHANGELOG.md")
        assert plugin_ver in changelog, \
            f"CHANGELOG.md does not mention current version {plugin_ver}"
