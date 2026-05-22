#!/bin/bash
# h_mad_derive_test_path.sh — map a production .py path to its test path.
# Returns empty string for unknown patterns or non-.py files.
# Used by ~/.claude/hooks/h-mad-tdd-gate.sh and the /h-mad skill.

set -euo pipefail

PROD_PATH="${1:-}"

# Empty input → empty output
[ -z "$PROD_PATH" ] && exit 0

# Non-.py files → empty
case "$PROD_PATH" in
  *.py) ;;
  *) exit 0 ;;
esac

# Test files themselves → empty (caller shouldn't ask)
case "$PROD_PATH" in
  *test_*.py|*/tests/*|*conftest*) exit 0 ;;
esac

# Extract project root
case "$PROD_PATH" in
  hematology-paper-writer/*)
    PROJECT="hematology-paper-writer"
    ;;
  clinical-statistics-analyzer/*)
    PROJECT="clinical-statistics-analyzer"
    ;;
  *)
    # Unknown project layout → empty
    exit 0
    ;;
esac

# Strip project prefix to get internal path, then take basename
INTERNAL="${PROD_PATH#${PROJECT}/}"
MOD_BASENAME=$(basename "$INTERNAL" .py)

# Skip top-level __init__.py and similar
case "$MOD_BASENAME" in
  __init__|__main__) exit 0 ;;
esac

echo "${PROJECT}/tests/test_${MOD_BASENAME}.py"
