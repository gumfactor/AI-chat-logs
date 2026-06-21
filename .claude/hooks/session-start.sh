#!/bin/bash
set -euo pipefail

# Assign a Task ID and write a metadata.yaml stub for this session.
# Outputs hookSpecificOutput JSON with additionalContext injecting the Task ID.
REPO_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
exec python3 "$REPO_ROOT/tools/session_init.py" \
    --agent claude \
    --hook-event SessionStart
