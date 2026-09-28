#!/bin/bash
# OQ-D1, Claude half (Task 11 item 12; design D6): does Claude Code wait for the gate's own verdict
# when the resolved test takes 35 s, or does the host's hook deadline cancel the gate first?
# Usage: oqd1-host-deadline.sh <skills-tree>   (run from a cwd OUTSIDE every repository)
# Mechanism is V-0's: a real headless `claude -p` session is asked to Write a governed production
# file, with the tree's `hooks/h-mad-tdd-gate.sh` registered through `--settings`. The hook is
# reached through a wrapper that appends `DONE rc=<rc> out=<stdout>` to a log only AFTER the gate
# returns, so a host that kills the hook at its deadline leaves no DONE line. Presence of the file
# alone cannot tell a gate ALLOW from a cancelled hook, which is why the DONE line is required.
# Arms: SLOW = the test sleeps 35 s and then fails (expected: gate ALLOW, file present).
#       PASSING = the test passes at once (control: gate deny, file absent), proving the hook is live.
# Every halt is `exit 1` and means UNMEASURED, never a pass.
SK=$(cd "$1" && pwd -P) || exit 1
GATE="$SK/h-mad/hooks/h-mad-tdd-gate.sh"
[ -f "$GATE" ] || { echo "OQ-D1: HALT no gate at $GATE"; exit 1; }
command -v jq >/dev/null || { echo "OQ-D1: HALT no jq"; exit 1; }
PY=/opt/anaconda3/bin/python
S="$(mktemp -d "${TMPDIR:-/tmp}/hmad-oqd1.XXXXXX")" || exit 1
S=$(cd "$S" && pwd -P)
git -C "$S" rev-parse --show-toplevel >/dev/null 2>&1 && { echo "OQ-D1: HALT scratch is inside a git repo"; exit 1; }
claude --version > "$S/claude.version" || { echo "OQ-D1: HALT claude --version"; exit 1; }

project() {  # $1 = arm, $2 = test body
  local R="$S/$1"
  mkdir -p "$R/docs/01-plan/features" "$R/pkg" "$R/tests" || exit 1
  printf '%s\n' '{"orchestrator_state":{"oqd1":{"phase":"step5","codex_status":"unavailable"}}}' \
    > "$R/docs/.bkit-memory.json" || exit 1
  printf '%s\n' '# oqd1 impl-plan' '' '## Task 1: w' '' '**Production file**: `pkg/w.py`' \
    '**Test file**: `tests/test_w.py`' '**Task shape**: `unit`' > "$R/docs/01-plan/features/oqd1.impl-plan.md" || exit 1
  printf '%s\n' "$2" > "$R/tests/test_w.py" || exit 1
  "$PY" -m venv --system-site-packages "$R/.venv" || { echo "OQ-D1: HALT venv"; exit 1; }
  git init -q "$R" || exit 1
  {
    printf '#!/bin/bash\np=$(cat)\nstart=$(date +%%s)\n'
    printf 'out=$(printf "%%s" "$p" | CLAUDE_PROJECT_DIR=%q bash %q 2>>%q); rc=$?\n' "$R" "$GATE" "$S/$1.gate.err"
    printf 'printf "DONE rc=%%s s=%%s out=%%s\\n" "$rc" "$(( $(date +%%s) - start ))" "$out" >> %q\n' "$S/$1.log"
    printf 'printf "%%s" "$out"\nexit $rc\n'
  } > "$S/hook.$1.sh" || exit 1
  chmod +x "$S/hook.$1.sh" || exit 1
  jq -n --arg c "$S/hook.$1.sh" \
    '{hooks:{PreToolUse:[{matcher:"Write|Edit",hooks:[{type:"command",command:$c}]}]}}' > "$S/settings.$1.json" || exit 1
}

attempt() {  # $1 = arm
  local R="$S/$1" t0 t1
  t0=$(date +%s)
  (cd "$R" && claude -p "Use the Write tool to create pkg/w.py containing exactly: X = 1" \
      --settings "$S/settings.$1.json" --setting-sources project --strict-mcp-config \
      --tools Write --permission-mode acceptEdits --model haiku \
      --no-session-persistence --output-format json > "$S/$1.out.json" 2> "$S/$1.err")
  t1=$(date +%s)
  done_line=$(grep '^DONE ' "$S/$1.log" 2>/dev/null | tail -1)
  present=absent; [ -e "$R/pkg/w.py" ] && present=present
  echo "OQ-D1: arm=$1 session_s=$((t1 - t0)) file=$present gate=${done_line:-<no DONE line>}"
  eval "FILE_$1=\$present"; eval "DONE_$1=\$done_line"
}

project SLOW 'import time
def test_w():
    time.sleep(35)
    assert False'
project PASSING 'def test_w():
    assert True'
attempt PASSING
attempt SLOW

case "$DONE_PASSING" in *'"deny"'*) ;; *) echo "OQ-D1: HALT control did not reach a gate deny"; exit 1;; esac
[ "$FILE_PASSING" = absent ] || { echo "OQ-D1: HALT control file present despite deny"; exit 1; }
V=FAIL
case "$DONE_SLOW" in
  "DONE rc=0 s="*" out=") [ "$FILE_SLOW" = present ] && V=PASS ;;
esac
echo "OQ-D1: DONE VERDICT=$V skills=$(git -C "$SK" rev-parse --short HEAD) claude=$(head -1 "$S/claude.version") scratch=$S"
[ "$V" = PASS ] || exit 2
