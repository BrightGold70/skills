#!/bin/bash
# h_mad_emit_marker.sh — emit a [H-MAD] log line.
# Usage: h_mad_emit_marker.sh <feature> <phase> <decision>

FEATURE="${1:-?}"
PHASE="${2:-?}"
DECISION="${3:-?}"

echo "[H-MAD] $FEATURE phase$PHASE $DECISION"
