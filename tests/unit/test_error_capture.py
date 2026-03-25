"""
Unit tests for hooks/error_capture.py

Run: python3 -m pytest tests/unit/test_error_capture.py -v
"""
import json
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

HOOK = Path(__file__).parent.parent.parent / "hooks" / "error_capture.py"


def run_hook(event: dict, cwd: str = None) -> tuple[dict, int]:
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
        return {"error": result.stdout}, result.returncode


def make_bash_event(command: str, output: str) -> dict:
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command, "description": "test command"},
        "tool_response": {"output": output},
    }


class TestErrorDetection:
    def test_captures_type_error(self):
        event = make_bash_event("bun run hud", "TypeError: Cannot read properties of undefined")
        out, code = run_hook(event)
        assert code == 0
        assert out.get("continue") is True

    def test_captures_module_not_found(self):
        event = make_bash_event("bun run hud", "Module not found: 'ink'")
        out, code = run_hook(event)
        assert code == 0

    def test_passes_through_clean_output(self):
        event = make_bash_event("bun run hud", "HUD started on port 3000")
        out, code = run_hook(event)
        assert code == 0
        assert out.get("continue") is True

    def test_captures_enoent(self):
        event = make_bash_event("cat missing.txt", "ENOENT: no such file or directory")
        out, code = run_hook(event)
        assert code == 0

    def test_captures_exit_code_1(self):
        event = make_bash_event("bun test", "Tests failed with exit code 1")
        out, code = run_hook(event)
        assert code == 0


class TestNonCliProject:
    def test_skips_non_cli_project(self, tmp_path):
        """In a directory without src/cli.ts or hud script, should skip buffering."""
        event = make_bash_event("ls", "TypeError: something broke")
        out, code = run_hook(event, cwd=str(tmp_path))
        assert code == 0
        assert out.get("continue") is True
        # No errors_buffer.jsonl should be created in non-CLI project
        assert not (tmp_path / ".cli" / "sessions" / ".errors_buffer.jsonl").exists()


class TestBuffering:
    def test_writes_to_errors_buffer_in_cli_project(self, tmp_path):
        """In a CLI project directory, errors should be buffered."""
        # Set up minimal CLI project
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "cli.ts").write_text("// entry")
        (tmp_path / ".cli" / "sessions").mkdir(parents=True)

        event = make_bash_event("bun run hud", "TypeError: failed to load")
        out, code = run_hook(event, cwd=str(tmp_path))
        assert code == 0

        buf = tmp_path / ".cli" / "sessions" / ".errors_buffer.jsonl"
        assert buf.exists(), "errors_buffer.jsonl should be created"
        entries = [json.loads(l) for l in buf.read_text().splitlines() if l]
        assert len(entries) == 1
        assert "TypeError" in entries[0]["error_snippet"]


class TestMalformedInput:
    def test_handles_empty_stdin(self):
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_handles_missing_tool_response(self):
        event = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
        out, code = run_hook(event)
        assert code == 0
