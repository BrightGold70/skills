#!/bin/bash
# h_mad_emit_marker.sh — emit a [H-MAD] log line.
# Usage: h_mad_emit_marker.sh <feature> <phase> <decision>
#
#   <phase> is the phase label without the "phase" prefix ("2", "5d",
#   "6a-prime"). A caller that already includes the prefix is tolerated —
#   prefixing is idempotent — because doubling it ("phasephase2") corrupts
#   the marker stream that tooling greps after a run.
#
# Markers are that stream, so a malformed line is worse than none: every
# argument is required, and a bad call fails loudly on stderr rather than
# emitting a partial marker padded with "?" placeholders.

set -uo pipefail

usage() {
  echo "usage: h_mad_emit_marker.sh <feature> <phase> <decision>" >&2
  echo "  e.g. h_mad_emit_marker.sh my-feature 5d red_not_all_failing" >&2
  exit 2
}

[ "$#" -eq 3 ] || usage

FEATURE="$1"
PHASE="$2"
DECISION="$3"

[ -n "$FEATURE" ] && [ -n "$PHASE" ] && [ -n "$DECISION" ] || usage

# Idempotent prefix: accept both "2" and "phase2".
PHASE="${PHASE#phase}"

echo "[H-MAD] $FEATURE phase$PHASE $DECISION"
