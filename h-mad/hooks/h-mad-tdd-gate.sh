#!/bin/bash
# h-mad-tdd-gate.sh — PreToolUse hook gating Write/Edit during /h-mad Phase 5.
# Fast no-op when no Phase 5 run is active. Blocks production writes
# missing a corresponding failing test.
# v2.2: phase tag is "step5" (not "step7" as in v1).
#
# Install as a PreToolUse hook in ~/.claude/settings.json:
#   "hooks": {
#     "PreToolUse": [
#       { "matcher": "Write|Edit", "hooks": [{ "type": "command", "command": "bash ~/.claude/skills/h-mad/hooks/h-mad-tdd-gate.sh \"$CLAUDE_TOOL_INPUT_PATH\"" }] }
#     ]
#   }

set -euo pipefail

STATE_FILE="${CLAUDE_PROJECT_DIR:-.}/docs/.bkit-memory.json"

# Claude Code PreToolUse hooks receive tool input as JSON via stdin.
# Positional arg is supported for direct invocation / testing.
if [ -n "${1:-}" ]; then
  TARGET_PATH="$1"
else
  # Read JSON from stdin; extract file_path field
  INPUT=$(cat 2>/dev/null || true)
  TARGET_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    print(d.get('file_path', d.get('path', '')))
except Exception:
    print('')
" 2>/dev/null || true)
fi

# Fast path: no state file → no orchestrator → allow
[ ! -f "$STATE_FILE" ] && exit 0

# Need jq to parse state
if ! command -v jq >/dev/null 2>&1; then
  # No jq available → fail open (allow). Hook never blocks unless it can confirm step5.
  exit 0
fi

# Check if any feature is in step5
ACTIVE=$(jq -r '
  .orchestrator_state // {} |
  to_entries[] |
  select(.value.phase == "step5") |
  .key
' "$STATE_FILE" 2>/dev/null | head -1)

[ -z "$ACTIVE" ] && exit 0

# Phase 5 active — apply TDD gate.
# Empty target path → allow (not a file write)
[ -z "$TARGET_PATH" ] && exit 0

# Allow test files, fixtures, docs, config files unconditionally.
case "$TARGET_PATH" in
  *test_*.py|*/tests/*|*conftest*.py|*/fixtures/*)
    exit 0 ;;
  *.md|*.yaml|*.yml|*.json|*.toml|*.txt|*.rst|*.cfg|*.ini)
    exit 0 ;;
  *.sh|*.bash|Makefile|Dockerfile|*.dockerignore|*.gitignore)
    exit 0 ;;
esac

# Only gate .py production files
[[ "$TARGET_PATH" != *.py ]] && exit 0

# Production-code write → require derivable test that currently fails.
DERIVE_SCRIPT="$HOME/.claude/skills/h-mad/scripts/h_mad_derive_test_path.sh"
if [ ! -x "$DERIVE_SCRIPT" ]; then
  echo "[H-MAD-TDD-GATE] BLOCK: derivation script missing at $DERIVE_SCRIPT" >&2
  exit 1
fi

TEST_PATH=$("$DERIVE_SCRIPT" "$TARGET_PATH")
if [ -z "$TEST_PATH" ]; then
  echo "[H-MAD-TDD-GATE] BLOCK: cannot derive test path for $TARGET_PATH" >&2
  echo "Either add the path pattern to h_mad_derive_test_path.sh or write the test manually first." >&2
  exit 1
fi

if [ ! -f "$TEST_PATH" ]; then
  echo "[H-MAD-TDD-GATE] BLOCK: no test file at $TEST_PATH for $TARGET_PATH" >&2
  echo "Write a failing test first (RED-phase) before implementing." >&2
  exit 1
fi

# Test file exists. If target file being MODIFIED (already exists), confirm test currently fails.
if [ -f "$TARGET_PATH" ]; then
  if pytest "$TEST_PATH" -x -q --no-header >/dev/null 2>&1; then
    echo "[H-MAD-TDD-GATE] BLOCK: $TEST_PATH already passing; no new code needed?" >&2
    echo "Either update the test to RED first, or skip this Edit." >&2
    exit 1
  fi
fi

exit 0
