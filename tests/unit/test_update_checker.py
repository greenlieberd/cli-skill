"""
Unit tests for hooks/update_checker.py

Run: python3 -m pytest tests/unit/test_update_checker.py -v
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add hook to path for direct import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))
import update_checker


# ── helpers ──────────────────────────────────────────────────────────────────

def fake_plugin_json(tmp_path: Path, version: str) -> Path:
    plugin_dir = tmp_path / ".claude-plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "plugin.json").write_text(json.dumps({"version": version}))
    return tmp_path


def make_cache(path: Path, latest: str, hours_old: int = 0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "checked_at": (datetime.now() - timedelta(hours=hours_old)).isoformat(),
        "latest": latest,
    }))


# ── parse_version ─────────────────────────────────────────────────────────────

class TestParseVersion:
    def test_parses_standard_semver(self):
        assert update_checker.parse_version("1.2.3") == (1, 2, 3)

    def test_parses_with_v_prefix(self):
        assert update_checker.parse_version("v0.3.0") == (0, 3, 0)

    def test_returns_zeros_on_bad_input(self):
        assert update_checker.parse_version("not-a-version") == (0, 0, 0)

    def test_version_comparison_works(self):
        assert update_checker.parse_version("0.4.0") > update_checker.parse_version("0.3.0")
        assert update_checker.parse_version("1.0.0") > update_checker.parse_version("0.9.9")
        assert update_checker.parse_version("0.3.0") == update_checker.parse_version("0.3.0")


# ── get_installed_version ─────────────────────────────────────────────────────

class TestGetInstalledVersion:
    def test_reads_version_from_plugin_json(self, tmp_path):
        fake_plugin_json(tmp_path, "0.3.0")
        plugin_json = tmp_path / ".claude-plugin" / "plugin.json"
        assert json.loads(plugin_json.read_text())["version"] == "0.3.0"

    def test_returns_zero_on_missing_file(self):
        with patch("update_checker.Path") as mock_path:
            mock_path.return_value.__file__ = "/nonexistent"
            # get_installed_version catches exceptions and returns "0.0.0"
            with patch.object(Path, "read_text", side_effect=FileNotFoundError):
                result = update_checker.get_installed_version()
                assert result == "0.0.0"


# ── get_latest_version ────────────────────────────────────────────────────────

class TestGetLatestVersion:
    def test_returns_cached_version_within_ttl(self, tmp_path):
        cache = tmp_path / ".update-cache.json"
        make_cache(cache, "0.4.0", hours_old=1)
        with patch.object(update_checker, "CACHE_PATH", cache):
            result = update_checker.get_latest_version()
        assert result == "0.4.0"

    def test_ignores_expired_cache(self, tmp_path):
        cache = tmp_path / ".update-cache.json"
        make_cache(cache, "0.4.0", hours_old=25)
        remote_data = json.dumps({"version": "0.5.0"}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = remote_data
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch.object(update_checker, "CACHE_PATH", cache):
            with patch("urllib.request.urlopen", return_value=mock_resp):
                result = update_checker.get_latest_version()
        assert result == "0.5.0"

    def test_fetches_from_remote_when_no_cache(self, tmp_path):
        cache = tmp_path / ".update-cache.json"
        remote_data = json.dumps({"version": "0.4.0"}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = remote_data
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch.object(update_checker, "CACHE_PATH", cache):
            with patch("urllib.request.urlopen", return_value=mock_resp):
                result = update_checker.get_latest_version()
        assert result == "0.4.0"

    def test_writes_cache_after_remote_fetch(self, tmp_path):
        cache = tmp_path / ".update-cache.json"
        remote_data = json.dumps({"version": "0.4.0"}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = remote_data
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch.object(update_checker, "CACHE_PATH", cache):
            with patch("urllib.request.urlopen", return_value=mock_resp):
                update_checker.get_latest_version()
        assert cache.exists()
        cached = json.loads(cache.read_text())
        assert cached["latest"] == "0.4.0"

    def test_returns_none_on_network_error(self, tmp_path):
        cache = tmp_path / ".update-cache.json"
        with patch.object(update_checker, "CACHE_PATH", cache):
            with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
                result = update_checker.get_latest_version()
        assert result is None

    def test_returns_none_on_bad_remote_json(self, tmp_path):
        cache = tmp_path / ".update-cache.json"
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"not json"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch.object(update_checker, "CACHE_PATH", cache):
            with patch("urllib.request.urlopen", return_value=mock_resp):
                result = update_checker.get_latest_version()
        assert result is None


# ── main (integration) ────────────────────────────────────────────────────────

class TestMain:
    def _run(self, installed, latest, tmp_path):
        cache = tmp_path / ".update-cache.json"
        if latest:
            make_cache(cache, latest, hours_old=1)
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent.parent / "hooks" / "update_checker.py")],
            capture_output=True, text=True,
            env={**__import__("os").environ, "HOME": str(tmp_path)},
        )
        return result.stdout.strip()

    def test_prints_notice_when_update_available(self, tmp_path):
        import io
        from contextlib import redirect_stdout
        with patch("update_checker.get_installed_version", return_value="0.3.0"):
            with patch("update_checker.get_latest_version", return_value="0.4.0"):
                f = io.StringIO()
                with redirect_stdout(f):
                    update_checker.main()
                output = f.getvalue().strip()
        assert "0.3.0 → 0.4.0" in output
        assert "claude plugin update cli@cli" in output

    def test_prints_nothing_when_up_to_date(self, tmp_path):
        with patch("update_checker.get_installed_version", return_value="0.4.0"):
            with patch("update_checker.get_latest_version", return_value="0.4.0"):
                import io
                from contextlib import redirect_stdout
                f = io.StringIO()
                with redirect_stdout(f):
                    update_checker.main()
                output = f.getvalue().strip()
        assert output == ""

    def test_prints_nothing_when_network_fails(self, tmp_path):
        with patch("update_checker.get_installed_version", return_value="0.3.0"):
            with patch("update_checker.get_latest_version", return_value=None):
                import io
                from contextlib import redirect_stdout
                f = io.StringIO()
                with redirect_stdout(f):
                    update_checker.main()
                output = f.getvalue().strip()
        assert output == ""

    def test_prints_nothing_when_installed_is_newer(self, tmp_path):
        # Edge case: locally patched version ahead of remote
        with patch("update_checker.get_installed_version", return_value="0.5.0"):
            with patch("update_checker.get_latest_version", return_value="0.4.0"):
                import io
                from contextlib import redirect_stdout
                f = io.StringIO()
                with redirect_stdout(f):
                    update_checker.main()
                output = f.getvalue().strip()
        assert output == ""
