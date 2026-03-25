"""
Session logger — fires on Stop hook after any cli:* skill session.
Writes a compact JSONL entry to .cli/sessions/ for later learning extraction.
Fail-silent: never blocks or crashes the main session.
"""
import json
import sys
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

def is_cli_project(cwd: Path) -> bool:
    if (cwd / 'src' / 'cli.ts').exists():
        return True
    pkg = cwd / 'package.json'
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
            scripts = data.get('scripts', {})
            return 'hud' in scripts or 'bun hud' in str(scripts)
        except Exception:
            pass
    return False

def detect_skill(cwd: Path) -> str:
    """Guess which cli:* skill ran based on what was recently touched."""
    dot_cli = cwd / '.cli'
    if not dot_cli.exists():
        return 'unknown'

    # Check modification times on .cli/ subfolders
    plan_md = dot_cli / 'plan' / 'PLAN.md'
    explore_md = dot_cli / 'audit' / 'EXPLORE.md'
    session_dir = dot_cli / 'sessions'

    now = datetime.now(timezone.utc).timestamp()
    threshold = 600  # modified in last 10 minutes

    def fresh(p: Path) -> bool:
        return p.exists() and (now - p.stat().st_mtime) < threshold

    if fresh(explore_md) and not fresh(plan_md):
        return 'cli:explore'
    if fresh(plan_md) and not (cwd / 'src' / 'cli.ts').exists():
        return 'cli:plan'
    if fresh(plan_md) and (cwd / 'src' / 'cli.ts').exists():
        # Check if src/cli.ts is brand new (new project) or old (audit)
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', '-1', '--diff-filter=A', '--', 'src/cli.ts'],
                cwd=cwd, capture_output=True, text=True, timeout=3
            )
            if result.stdout.strip():
                return 'cli:new'
        except Exception:
            pass
        return 'cli:audit'
    return 'unknown'

def get_recent_changes(cwd: Path) -> list:
    """Files written or edited in the current git session."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD'],
            cwd=cwd, capture_output=True, text=True, timeout=3
        )
        staged = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            cwd=cwd, capture_output=True, text=True, timeout=3
        )
        files = set()
        for line in (result.stdout + staged.stdout).strip().splitlines():
            if line.strip():
                files.add(line.strip())
        return sorted(files)[:20]
    except Exception:
        return []

def get_project_name(cwd: Path) -> str:
    pkg = cwd / 'package.json'
    if pkg.exists():
        try:
            return json.loads(pkg.read_text()).get('name', cwd.name)
        except Exception:
            pass
    return cwd.name

def get_pending_errors(cwd: Path) -> list:
    """Read errors captured by the bash error hook during this session."""
    buf = cwd / '.cli' / 'sessions' / '.errors_buffer.jsonl'
    if not buf.exists():
        return []
    try:
        errors = []
        for line in buf.read_text().strip().splitlines():
            if line.strip():
                errors.append(json.loads(line))
        buf.unlink()  # clear after reading
        return errors[-10:]  # cap at 10
    except Exception:
        return []

def main():
    try:
        event = json.loads(sys.stdin.read())
    except Exception:
        print(json.dumps({"continue": True}))
        return

    cwd = Path(os.getcwd())

    if not is_cli_project(cwd):
        print(json.dumps({"continue": True}))
        return

    try:
        sessions_dir = cwd / '.cli' / 'sessions'
        sessions_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc)
        entry = {
            "ts": ts.isoformat(),
            "project": get_project_name(cwd),
            "skill": detect_skill(cwd),
            "changed_files": get_recent_changes(cwd),
            "errors": get_pending_errors(cwd),
            "tokens": event.get("usage", {}),
            "stop_reason": event.get("stop_reason", "unknown"),
        }

        # Read .cli/plan/PLAN.md for task progress snapshot
        plan_md = cwd / '.cli' / 'plan' / 'PLAN.md'
        if plan_md.exists():
            content = plan_md.read_text()
            done = content.count('- [x]')
            total = content.count('- [x]') + content.count('- [ ]')
            entry["plan_progress"] = f"{done}/{total}"

        log_file = sessions_dir / f"{ts.strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    except Exception:
        pass  # fail-silent always

    print(json.dumps({"continue": True}))

if __name__ == '__main__':
    main()
