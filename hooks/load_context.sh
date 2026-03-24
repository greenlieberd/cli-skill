#!/bin/bash
# Runs at session start. Reminds Claude of the CLI architecture standard.
# Output goes to Claude as a system message via hooks.json SessionStart hook.

echo '{"continue":true,"systemMessage":"CLI projects: use /new-cli to scaffold. Key rules: (1) model IDs only in src/models.ts, (2) sources always return SourceResult — never throw, (3) no databases — flat files only, (4) .propane/ for runtime state, output/ for generated files. See cli-skill/guides/ for full reference."}'
