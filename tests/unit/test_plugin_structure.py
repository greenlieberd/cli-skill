"""
Plugin structure validation tests.
Verifies that all expected files exist and have correct structure.

Run: python3 -m pytest tests/unit/test_plugin_structure.py -v
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


class TestPluginJSON:
    def test_plugin_json_exists(self):
        assert (ROOT / ".claude-plugin" / "plugin.json").exists()

    def test_plugin_json_valid(self):
        data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        assert data["name"] == "cli"
        assert "version" in data
        assert "description" in data

    def test_marketplace_json_exists(self):
        assert (ROOT / ".claude-plugin" / "marketplace.json").exists()

    def test_marketplace_json_valid(self):
        data = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        assert "plugins" in data
        assert len(data["plugins"]) >= 1
        plugin = data["plugins"][0]
        assert "name" in plugin
        assert "version" in plugin

    def test_versions_match(self):
        p = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        m = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        assert p["version"] == m["plugins"][0]["version"], "plugin.json and marketplace.json versions must match"


class TestSkillFiles:
    EXPECTED_SKILLS = ["cli-new", "cli-plan", "cli-explore", "cli-audit", "cli-learn"]

    def test_all_skill_directories_exist(self):
        for skill in self.EXPECTED_SKILLS:
            path = ROOT / "skills" / skill
            assert path.exists(), f"Missing skill directory: skills/{skill}"

    def test_all_skill_md_files_exist(self):
        for skill in self.EXPECTED_SKILLS:
            path = ROOT / "skills" / skill / "SKILL.md"
            assert path.exists(), f"Missing SKILL.md for: {skill}"

    def test_skill_frontmatter_has_required_fields(self):
        required = ["name", "description", "model", "effort", "allowed-tools"]
        for skill in self.EXPECTED_SKILLS:
            content = (ROOT / "skills" / skill / "SKILL.md").read_text()
            # Extract frontmatter block
            if not content.startswith("---"):
                raise AssertionError(f"{skill}/SKILL.md has no frontmatter")
            fm_end = content.index("---", 3)
            fm = content[3:fm_end]
            for field in required:
                assert field in fm, f"{skill}/SKILL.md missing frontmatter field: {field}"

    def test_skill_descriptions_are_third_person(self):
        """Descriptions must start with 'This skill should be used when' not 'Use this skill'."""
        for skill in self.EXPECTED_SKILLS:
            content = (ROOT / "skills" / skill / "SKILL.md").read_text()
            # Extract description from frontmatter
            match = re.search(r'description:\s*(.+)', content)
            if match:
                desc = match.group(1).strip()
                assert not desc.lower().startswith("use this skill"), \
                    f"{skill}/SKILL.md: description is second-person. Must be third-person."

    def test_skill_names_match_directory(self):
        """The name field in frontmatter should match the directory name."""
        for skill in self.EXPECTED_SKILLS:
            content = (ROOT / "skills" / skill / "SKILL.md").read_text()
            match = re.search(r'^name:\s*(.+)', content, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                assert name == skill, f"{skill}/SKILL.md: name field is '{name}', expected '{skill}'"


class TestAgentFiles:
    EXPECTED_AGENTS = ["cli-planner", "cli-explorer", "cli-architect", "cli-reviewer", "cli-learner"]

    def test_all_agent_files_exist(self):
        for agent in self.EXPECTED_AGENTS:
            path = ROOT / "agents" / f"{agent}.md"
            assert path.exists(), f"Missing agent: agents/{agent}.md"

    def test_agent_frontmatter_uses_allowed_tools(self):
        """Agents must use 'allowed-tools:' not 'tools:' (which is silently ignored)."""
        for agent in self.EXPECTED_AGENTS:
            content = (ROOT / "agents" / f"{agent}.md").read_text()
            if "tools:" in content and "allowed-tools:" not in content:
                raise AssertionError(
                    f"agents/{agent}.md uses 'tools:' — must be 'allowed-tools:' (tools: is silently ignored)"
                )

    def test_agent_frontmatter_has_model(self):
        for agent in self.EXPECTED_AGENTS:
            content = (ROOT / "agents" / f"{agent}.md").read_text()
            assert "model:" in content, f"agents/{agent}.md missing model field"

    def test_read_only_agents_use_haiku(self):
        """Explorer and learner do read-only work — should use haiku, not sonnet."""
        for agent in ["cli-explorer", "cli-learner"]:
            content = (ROOT / "agents" / f"{agent}.md").read_text()
            match = re.search(r'^model:\s*(.+)', content, re.MULTILINE)
            if match:
                model = match.group(1).strip()
                assert model == "haiku", \
                    f"agents/{agent}.md uses model '{model}' — should be haiku (read-only work)"


class TestHookFiles:
    EXPECTED_HOOKS = ["check_conventions.py", "error_capture.py", "session_logger.py"]

    def test_hooks_json_exists(self):
        assert (ROOT / "hooks" / "hooks.json").exists()

    def test_all_hook_scripts_exist(self):
        for hook in self.EXPECTED_HOOKS:
            assert (ROOT / "hooks" / hook).exists(), f"Missing hook script: hooks/{hook}"

    def test_hooks_json_valid(self):
        data = json.loads((ROOT / "hooks" / "hooks.json").read_text())
        assert "hooks" in data

    def test_hook_scripts_are_fail_silent(self):
        """Each hook script should have try/except and always exit 0."""
        for hook in self.EXPECTED_HOOKS:
            content = (ROOT / "hooks" / hook).read_text()
            assert "except" in content, f"hooks/{hook}: should have try/except for fail-silent behavior"


class TestRulesDirectory:
    def test_rules_directory_exists(self):
        assert (ROOT / "rules").exists()

    def test_rules_have_frontmatter(self):
        """Every rule file must start with YAML frontmatter."""
        rules = list((ROOT / "rules").glob("*.md"))
        assert len(rules) > 0, "No rule files found"
        for rule in rules:
            content = rule.read_text()
            assert content.startswith("---"), f"rules/{rule.name}: missing frontmatter"

    def test_critical_rules_exist(self):
        """Rules referenced by skills must exist."""
        critical = [
            "conventions.md", "testing.md", "hud-screens.md", "ascii-art.md",
            "wizard-steps.md", "source-results.md", "models.md", "environment-setup.md",
        ]
        for rule in critical:
            assert (ROOT / "rules" / rule).exists(), f"Missing critical rule: rules/{rule}"


class TestAssetsDirectory:
    def test_assets_directory_exists(self):
        assets_path = ROOT / "skills" / "cli-new" / "assets"
        assert assets_path.exists()

    def test_core_assets_exist(self):
        assets_path = ROOT / "skills" / "cli-new" / "assets"
        required = ["hud.ts", "theme.ts", "models.ts", "configure.ts"]
        for asset in required:
            assert (assets_path / asset).exists(), f"Missing core asset: {asset}"
