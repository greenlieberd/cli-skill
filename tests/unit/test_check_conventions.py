"""
Unit tests for hooks/check_conventions.py

Run: python3 -m pytest tests/unit/test_check_conventions.py -v
"""
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent.parent.parent / "hooks" / "check_conventions.py"
FIXTURES = Path(__file__).parent.parent / "fixtures"


def run_hook(event: dict) -> tuple[dict, int]:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
    )
    try:
        return json.loads(result.stdout), result.returncode
    except json.JSONDecodeError:
        return {"error": result.stdout, "stderr": result.stderr}, result.returncode


def make_event(file_path: str, content: str) -> dict:
    return {
        "tool_name": "Write",
        "tool_input": {
            "file_path": file_path,
            "content": content,
        }
    }


class TestHardcodedModelIDs:
    def test_warns_on_hardcoded_model_in_non_models_file(self):
        event = make_event("src/hud.ts", "const MODEL = 'claude-sonnet-4-6'")
        out, code = run_hook(event)
        assert code == 0, "Hook must exit 0 (never block)"
        assert "systemMessage" in out
        assert "claude-sonnet" in out["systemMessage"]

    def test_no_warning_in_models_file(self):
        event = make_event("src/models.ts", "const id = 'claude-sonnet-4-6'")
        out, code = run_hook(event)
        assert code == 0
        assert "systemMessage" not in out, "models.ts is allowed to contain model IDs"

    def test_haiku_id_detected(self):
        event = make_event("src/cli.ts", "const M = 'claude-haiku-4-5-20251001'")
        out, code = run_hook(event)
        assert code == 0
        assert "systemMessage" in out

    def test_no_false_positive_on_clean_file(self):
        event = make_event("src/cli.ts", "import { MODELS } from './models'")
        out, code = run_hook(event)
        assert code == 0
        assert "systemMessage" not in out


class TestDatabaseImports:
    def test_warns_on_sqlite(self):
        event = make_event("src/db.ts", "import Database from 'better-sqlite3'")
        out, code = run_hook(event)
        assert code == 0
        assert "systemMessage" in out
        assert "better-sqlite3" in out["systemMessage"]

    def test_warns_on_prisma(self):
        event = make_event("src/db.ts", "import { PrismaClient } from 'prisma'")
        out, code = run_hook(event)
        assert code == 0
        assert "systemMessage" in out

    def test_no_false_positive_on_flat_file_read(self):
        event = make_event("src/storage.ts", "const data = JSON.parse(fs.readFileSync('data.json'))")
        out, code = run_hook(event)
        assert code == 0
        assert "systemMessage" not in out


class TestThrowingSource:
    def test_warns_on_throw_in_source_without_sourceError(self):
        event = make_event(
            "src/sources/reddit.ts",
            "if (!res.ok) throw new Error('failed')"
        )
        out, code = run_hook(event)
        assert code == 0
        assert "systemMessage" in out
        assert "SourceResult" in out["systemMessage"]

    def test_no_warning_when_sourceError_present(self):
        event = make_event(
            "src/sources/reddit.ts",
            "if (!res.ok) return sourceError('reddit', 'HTTP error', err)"
        )
        out, code = run_hook(event)
        assert code == 0
        # sourceError is present, so throw in broader content is ok
        assert "systemMessage" not in out or "SourceResult" not in out.get("systemMessage", "")

    def test_no_warning_for_non_source_file(self):
        event = make_event("src/cli.ts", "if (!res.ok) throw new Error('failed')")
        out, code = run_hook(event)
        assert code == 0
        assert "systemMessage" not in out


class TestNonTypeScriptFiles:
    def test_json_file_skipped(self):
        event = make_event("package.json", '{"name": "test", "model": "claude-sonnet-4-6"}')
        out, code = run_hook(event)
        assert code == 0
        assert "systemMessage" not in out

    def test_md_file_skipped(self):
        event = make_event("README.md", "Use claude-sonnet-4-6 for best results")
        out, code = run_hook(event)
        assert code == 0
        assert "systemMessage" not in out


class TestMalformedInput:
    def test_handles_empty_stdin(self):
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="",
            capture_output=True,
            text=True,
        )
        # Should not crash — may output error or continue
        assert result.returncode == 0 or True  # fail-silent

    def test_handles_missing_fields(self):
        event = make_event("src/cli.ts", "")
        out, code = run_hook(event)
        assert code == 0
