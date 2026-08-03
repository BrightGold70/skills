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

_resolve_state_file() {
  # Find the orchestrator state that governs the file being written.
  #
  # This used to be a bare "${CLAUDE_PROJECT_DIR:-.}/docs/.bkit-memory.json",
  # which assumes the state sits at the repo root. HemaSuite keeps its state at
  # `hematology-paper-writer/docs/.bkit-memory.json`, so that path never existed
  # and the fast-path below ("no state file -> allow") fired on EVERY write: a
  # full Phase 5 ran there believing production writes were gated. They were not,
  # and nothing said so — a gate that stands down silently is indistinguishable
  # from a gate that approves.
  local target="$1"
  local root="${CLAUDE_PROJECT_DIR:-.}" root_abs=""
  root_abs="$(cd "$root" 2>/dev/null && pwd -P)" || root_abs=""

  # 1. Repo-root layout — the common single-project case, and back-compat.
  if [ -n "$root_abs" ] && [ -f "$root_abs/docs/.bkit-memory.json" ]; then
    printf '%s\n' "$root_abs/docs/.bkit-memory.json"
    return 0
  fi

  # 2. Sub-project layout — walk UP from the file being written.
  [ -n "$target" ] || return 1
  local dir
  dir="$(cd "$(dirname "$target")" 2>/dev/null && pwd -P)" || return 1
  # Only walk within the project. A state file in a PARENT of this project
  # belongs to a different project, and adopting it would let one repo's Phase 5
  # gate writes in an unrelated sibling — a false block with nothing in the
  # current repo to explain it.
  if [ -n "$root_abs" ]; then
    case "$dir/" in
      "$root_abs"/*) ;;
      *) return 1 ;;
    esac
  fi
  while [ -n "$dir" ] && [ "$dir" != "/" ]; do
    if [ -f "$dir/docs/.bkit-memory.json" ]; then
      printf '%s\n' "$dir/docs/.bkit-memory.json"
      return 0
    fi
    [ -n "$root_abs" ] && [ "$dir" = "$root_abs" ] && break
    dir="$(dirname "$dir")"
  done
  return 1
}

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

# Resolved AFTER the target path, because a sub-project's state is found by
# walking up from the file being written — there is nothing else to search from.
STATE_FILE="$(_resolve_state_file "$TARGET_PATH" || true)"

# Fast path: no state file anywhere → no orchestrator → allow.
# This fail-open is correct for a project that simply does not use h-mad. It was
# wrong only because the search could not see a state file that existed.
# An unresolved search yields "", and `[ ! -f "" ]` is true, so this one test
# covers both "not found" and "found but gone".
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
# Test FILES are matched on the basename, not the whole path. `*test_*.py`
# matched "test_" anywhere, including a parent directory — so a production file
# under `test_helpers/` (or any dir with `test_` in its name) was silently
# exempted from the gate. Same silent-stand-down class as the state-file bug
# above, and found by its test harness: pytest's own tmp dirs are named
# `test_<name>0`, which exempted every fixture written under them.
case "${TARGET_PATH##*/}" in
  test_*.py|*_test.py|conftest*.py)
    exit 0 ;;
esac
# Test DIRECTORIES stay path-matched, anchored to a full segment.
case "$TARGET_PATH" in
  */tests/*|*/fixtures/*)
    exit 0 ;;
  *.md|*.yaml|*.yml|*.json|*.toml|*.txt|*.rst|*.cfg|*.ini)
    exit 0 ;;
  *.sh|*.bash|Makefile|Dockerfile|*.dockerignore|*.gitignore)
    exit 0 ;;
esac

# Only gate .py production files
[[ "$TARGET_PATH" != *.py ]] && exit 0

# --- Codex-authorship enforcement -------------------------------------------
# Codex writes via its OWN process (subprocess `codex exec`, or its pane); those
# writes never reach this PreToolUse hook. Only Claude's Write/Edit tool does. So
# a production write arriving HERE during step5 is Claude self-implementing — the
# exact thing Phase 5 delegates to Codex. Block it when Codex is available, and
# name the dispatch. The ONLY escape is an auditable declaration that Codex is
# unavailable: state `codex_status` = unavailable|exhausted, or the
# HMAD_CODEX_UNAVAILABLE env override. Silent self-authoring is never allowed.
CODEX_STATUS=$(jq -r --arg k "$ACTIVE" \
  '.orchestrator_state[$k].codex_status // "available"' "$STATE_FILE" 2>/dev/null || echo available)
if [ -z "${HMAD_CODEX_UNAVAILABLE:-}" ] \
   && [ "$CODEX_STATUS" != "unavailable" ] && [ "$CODEX_STATUS" != "exhausted" ] \
   && command -v codex >/dev/null 2>&1; then
  echo "[H-MAD-TDD-GATE] BLOCK: Phase 5 implementation must be authored by Codex, not Claude." >&2
  echo "Dispatch this module to Codex: hmad-dispatch exec codex <promptfile>  (or: send codex)." >&2
  echo "Codex looks available (codex on PATH; codex_status=$CODEX_STATUS). If it is out of quota, record it —" >&2
  echo "  python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py --feature $ACTIVE --set codex_status=exhausted \"$STATE_FILE\"" >&2
  echo "then Claude may author the fallback (still test-first). Or export HMAD_CODEX_UNAVAILABLE=1 for a one-off." >&2
  exit 1
fi
# Codex unavailable / declared exhausted → fall through: Claude may author the
# fallback, still under the test-first gate below.

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
