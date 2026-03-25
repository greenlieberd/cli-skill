"""
Error capture — fires PostToolUse on Bash.
Buffers errors to .cli/sessions/.errors_buffer.jsonl
so session_logger can include them in the session summary.
Fail-silent always. Never blocks.
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

ERROR_SIGNALS = [
    'error:', 'Error:', 'ERROR:', 'failed', 'Failed',
    'Cannot find', 'Module not found', 'SyntaxError',
    'TypeError', 'ReferenceError', 'not found', 'ENOENT',
    'exit code 1', 'exit status 1',
]

def looks_like_error(output: str) -> bool:
    if not output:
        return False
    for signal in ERROR_SIGNALS:
        if signal in output:
            return True
    return False

def main():
    try:
        event = json.loads(sys.stdin.read())
    except Exception:
        print(json.dumps({"continue": True}))
        return

    try:
        tool_input = event.get('tool_input', {})
        tool_response = event.get('tool_response', {})
        output = tool_response.get('output', '') or ''
        command = tool_input.get('command', '') or ''
        description = tool_input.get('description', '') or ''

        # Only log if it looks like something went wrong
        if not looks_like_error(output):
            print(json.dumps({"continue": True}))
            return

        # Only in CLI projects
        cwd = Path(os.getcwd())
        has_cli = (cwd / 'src' / 'cli.ts').exists()
        has_hud = False
        pkg = cwd / 'package.json'
        if pkg.exists():
            try:
                has_hud = 'hud' in json.loads(pkg.read_text()).get('scripts', {})
            except Exception:
                pass

        if not has_cli and not has_hud:
            print(json.dumps({"continue": True}))
            return

        buf = cwd / '.cli' / 'sessions' / '.errors_buffer.jsonl'
        buf.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "command": command[:200],
            "description": description[:100],
            "error_snippet": output[:500],
        }

        with open(buf, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    except Exception:
        pass  # fail-silent always

    print(json.dumps({"continue": True}))

if __name__ == '__main__':
    main()
