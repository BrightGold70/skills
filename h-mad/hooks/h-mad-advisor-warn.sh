#!/bin/bash
# h-mad-advisor-warn.sh — PostToolUse advisory: the context budget, injected back
# to the model while it can still act on it.
#
# THIS IS NOT A GATE, AND IT CANNOT BE ONE. `advisor()` is a `server_tool_use`
# block executed server-side; it never enters the harness's local tool-dispatch
# path, so no tool-scoped hook event — PreToolUse, PermissionRequest, PostToolUse,
# PostToolUseFailure — ever fires for it. Its predecessor `h-mad-advisor-gate.sh`
# was registered as `{"matcher": "advisor"}` on PreToolUse and, on two
# instrumented probes with the marker at line 1, never ran once (J44). Verified
# twice over: the 2.1.241 binary calls it "the server-side advisor tool" and emits
# `server_tool_use` / `advisor_tool_result` blocks for it, and a live transcript
# carrying three real `advisor()` calls records them as `server_tool_use`
# name=advisor beside 101 ordinary `tool_use` blocks for the tools that DO fire
# hooks. Do not re-propose a PreToolUse matcher for this; no matcher string works.
#
# What is attachable is the turn BEFORE the call. `advisor()` forwards the whole
# transcript and bills it into the same turn, so the turn costs ~2x the current
# context; above the ceiling it cannot fit and the overflow ends the run. This
# hook rides PostToolUse — the event whose firing rate tracks the risk, because
# tool results are what grow a transcript — and injects the budget verdict as
# `additionalContext`. The model reads it during exactly the orientation window in
# which it decides whether to call the advisor.
#
# Install as a PostToolUse hook in ~/.claude/settings.json:
#   { "matcher": "*", "hooks": [{ "type": "command",
#     "command": "bash $HOME/.claude/skills/h-mad/hooks/h-mad-advisor-warn.sh" }] }
#
# It rides the `~/.claude/skills/h-mad` symlink deliberately: a second hook
# symlink would add a SPLIT_INSTALL failure mode for no gain, and the skills link
# is already verified by h_mad_install_check.py.
#
# There is no override env var, because an advisory has nothing to escape. The old
# gate needed `HMAD_ADVISOR_OVERRIDE` precisely because it could refuse; a refusal
# that teaches no way out gets deleted from settings.json wholesale, taking the
# rule with it. This one cannot refuse, so it cannot earn that reaction.
#
# NOT `set -e`. The budget script exits 2 on a cannot-judge, and under `set -e`
# that rc would propagate out. Read the CTXBUDGET: token, never the rc.
set -uo pipefail

BUDGET="${HMAD_CONTEXT_BUDGET_SCRIPT:-$HOME/.claude/skills/h-mad/scripts/h_mad_context_budget.py}"
CEILING="${HMAD_CONTEXT_CEILING:-45}"
WINDOW="${HMAD_CONTEXT_WINDOW:-1000000}"
# Seconds between emissions. Not a cost control — the check measures at ~60 ms on
# a 2.3 MB transcript, cheap enough for every tool call. It bounds REPETITION: the
# verdict does not change between two calls a second apart, and a warning that
# reprints on all of them is itself context bloat, which is the thing this hook
# exists to prevent.
EVERY="${HMAD_ADVISOR_WARN_INTERVAL:-60}"

INPUT="$(cat 2>/dev/null || true)"

# session_id and transcript_path off the hook payload. `transcript_path` is the
# harness naming the exact file, which beats the script's own session-id lookup;
# `session_id` keys the throttle stamp so two concurrent sessions do not silence
# each other.
read -r SESSION TRANSCRIPT <<EOF
$(printf '%s' "$INPUT" | python3 -c '
import sys, json
try:
    d = json.loads(sys.stdin.read())
except Exception:
    d = {}
if not isinstance(d, dict):
    d = {}
sid = d.get("session_id") or ""
path = d.get("transcript_path") or ""
# a path with whitespace would split the read; hand back a sentinel instead
if " " in path or "\t" in path:
    path = ""
print(sid.strip() or "-", path.strip() or "-")
' 2>/dev/null || printf '%s %s' "-" "-")
EOF
SESSION="${SESSION:--}"
TRANSCRIPT="${TRANSCRIPT:--}"

[ -f "$BUDGET" ] || exit 0   # no checker -> say nothing; this hook never guesses

# Throttle. A stamp younger than $EVERY means we already said it recently.
# Every failure path here falls through to EMITTING, not to silence: an advisory
# that cannot prove it is repeating itself should repeat itself, because the cost
# of one extra warning is two lines and the cost of a missed one is the run.
STAMP_DIR="${TMPDIR:-/tmp}"
case "$SESSION" in
  ""|*/*|*..*) STAMP="" ;;                       # refuse to build a path from it
  *) STAMP="${STAMP_DIR%/}/h-mad-advisor-warn.${SESSION}.stamp" ;;
esac
if [ -n "$STAMP" ] && [ -f "$STAMP" ]; then
  NOW="$(date +%s 2>/dev/null || echo 0)"
  THEN="$(cat "$STAMP" 2>/dev/null || echo 0)"
  case "$NOW$THEN" in
    *[!0-9]*|"") ;;                              # unreadable -> emit
    *) [ "$((NOW - THEN))" -lt "$EVERY" ] && exit 0 ;;
  esac
fi

ARGS=(--window "$WINDOW" --ceiling "$CEILING" --mode advisor)
[ "$TRANSCRIPT" != "-" ] && [ -f "$TRANSCRIPT" ] && ARGS+=(--transcript "$TRANSCRIPT")

OUT="$(python3 "$BUDGET" "${ARGS[@]}" 2>/dev/null || true)"
VERDICT="$(printf '%s\n' "$OUT" | grep '^CTXBUDGET:' || true)"

# Only DENY speaks. OK, UNKNOWN and a missing token all mean "nothing useful to
# say", and a hook that narrates its own silence is the bloat it is warning about.
# The glob is `CTXBUDGET: DENY` and nothing else: `--mode run`'s ceiling is worded
# `HALT` on purpose so a dying RUN cannot be mistaken for an over-budget ADVISOR
# call (J45). Matching loosely here would collapse that distinction.
case "$VERDICT" in
  *"CTXBUDGET: DENY"*) ;;
  *) exit 0 ;;
esac

[ -n "$STAMP" ] && { date +%s > "$STAMP" 2>/dev/null || true; }

PCT="$(printf '%s' "$VERDICT" | sed -n 's/.*pct=\([0-9.]*\).*/\1/p')"
PROJ="$(printf '%s' "$VERDICT" | sed -n 's/.*projected=\([0-9]*\).*/\1/p')"

MSG="[H-MAD] Context budget: ${PCT:-?}% of a ${WINDOW}-token window used (ceiling ${CEILING}%). \
An advisor() call forwards the whole transcript and would project to ~${PROJ:-?} tokens this turn. \
Prefer: hmad-dispatch exec agy <promptfile> (reviews in its own context, ~2k returns), \
or Agent(subagent_type: \"fork\"). Assumed window is ${WINDOW}; export HMAD_CONTEXT_WINDOW if it differs."

python3 -c '
import json, sys
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": sys.argv[1],
}}))
' "$MSG" 2>/dev/null || printf '%s\n' "$MSG"
exit 0
