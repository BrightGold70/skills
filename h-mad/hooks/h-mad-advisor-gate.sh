#!/bin/bash
# h-mad-advisor-gate.sh — PreToolUse hook denying `advisor()` above the context ceiling.
#
# `advisor()` forwards the whole transcript to a second model and bills it into the
# same turn, so the turn costs ~2x the current context. Above ~50% window used it
# cannot fit, and the overflow ends the run. SKILL.md §"Orchestrator context hygiene
# (your own window)" carries the rule; this makes it mechanical, because a rule that
# only lives in prose is one the orchestrator can talk itself out of at exactly the
# moment it is most expensive to be wrong.
#
# Install as a PreToolUse hook in ~/.claude/settings.json:
#   { "matcher": "advisor", "hooks": [{ "type": "command",
#     "command": "bash $HOME/.claude/skills/h-mad/hooks/h-mad-advisor-gate.sh" }] }
#
# It rides the `~/.claude/skills/h-mad` symlink deliberately: a second hook symlink
# would add a SPLIT_INSTALL failure mode for no gain, and the skills link is already
# verified by h_mad_install_check.py.
#
# NOT `set -e`. The budget script exits 2 on a cannot-judge, and under `set -e` that
# rc would propagate out of this hook — where 2 means BLOCK. A fresh session with no
# usage record yet would then be denied at exactly the point the ladder says to call
# early. Read the CTXBUDGET: token, never the rc; allow anything that is not DENY.
set -uo pipefail

BUDGET="${HMAD_CONTEXT_BUDGET_SCRIPT:-$HOME/.claude/skills/h-mad/scripts/h_mad_context_budget.py}"
CEILING="${HMAD_CONTEXT_CEILING:-45}"
WINDOW="${HMAD_CONTEXT_WINDOW:-1000000}"

# Deliberate escape hatch, checked before any work: the ceiling is a budget, not a
# safety property, and an operator who has decided to spend it must not have to
# unwire a hook to do so. A deny that teaches no way out gets disabled wholesale.
[ "${HMAD_ADVISOR_OVERRIDE:-}" = "1" ] && exit 0

INPUT="$(cat 2>/dev/null || true)"

# tool_name and transcript_path off the hook payload. `transcript_path` is the
# harness naming the exact file, which beats the script's own session-id lookup.
read -r TOOL_NAME TRANSCRIPT <<EOF
$(printf '%s' "$INPUT" | python3 -c '
import sys, json
try:
    d = json.loads(sys.stdin.read())
except Exception:
    d = {}
if not isinstance(d, dict):
    d = {}
name = d.get("tool_name") or ""
path = d.get("transcript_path") or ""
# a path with whitespace would split the read; hand back a sentinel instead
if " " in path or "\t" in path:
    path = ""
print(name.strip() or "-", path.strip() or "-")
' 2>/dev/null || printf '%s %s' "-" "-")
EOF
TOOL_NAME="${TOOL_NAME:--}"
TRANSCRIPT="${TRANSCRIPT:--}"

# Only advisor. A "*" matcher, or a harness that renames the tool, must not turn
# this into a gate on everything — a hook that blocks the wrong tool gets removed,
# taking the real rule with it.
[ "$TOOL_NAME" = "advisor" ] || exit 0

[ -f "$BUDGET" ] || exit 0   # no checker -> allow; this hook never blocks blind

ARGS=(--window "$WINDOW" --ceiling "$CEILING")
[ "$TRANSCRIPT" != "-" ] && [ -f "$TRANSCRIPT" ] && ARGS+=(--transcript "$TRANSCRIPT")

OUT="$(python3 "$BUDGET" "${ARGS[@]}" 2>/dev/null || true)"
VERDICT="$(printf '%s\n' "$OUT" | grep '^CTXBUDGET:' || true)"

case "$VERDICT" in
  *"CTXBUDGET: DENY"*) ;;
  *) exit 0 ;;   # OK, UNKNOWN, no token at all -> allow. Cannot-judge is not a block.
esac

USED="$(printf '%s' "$VERDICT" | sed -n 's/.*used=\([0-9]*\).*/\1/p')"
PCT="$(printf '%s' "$VERDICT" | sed -n 's/.*pct=\([0-9.]*\).*/\1/p')"
PROJ="$(printf '%s' "$VERDICT" | sed -n 's/.*projected=\([0-9]*\).*/\1/p')"

{
  echo "[H-MAD-ADVISOR-GATE] BLOCK: advisor() would cost a second full copy of this session."
  echo "  $VERDICT"
  echo "  ~${USED:-?} tokens of context now; the advisor turn projects to ~${PROJ:-?} (${PCT:-?}% used, ceiling ${CEILING}%)."
  echo "  Window assumed to be ${WINDOW}. If this model's window differs, export HMAD_CONTEXT_WINDOW."
  echo "Substitute instead (SKILL.md \"Orchestrator context hygiene (your own window)\"):"
  echo "  1. hmad-dispatch exec agy <promptfile>   — reviews in its own context; only its report (~2k) returns"
  echo "  2. Agent(subagent_type: \"fork\")          — free for this window, but runs on YOUR model"
  echo "  3. /compact FIRST, then call             — lossy, last resort; compacting after an overflow recovers nothing"
  echo "To spend the budget anyway: HMAD_ADVISOR_OVERRIDE=1"
} >&2
exit 2
