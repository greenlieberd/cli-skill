"""
Unit tests for hooks/auto_learn.py

Run: python3 -m pytest tests/unit/test_auto_learn.py -v
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))
import auto_learn


# ── helpers ───────────────────────────────────────────────────────────────────

def make_session(tmp_path: Path, filename: str, entries: list):
    sessions_dir = tmp_path / ".cli" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    log = sessions_dir / filename
    log.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    return sessions_dir


def now_iso(days_ago: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def basic_session(skill="cli:audit", files=None, errors=None, cost=0.05, days_ago=0):
    return {
        "ts": now_iso(days_ago),
        "project": "test-cli",
        "skill": skill,
        "changed_files": files or ["src/models.ts"],
        "errors": errors or [],
        "tokens": {"input": 1000, "output": 500, "cost_usd": cost},
        "plan_progress": "3/8",
    }


# ── load_sessions ──────────────────────────────────────────────────────────────

class TestLoadSessions:
    def test_loads_jsonl_entries(self, tmp_path):
        make_session(tmp_path, "2026-03-01.jsonl", [basic_session()])
        sessions = auto_learn.load_sessions(tmp_path / ".cli" / "sessions")
        assert len(sessions) == 1

    def test_skips_errors_buffer(self, tmp_path):
        sessions_dir = tmp_path / ".cli" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        (sessions_dir / ".errors_buffer.jsonl").write_text(json.dumps({"error": "x"}) + "\n")
        (sessions_dir / "2026-03-01.jsonl").write_text(json.dumps(basic_session()) + "\n")
        sessions = auto_learn.load_sessions(sessions_dir)
        assert len(sessions) == 1

    def test_loads_multiple_files(self, tmp_path):
        sessions_dir = tmp_path / ".cli" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        for i in range(3):
            (sessions_dir / f"2026-03-0{i+1}.jsonl").write_text(
                json.dumps(basic_session()) + "\n"
            )
        sessions = auto_learn.load_sessions(sessions_dir)
        assert len(sessions) == 3

    def test_skips_invalid_json_lines(self, tmp_path):
        sessions_dir = tmp_path / ".cli" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        (sessions_dir / "2026-03-01.jsonl").write_text("not json\n" + json.dumps(basic_session()) + "\n")
        sessions = auto_learn.load_sessions(sessions_dir)
        assert len(sessions) == 1


# ── recency_weight ─────────────────────────────────────────────────────────────

class TestRecencyWeight:
    def test_recent_session_gets_high_weight(self):
        now = datetime.now(timezone.utc)
        ts = (now - timedelta(days=1)).isoformat()
        assert auto_learn.recency_weight(ts, now) == 2.0

    def test_month_old_session_gets_normal_weight(self):
        now = datetime.now(timezone.utc)
        ts = (now - timedelta(days=15)).isoformat()
        assert auto_learn.recency_weight(ts, now) == 1.0

    def test_old_session_fades(self):
        now = datetime.now(timezone.utc)
        ts = (now - timedelta(days=45)).isoformat()
        assert auto_learn.recency_weight(ts, now) == 0.5

    def test_bad_ts_returns_default(self):
        now = datetime.now(timezone.utc)
        assert auto_learn.recency_weight("not-a-date", now) == 1.0


# ── extract_patterns ──────────────────────────────────────────────────────────

class TestExtractPatterns:
    def test_identifies_hot_files(self):
        sessions = [
            basic_session(files=["src/models.ts", "src/cli.ts"]),
            basic_session(files=["src/models.ts", "src/sources/reddit.ts"]),
            basic_session(files=["src/models.ts"]),
        ]
        hot_files, _, _, _, _ = auto_learn.extract_patterns(sessions)
        assert "src/models.ts" in hot_files

    def test_identifies_recurring_errors(self):
        err = {"command": "bun typecheck", "error": "Cannot find SourceResult"}
        sessions = [
            basic_session(errors=[err]),
            basic_session(errors=[err]),
            basic_session(errors=[err]),
        ]
        _, recurring, _, _, _ = auto_learn.extract_patterns(sessions)
        assert len(recurring) > 0
        assert any("bun typecheck" in e for e in recurring)

    def test_sums_cost(self):
        sessions = [basic_session(cost=0.05)] * 4
        _, _, _, total_cost, _ = auto_learn.extract_patterns(sessions)
        assert abs(total_cost - 0.20) < 0.001

    def test_returns_latest_plan_progress(self):
        sessions = [
            basic_session(days_ago=5),
            {**basic_session(days_ago=0), "plan_progress": "5/8"},
        ]
        sessions[0]["plan_progress"] = "3/8"
        _, _, _, _, progress = auto_learn.extract_patterns(sessions)
        assert progress == "5/8"

    def test_cold_files_excluded(self):
        # File only appears once with low weight — should NOT be in hot_files
        sessions = [basic_session(files=["src/rarely-touched.ts"])]
        hot_files, _, _, _, _ = auto_learn.extract_patterns(sessions)
        # Single recent session = weight 2.0 ≥ 1.5, so it IS included
        # But with days_ago=10 weight drops to 1.0 which is < 1.5
        sessions_old = [basic_session(files=["src/rarely-touched.ts"], days_ago=15)]
        hot_files_old, _, _, _, _ = auto_learn.extract_patterns(sessions_old)
        assert "src/rarely-touched.ts" not in hot_files_old


# ── render_summary ─────────────────────────────────────────────────────────────

class TestRenderSummary:
    def test_includes_project_name(self):
        sessions = [basic_session()]
        result = auto_learn.render_summary(sessions, "my-cli")
        assert "my-cli" in result

    def test_includes_session_count(self):
        sessions = [basic_session()] * 3
        result = auto_learn.render_summary(sessions, "x")
        assert "sessions_analyzed: 3" in result

    def test_includes_hot_files_section(self):
        sessions = [basic_session(files=["src/models.ts"])] * 3
        result = auto_learn.render_summary(sessions, "x")
        assert "Hot files" in result
        assert "src/models.ts" in result

    def test_includes_cost(self):
        sessions = [basic_session(cost=0.10)] * 2
        result = auto_learn.render_summary(sessions, "x")
        assert "0.20" in result

    def test_returns_empty_on_no_sessions(self):
        assert auto_learn.render_summary([], "x") == ""

    def test_includes_auto_generated_marker(self):
        sessions = [basic_session()]
        result = auto_learn.render_summary(sessions, "x")
        assert "auto-generated" in result


# ── main (integration) ────────────────────────────────────────────────────────

class TestMain:
    def test_writes_summary_md(self, tmp_path):
        make_session(tmp_path, "2026-03-01.jsonl", [basic_session()] * 3)
        auto_learn.main.__globals__["sys"].argv = ["auto_learn.py", str(tmp_path)]
        import importlib
        # Call main directly with path
        sys.argv = ["auto_learn.py", str(tmp_path)]
        auto_learn.main()
        summary = tmp_path / ".cli" / "learnings" / "SUMMARY.md"
        assert summary.exists()
        content = summary.read_text()
        assert "Session learnings" in content

    def test_creates_learnings_dir(self, tmp_path):
        make_session(tmp_path, "2026-03-01.jsonl", [basic_session()])
        sys.argv = ["auto_learn.py", str(tmp_path)]
        auto_learn.main()
        assert (tmp_path / ".cli" / "learnings").exists()

    def test_no_crash_on_empty_sessions_dir(self, tmp_path):
        sessions_dir = tmp_path / ".cli" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        sys.argv = ["auto_learn.py", str(tmp_path)]
        auto_learn.main()  # should not raise

    def test_no_crash_on_missing_sessions_dir(self, tmp_path):
        sys.argv = ["auto_learn.py", str(tmp_path)]
        auto_learn.main()  # should not raise
