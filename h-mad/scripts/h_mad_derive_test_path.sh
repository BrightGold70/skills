#!/bin/bash
# h_mad_derive_test_path.sh — map a production .py path to its test path.
# Returns empty string for unknown patterns or non-.py files.
# Used by h_mad_tdd_judge.py.

set -euo pipefail

PROD_PATH="${1:-}"

# Empty input → empty output
[ -z "$PROD_PATH" ] && exit 0

# Non-.py files → empty
[[ "$PROD_PATH" != *.py ]] && exit 0

# Test files themselves → empty (caller shouldn't ask). Read the BASENAME the way
# _is_production_python does: `test_` anywhere in the path used to hide production
# names such as h_mad_test_boundaries_check.py (2026-10-31 residual).
BASE_NAME="${PROD_PATH##*/}"
[[ "$BASE_NAME" == test_* || "$BASE_NAME" == *_test.py || "$BASE_NAME" == conftest* ]] && exit 0  # M:NM-TEST-BASENAME
[[ "$PROD_PATH" == */tests/* || "$PROD_PATH" == tests/* ]] && exit 0  # M:NM-TEST-DIR

# Extract project root
case "$PROD_PATH" in
  hematology-paper-writer/*)
    PROJECT="hematology-paper-writer"
    ;;
  clinical-statistics-analyzer/*)
    PROJECT="clinical-statistics-analyzer"
    ;;
  shared/*)
    PROJECT="shared"
    ;;
  h-mad/scripts/*)
    # h-mad's own scripts (row 2844). Hooks are hyphenated and have no 1:1 test name.
    PROJECT="h-mad"
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
[ "$MOD_BASENAME" = "__init__" ] && exit 0
[ "$MOD_BASENAME" = "__main__" ] && exit 0

echo "${PROJECT}/tests/test_${MOD_BASENAME}.py"
