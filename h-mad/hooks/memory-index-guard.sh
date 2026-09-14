#!/bin/bash
# memory-index-guard.sh — surface the auto-memory index cap AUTOMATICALLY.
#
# The cap (25000 bytes / 200 lines) is enforced at LOAD, not at write. Past it
# the write SUCCEEDS and the overflow is dropped on EVERY load, silently, with no
# error at the point of loss. `h_mad_check_memory_index.py` detects that, and
# until now it ran only when someone READ the step that documents it in
# `handoff/references/auto-memories.md`. A documented rule is not an enforced
# one: nothing failed, nothing warned, and the index sat at 100% of cap for a day
# with two entries already invisible.
#
# Two events, because the loss and the cause happen at different moments:
#
#   SessionStart  — the loss happens HERE, at load. If the index is already over,
#                   every session is reading a truncated index and nobody is
#                   told. This is the only moment that fact is observable.
#   PreToolUse    — the CAUSE happens here, on the write that crosses the line.
#                   Warning before it is the last moment compaction is cheap.
#
# ADVISORY, never a block. It exits 0 on every path:
#
#   * A block would have to be right about someone's memory write, and the cost
#     of being wrong is a refused write the user cannot complete. The cost of
#     being wrong the other way is a line of text.
#   * Both hook events put stdout into the session as context, so an advisory is
#     READ rather than merely logged — which is the property the documented step
#     never had. This is not a documented rule wearing a hook's clothes.
#   * A hook that can fail the session is a hook people disable. This one cannot.
#
# Install (symlink into ~/.claude/hooks/, wire in ~/.claude/settings.json):
#   SessionStart: bash ~/.claude/hooks/memory-index-guard.sh --session-start
#   PreToolUse (matcher "Write|Edit"): bash ~/.claude/hooks/memory-index-guard.sh

set -uo pipefail        # deliberately NOT -e: see the exit-0 contract above

CHECKER="${HMAD_MEMORY_INDEX_CHECKER:-$HOME/.claude/skills/h-mad/scripts/h_mad_check_memory_index.py}"
PY="${HMAD_PYTHON:-python3.11}"

# Missing checker, missing interpreter -> say nothing and allow. A guard that
# cannot run is not a finding about the index, and printing "I could not check"
# into every single session start would train the reader to ignore this hook —
# which is the one failure that disarms the other two paths as well.
command -v "$PY" >/dev/null 2>&1 || exit 0
[ -f "$CHECKER" ] || exit 0

MODE="${1:-pretooluse}"

if [ "$MODE" != "--session-start" ]; then
  # PreToolUse: only the INDEX matters. A topic file under the same directory is
  # uncapped and writing one is never the event that drops a tail, so firing on
  # it would be noise on the commonest memory write there is.
  INPUT=$(cat 2>/dev/null || true)
  TARGET=$(printf '%s' "$INPUT" | "$PY" -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    t = d.get('tool_input') or d
    print(t.get('file_path') or t.get('path') or '')
except Exception:
    print('')
" 2>/dev/null || true)
  case "$TARGET" in
    */memory/MEMORY.md) ;;
    *) exit 0 ;;
  esac
fi

OUT=$("$PY" "$CHECKER" --show-dropped 2>&1)
RC=$?

# Read the VERDICT, never `$?` alone. Exit 1 covers both WARN and OVER and those
# are different situations: WARN is "compact now, it is still cheap", OVER is
# "content is ALREADY invisible and here is which". Exit 2 is unreadable, which
# is neither — and must not be reported as clean.
case "$OUT" in
  *"OVER "*)
    printf '[memory-index-guard] OVER CAP — the tail of your auto-memory index is ALREADY being\n'
    printf 'dropped on every load. The text below is invisible to every session reading it:\n\n'
    printf '%s\n\n' "$OUT"
    printf 'Compact MEMORY.md before writing another memory. Note that hooks are only ~7%% of\n'
    printf 'the file: at ~200 entries the link text alone exceeds the compaction target, so the\n'
    printf 'lever is moving settled entries to MEMORY-ARCHIVE.md, not shortening hooks.\n'
    ;;
  *"WARN "*)
    printf '[memory-index-guard] WARN — the auto-memory index is near its cap. The next memory\n'
    printf 'written may push an older entry off the end, where it is dropped at LOAD with no\n'
    printf 'error. Compact now, while nothing is lost yet:\n\n%s\n' "$OUT"
    ;;
  *"UNREADABLE"*)
    printf '[memory-index-guard] UNREADABLE — the index could not be read, so this is NOT a\n'
    printf 'clean result. "I could not check" and "the check said OK" lead to opposite actions:\n\n%s\n' "$OUT"
    ;;
  *"OK "*)
    : # healthy — say nothing, every session start pays for this line
    ;;
  *)
    # A verdict this script does not recognise. Surface it rather than swallow
    # it: a token that changed spelling is exactly how a guard goes quiet while
    # still appearing to run.
    printf '[memory-index-guard] unrecognised verdict from the checker (rc=%s). Not a clean\n' "$RC"
    printf 'result — the token may have been renamed:\n\n%s\n' "$OUT"
    ;;
esac

exit 0
