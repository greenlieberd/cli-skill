#!/usr/bin/env python3
"""
auto_learn.py — frequency-based session compression. Called by session_logger.py
after every AUTO_LEARN_EVERY sessions. Reads all .cli/sessions/*.jsonl files,
extracts recurring patterns, and writes a compact SUMMARY.md to .cli/learnings/.

No stdin required. Takes project path as first argument.
Fail-silent: never blocks or crashes a session.
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

AUTO_LEARN_EVERY = 5


def load_sessions(sessions_dir: Path):
    """Load all session entries from JSONL files, excluding error buffer."""
    sessions = []
    files = sorted(f for f in sessions_dir.glob("*.jsonl") if f.name != ".errors_buffer.jsonl")
    for f in files:
        for line in f.read_text(errors="replace").strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                sessions.append(json.loads(line))
            except Exception:
                pass
    return sessions


def recency_weight(ts_str: str, now: datetime) -> float:
    """Recent sessions count more; old ones fade. Frequency promotes, silence fades."""
    try:
        ts = datetime.fromisoformat(ts_str)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age_days = (now - ts).days
        if age_days <= 7:
            return 2.0   # last week: promoted
        if age_days <= 30:
            return 1.0   # last month: normal
        return 0.5       # older: fading
    except Exception:
        return 1.0


def extract_patterns(sessions):
    """Return hot_files, recurring_errors, skill_dist, total_cost, latest_progress."""
    now = datetime.now(timezone.utc)

    file_weights = Counter()
    error_weights = Counter()
    skill_counts = Counter()
    total_cost = 0.0
    latest_progress = None
    latest_ts = None

    for s in sessions:
        w = recency_weight(s.get("ts", ""), now)
        skill = s.get("skill", "unknown")
        skill_counts[skill] += 1

        for f in s.get("changed_files", []):
            file_weights[f] += w

        for e in s.get("errors", []):
            cmd = e.get("command", "")
            snippet = e.get("error", e.get("error_snippet", ""))[:60]
            key = f"{cmd}: {snippet}" if snippet else cmd
            if key:
                error_weights[key] += w

        cost = s.get("tokens", {}).get("cost_usd", 0)
        try:
            total_cost += float(cost)
        except Exception:
            pass

        progress = s.get("plan_progress")
        ts = s.get("ts", "")
        if progress and (latest_ts is None or ts > latest_ts):
            latest_progress = progress
            latest_ts = ts

    hot_files = [f for f, _ in file_weights.most_common(5) if file_weights[f] >= 1.5]
    recurring_errors = [e for e, _ in error_weights.most_common(3) if error_weights[e] >= 1.5]

    return hot_files, recurring_errors, skill_counts, total_cost, latest_progress


def render_summary(sessions, project_name: str) -> str:
    if not sessions:
        return ""

    hot_files, recurring_errors, skill_counts, total_cost, latest_progress = extract_patterns(sessions)

    dates = sorted(s.get("ts", "") for s in sessions if s.get("ts"))
    first_date = dates[0][:10] if dates else "?"
    last_date = dates[-1][:10] if dates else "?"
    n = len(sessions)

    lines = [
        "---",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        f"sessions_analyzed: {n}",
        f"date_range: {first_date} → {last_date}",
        "source: auto-generated (frequency analysis)",
        "---",
        "",
        f"# Session learnings — {project_name}",
        "",
    ]

    if hot_files:
        lines.append("## Hot files (touch carefully)")
        for f in hot_files:
            lines.append(f"- `{f}` — changed in most sessions")
        lines.append("")

    if recurring_errors:
        lines.append("## Recurring errors")
        for e in recurring_errors:
            lines.append(f"- `{e}`")
        lines.append("")

    if skill_counts:
        top_skills = ", ".join(f"{s} ({c}x)" for s, c in skill_counts.most_common(3))
        lines.append(f"## Activity")
        lines.append(f"- Skills: {top_skills}")
        if latest_progress:
            lines.append(f"- Plan progress: {latest_progress} tasks complete (last session)")
        lines.append(f"- Total cost: ${total_cost:.4f} USD across {n} sessions")
        lines.append("")

    lines.append("Full details: run /cli:learn to extract richer project memory.")
    lines.append("")

    return "\n".join(lines)


def main():
    project_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.getcwd())
    sessions_dir = project_path / ".cli" / "sessions"

    if not sessions_dir.exists():
        return

    sessions = load_sessions(sessions_dir)
    if not sessions:
        return

    project_name = project_path.name
    pkg = project_path / "package.json"
    if pkg.exists():
        try:
            project_name = json.loads(pkg.read_text()).get("name", project_name)
        except Exception:
            pass

    summary = render_summary(sessions, project_name)
    if not summary:
        return

    learnings_dir = project_path / ".cli" / "learnings"
    learnings_dir.mkdir(parents=True, exist_ok=True)
    (learnings_dir / "SUMMARY.md").write_text(summary)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-silent always
