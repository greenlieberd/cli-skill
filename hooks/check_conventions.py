"""
CLI convention check — runs before Write/Edit in any new CLI scaffolding session.
Warns when generated code violates Propane CLI patterns.
Does not block (exit 0 always). Issues appear as Claude system messages.
"""
import json
import sys

data = json.load(sys.stdin)
inp = data.get('tool_input', {})

file_path = inp.get('file_path', '') or ''
new_content = inp.get('new_string', '') or inp.get('content', '') or ''
warnings = []

# Only check TypeScript source files
if file_path.endswith('.ts') or file_path.endswith('.tsx'):

    # Rule: model IDs only in src/models.ts
    model_ids = ['claude-sonnet', 'claude-haiku', 'claude-opus']
    is_models_file = file_path.endswith('models.ts')
    if not is_models_file:
        for mid in model_ids:
            if mid in new_content:
                warnings.append(
                    f'Hardcoded model ID "{mid}" in {file_path}. '
                    f'Import from src/models.ts instead.'
                )

    # Rule: no database packages
    db_packages = ['better-sqlite3', 'sqlite', ' pg ', ' mysql ', 'mongoose', 'prisma', 'drizzle-orm']
    for pkg in db_packages:
        if pkg in new_content:
            warnings.append(
                f'Database package "{pkg.strip()}" detected in {file_path}. '
                f'Use flat files — see cli-skill/guides/04-data-philosophy.md.'
            )

    # Rule: sources must not throw — check for throw in source files
    import os
    if 'sources/' in file_path and 'throw ' in new_content and 'sourceError' not in new_content:
        warnings.append(
            f'Source file {file_path} uses throw without sourceError(). '
            f'Sources must return SourceResult — never throw.'
        )

if warnings:
    msg = '\n'.join(f'\u26a0\ufe0f  {w}' for w in warnings)
    print(json.dumps({"continue": True, "systemMessage": msg}))
else:
    print(json.dumps({"continue": True}))
