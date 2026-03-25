"""
Unit tests for hooks/session_logger.py

Run: python3 -m pytest tests/unit/test_session_logger.py -v
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).parent.parent.parent / "hooks" / "session_logger.py"


def run_hook(event: dict, cwd: str) -> tuple[dict, int]:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    try:
        return json.loads(result.stdout), result.returncode
    except json.JSONDecodeError:
        return {"error": result.stdout, "stderr": result.stderr}, result.returncode


STOP_EVENT = {
    "stop_reason": "end_turn",
    "usage": {
        "input_tokens": 12000,
        "output_tokens": 3400,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    }
}


def make_cli_project(tmp_path: Path, with_plan: bool = False) -> Path:
    """Set up a minimal CLI project directory."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "cli.ts").write_text("// entry")
    (tmp_path / "package.json").write_text(json.dumps({
        "name": "test-project",
        "scripts": {"hud": "bun src/cli.ts"}
    }))
    if with_plan:
        (tmp_path / ".cli" / "plan").mkdir(parents=True)
        (tmp_path / ".cli" / "plan" / "PLAN.md").write_text(
            "# PLAN\n- [x] done task\n- [ ] pending task\n"
        )
    return tmp_path


class TestCliProjectDetection:
    def test_writes_session_in_cli_project(self, tmp_path):
        make_cli_project(tmp_path)
        out, code = run_hook(STOP_EVENT, str(tmp_path))
        assert code == 0
        assert out.get("continue") is True

        sessions_dir = tmp_path / ".cli" / "sessions"
        assert sessions_dir.exists()
        logs = list(sessions_dir.glob("*.jsonl"))
        assert len(logs) == 1

    def test_skips_non_cli_project(self, tmp_path):
        out, code = run_hook(STOP_EVENT, str(tmp_path))
        assert code == 0
        assert out.get("continue") is True
        # No .cli/sessions should be created
        assert not (tmp_path / ".cli" / "sessions").exists()


class TestSessionEntry:
    def test_entry_has_required_fields(self, tmp_path):
        make_cli_project(tmp_path)
        run_hook(STOP_EVENT, str(tmp_path))

        logs = list((tmp_path / ".cli" / "sessions").glob("*.jsonl"))
        entry = json.loads(logs[0].read_text().strip())

        assert "ts" in entry
        assert "project" in entry
        assert "skill" in entry
        assert "changed_files" in entry
        assert "errors" in entry
        assert "tokens" in entry
        assert "stop_reason" in entry

    def test_reads_plan_progress(self, tmp_path):
        make_cli_project(tmp_path, with_plan=True)
        run_hook(STOP_EVENT, str(tmp_path))

        logs = list((tmp_path / ".cli" / "sessions").glob("*.jsonl"))
        entry = json.loads(logs[0].read_text().strip())
        assert "plan_progress" in entry
        assert entry["plan_progress"] == "1/2"

    def test_project_name_from_package_json(self, tmp_path):
        make_cli_project(tmp_path)
        run_hook(STOP_EVENT, str(tmp_path))

        logs = list((tmp_path / ".cli" / "sessions").glob("*.jsonl"))
        entry = json.loads(logs[0].read_text().strip())
        assert entry["project"] == "test-project"

    def test_token_usage_stored(self, tmp_path):
        make_cli_project(tmp_path)
        run_hook(STOP_EVENT, str(tmp_path))

        logs = list((tmp_path / ".cli" / "sessions").glob("*.jsonl"))
        entry = json.loads(logs[0].read_text().strip())
        tokens = entry["tokens"]
        assert tokens.get("input") == 12000
        assert tokens.get("output") == 3400
        assert tokens.get("total") == 15400
        assert "cost_usd" in tokens
        assert isinstance(tokens["cost_usd"], float)

    def test_appends_to_existing_log(self, tmp_path):
        """Multiple sessions in same day should append to same file."""
        make_cli_project(tmp_path)
        run_hook(STOP_EVENT, str(tmp_path))
        run_hook(STOP_EVENT, str(tmp_path))

        logs = list((tmp_path / ".cli" / "sessions").glob("*.jsonl"))
        assert len(logs) == 1
        lines = [l for l in logs[0].read_text().strip().splitlines() if l]
        assert len(lines) == 2


class TestErrorBuffer:
    def test_reads_and_clears_error_buffer(self, tmp_path):
        make_cli_project(tmp_path)
        buf = tmp_path / ".cli" / "sessions" / ".errors_buffer.jsonl"
        buf.parent.mkdir(parents=True, exist_ok=True)
        buf.write_text(json.dumps({"command": "bun test", "error_snippet": "TypeError"}) + "\n")

        run_hook(STOP_EVENT, str(tmp_path))

        # Buffer should be cleared
        assert not buf.exists(), "Error buffer should be cleared after reading"

        logs = list((tmp_path / ".cli" / "sessions").glob("[0-9]*.jsonl"))
        entry = json.loads(logs[0].read_text().strip())
        assert len(entry["errors"]) == 1
        assert entry["errors"][0]["error_snippet"] == "TypeError"


class TestMalformedInput:
    def test_handles_empty_stdin(self, tmp_path):
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="",
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

    def test_handles_missing_usage(self, tmp_path):
        make_cli_project(tmp_path)
        event = {"stop_reason": "end_turn"}
        out, code = run_hook(event, str(tmp_path))
        assert code == 0
