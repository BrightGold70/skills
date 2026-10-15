#!/bin/bash
# h-mad-advisor-warn.sh — PostToolUse advisory: the context budget, injected back
# to the model while it can still act on it.
#
# Two halves since 2026-10-15: the 45% ADVISOR note (below), and the 80%/90% RUN suggestion
# ("finish what you are on, then /handoff"), suggestive by operator decision. See the tail.
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

# Two independent halves, each with its own throttle stamp, emitted together in ONE payload:
#   1. the ADVISOR note (45%, `--mode advisor` DENY): "do not call advisor() now";
#   2. the RUN suggestion (80%/90%, `--mode run` HALT): "finish what you are doing, then close
#      out with /handoff". Suggestive by operator decision (2026-10-15), never obliging: it gives
#      time to complete the task in hand rather than demanding a halt.
# They stay worded apart (J45): a dying RUN must never read as an over-budget ADVISOR call.
# Every throttle failure falls through to SPEAKING: an extra note costs two lines, a missed one
# can cost the run.
STAMP_DIR="${TMPDIR:-/tmp}"
case "$SESSION" in
  ""|*/*|*..*) STAMP=""; RUN_STAMP="" ;;           # refuse to build a path from it
  *) STAMP="${STAMP_DIR%/}/h-mad-advisor-warn.${SESSION}.stamp"
     RUN_STAMP="${STAMP_DIR%/}/h-mad-run-suggest.${SESSION}.stamp" ;;
esac
NOW="$(date +%s 2>/dev/null || echo 0)"
TARGS=()
[ "$TRANSCRIPT" != "-" ] && [ -f "$TRANSCRIPT" ] && TARGS+=(--transcript "$TRANSCRIPT")

# --- 1. the advisor note -------------------------------------------------------------------
ADV_MSG=""
ADV_DUE=yes
if [ -n "$STAMP" ] && [ -f "$STAMP" ]; then
  THEN="$(cat "$STAMP" 2>/dev/null || echo 0)"
  case "$NOW$THEN" in
    *[!0-9]*|"") ;;                              # unreadable -> speak
    *) [ "$((NOW - THEN))" -lt "$EVERY" ] && ADV_DUE=no ;;
  esac
fi
if [ "$ADV_DUE" = yes ]; then
  OUT="$(python3 "$BUDGET" --window "$WINDOW" --ceiling "$CEILING" --mode advisor ${TARGS[@]+"${TARGS[@]}"} 2>/dev/null || true)"
  VERDICT="$(printf '%s\n' "$OUT" | grep '^CTXBUDGET:' || true)"
  # Only DENY speaks here. The glob is `CTXBUDGET: DENY` and nothing else: `--mode run`'s
  # ceiling is worded `HALT` on purpose (J45), and half 2 below owns it.
  case "$VERDICT" in
    *"CTXBUDGET: DENY"*)
      [ -n "$STAMP" ] && { date +%s > "$STAMP" 2>/dev/null || true; }
      PCT="$(printf '%s' "$VERDICT" | sed -n 's/.*pct=\([0-9.]*\).*/\1/p')"
      PROJ="$(printf '%s' "$VERDICT" | sed -n 's/.*projected=\([0-9]*\).*/\1/p')"
      ADV_MSG="[H-MAD] Context budget: ${PCT:-?}% of a ${WINDOW}-token window used (ceiling ${CEILING}%). \
An advisor() call forwards the whole transcript and would project to ~${PROJ:-?} tokens this turn. \
Prefer: hmad-dispatch exec agy <promptfile> (reviews in its own context, ~2k returns), \
or Agent(subagent_type: \"fork\"). Assumed window is ${WINDOW}; export HMAD_CONTEXT_WINDOW if it differs."
      ;;
  esac
fi

# --- 2. the run suggestion -----------------------------------------------------------------
RUN_AT="${HMAD_RUN_SUGGEST_AT:-80}"
URGENT_AT="${HMAD_RUN_URGENT_AT:-90}"
RUN_EVERY="${HMAD_RUN_SUGGEST_INTERVAL:-600}"
RUN_MSG=""
ROUT="$(python3 "$BUDGET" --window "$WINDOW" --ceiling "$RUN_AT" --mode run ${TARGS[@]+"${TARGS[@]}"} 2>/dev/null || true)"
RVERDICT="$(printf '%s\n' "$ROUT" | grep '^CTXBUDGET:' || true)"
case "$RVERDICT" in
  *"CTXBUDGET: HALT"*)                           # M:RUN-HALT-ONLY
    RPCT="$(printf '%s' "$RVERDICT" | sed -n 's/.*pct=\([0-9.]*\).*/\1/p')"
    BAND=soon
    python3 -c 'import sys; sys.exit(0 if float(sys.argv[1]) >= float(sys.argv[2]) else 1)' \
      "${RPCT:-0}" "$URGENT_AT" 2>/dev/null && BAND=urgent   # M:RUN-URGENT
    RUN_DUE=yes
    if [ -n "$RUN_STAMP" ] && [ -f "$RUN_STAMP" ]; then
      read -r LAST_BAND LAST_AT < "$RUN_STAMP" 2>/dev/null || LAST_BAND=""
      case "$LAST_BAND:${LAST_AT:-x}$NOW" in
        soon:*[!0-9]*|urgent:*[!0-9]*) ;;         # unreadable time -> speak
        "$BAND":*) [ "$((NOW - LAST_AT))" -lt "$RUN_EVERY" ] && RUN_DUE=no ;;   # M:RUN-THROTTLE
        urgent:*) [ "$BAND" = soon ] && [ "$((NOW - LAST_AT))" -lt "$RUN_EVERY" ] && RUN_DUE=no ;;
        *) ;;                                    # entering a higher band, or garbage -> speak
      esac
    fi
    if [ "$RUN_DUE" = yes ]; then
      [ -n "$RUN_STAMP" ] && { printf '%s %s\n' "$BAND" "$NOW" > "$RUN_STAMP" 2>/dev/null || true; }
      if [ "$BAND" = urgent ]; then
        RUN_MSG="[H-MAD] Run context: ${RPCT}% of a ${WINDOW}-token window used, close to the end. \
Suggestion, not a halt: finish only the step in hand (the current edit, test run or commit), \
then close out with /handoff --skip-scout --skip-memories. The doc, the index entry and the \
commit are what the next session needs; the skipped phases can run there."
      else
        RUN_MSG="[H-MAD] Run context: ${RPCT}% of a ${WINDOW}-token window used (suggest closing out past ${RUN_AT}%). \
No rush, and nothing is blocked: finish the task you are on and avoid starting a new large one, \
then run /handoff (WRITE) so the next session resumes instead of re-deriving. \
Inside an /h-mad run, the natural stopping point is the next phase boundary."
      fi
    fi
    ;;
esac

[ -n "$ADV_MSG$RUN_MSG" ] || exit 0
MSG="$ADV_MSG"
[ -n "$RUN_MSG" ] && MSG="${MSG:+$MSG

}$RUN_MSG"
python3 -c '
import json, sys
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": sys.argv[1],
}}))
' "$MSG" 2>/dev/null || printf '%s\n' "$MSG"
exit 0
