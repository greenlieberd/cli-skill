#!/usr/bin/env python3
"""
update_checker.py — checks for new cli-skill versions at SessionStart.

Reads installed version from plugin.json in the same plugin directory.
Fetches latest from GitHub with a 3s timeout, caches result for 24h.
Outputs a plain-text notice if behind — captured by SessionStart bash
and folded into the systemMessage so Claude surfaces it naturally.
Silent on any error: network failure, missing files, bad JSON — never
breaks a session.
"""
import json
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

REMOTE_URL = "https://raw.githubusercontent.com/greenlieberd/cli-skill/main/.claude-plugin/plugin.json"
CACHE_PATH = Path.home() / ".cli" / ".update-cache.json"
CACHE_TTL_HOURS = 24


def parse_version(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.strip("v").split("."))
    except Exception:
        return (0, 0, 0)


def get_installed_version() -> str:
    """Read version from plugin.json in the same plugin directory."""
    try:
        plugin_json = Path(__file__).parent.parent / ".claude-plugin" / "plugin.json"
        return json.loads(plugin_json.read_text())["version"]
    except Exception:
        return "0.0.0"


def get_latest_version():
    """Return latest version from cache or remote. None on any failure."""
    # Check cache first
    if CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text())
            checked_at = datetime.fromisoformat(cache["checked_at"])
            if datetime.now() - checked_at < timedelta(hours=CACHE_TTL_HOURS):
                return cache["latest"]
        except Exception:
            pass

    # Fetch from remote
    try:
        req = urllib.request.Request(
            REMOTE_URL,
            headers={"User-Agent": "cli-skill-update-checker"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            latest = json.loads(resp.read())["version"]
    except Exception:
        return None

    # Write cache
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps({
            "checked_at": datetime.now().isoformat(),
            "latest": latest,
        }))
    except Exception:
        pass

    return latest


def main():
    try:
        installed = get_installed_version()
        latest = get_latest_version()
        if latest and parse_version(latest) > parse_version(installed):
            print(f"cli-skill update available: {installed} → {latest} · run: claude plugin update cli@cli")
    except Exception:
        pass


if __name__ == "__main__":
    main()
