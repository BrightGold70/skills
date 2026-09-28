#!/bin/bash
# V-1 offline (plan v1.2): replay the HemaSuite #28 Task 7 incident against a skills tree's Codex
# gate, read-only on HemaSuite. Usage: v1-offline-replay.sh <skills-tree> <hemasuite-checkout>
# HemaSuite is only READ: `git archive` / `git show` of two pinned commits, and an APFS clone
# (`cp -c`) of its hematology-paper-writer/.venv. Every pytest run happens in the scratch copies.
# RED  = the tree before Task 7's commit plus that commit's test file (the incident's state:
#        the RED test existed, the production change did not).
# GREEN = Task 7's commit (the same test now passes): the denying control.
# Every halt is `exit 1` and means the reading is UNMEASURED, never a pass. A completed run scores
# each of the six gate lines against its post-merge pass condition (one `V-1r: CHECK` line each)
# and exits 0 only on `VERDICT=PASS`; any failed check gives `VERDICT=FAIL` and exit 2.
SK=$(cd "$1" && pwd -P) || exit 1
H=$(cd "$2" && pwd -P) || exit 1
GREEN_SHA=31bfcfe4 SUB=hematology-paper-writer  # `shared/` rides along: the sub-project conftest puts the git root on sys.path
PLAN=docs/01-plan/features/review-manifest-guideline-evidence.impl-plan.md
TEST=tests/test_certificate_lock_removed.py PROD=tools/review_round/guideline_excerpts.py
# Task 7's Test entries, in plan order: the judge's candidate set for PROD (FR-2 rule 4).
TESTS="$TEST tests/test_review_guideline_pdf_excerpts.py tests/test_review_qualitative_assets.py tests/test_review_intake_wiring.py"
RED_SHA=$(git -C "$H" rev-parse --short "$GREEN_SHA^") || exit 1
S="$(mktemp -d "${TMPDIR:-/tmp}/hmad-v1r.XXXXXX")" || exit 1

snapshot() {  # $1 = name, $2 = sha whose tree is used, $3 = sha the test file comes from
  local R="$S/$1"
  mkdir -p "$R/docs/01-plan/features" || exit 1
  git -C "$H" archive "$2" "$SUB" shared | tar -x -C "$R" || { echo "V-1r: HALT archive $2"; exit 1; }
  git -C "$H" show "$3:$SUB/$TEST" > "$R/$SUB/$TEST" || { echo "V-1r: HALT test blob $3"; exit 1; }
  git -C "$H" show "$2:$PLAN" > "$R/$PLAN" || { echo "V-1r: HALT impl-plan $2"; exit 1; }
  # State is synthesized, not copied: the root holds the step5 record, the sub-project a state
  # file with none (the OD-3 layout measured in HemaSuite, plan P9).
  printf '%s\n' '{"orchestrator_state":{"review-manifest-guideline-evidence":{"phase":"step5"}}}' > "$R/docs/.bkit-memory.json"
  mkdir -p "$R/$SUB/docs" && printf '%s\n' '{"orchestrator_state":{}}' > "$R/$SUB/docs/.bkit-memory.json" || exit 1
  cp -cR "$H/$SUB/.venv" "$R/$SUB/.venv" || { echo "V-1r: HALT venv clone (needs APFS clonefile)"; exit 1; }
  git init -q "$R" || exit 1
  # Independent control: each candidate test, run directly by the cloned venv, no gate involved.
  for t in $TESTS; do
    last=$(cd "$R/$SUB" && PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest "$t" -q --no-header -p no:cacheprovider 2>&1 | tail -1)
    echo "V-1r: direct $1 tree=$2 $t last=$last" | tee -a "$S/reading.txt"
  done
}

gate() {  # $1 = snapshot, $2 = label, $3 = payload json (cwd is the sub-project)
  local R="$S/$1" out rc
  out=$(cd "$R/$SUB" && env -u CODEX_PROJECT_DIR python3 "$SK/h-mad/hooks/h-mad-codex-tdd-gate.py" <<<"$3"); rc=$?
  echo "V-1r: gate $1 $2 rc=$rc out=${out:-<empty>}" | tee -a "$S/reading.txt"
  k="$1_$(printf '%s' "$2" | tr - _)"
  eval "RC_$k=\$rc"; eval "OUT_$k=\$out"
}
is_allow() {  # $1 = key: rc 0 and an empty or `{}` stdout
  eval "rc=\$RC_$1"; eval "out=\$OUT_$1"
  [ "$rc" = 0 ] && { [ -z "$out" ] || [ "$out" = "{}" ]; }
}
is_deny() {  # $1 = key, $2 = a word the deny must also carry (optional)
  eval "out=\$OUT_$1"
  case "$out" in *'"deny"'*) ;; *) return 1 ;; esac
  [ -z "$2" ] || case "$out" in *"$2"*) ;; *) return 1 ;; esac
}
FAILS=0
check() {  # $1 = check name, rest = the predicate
  local name=$1 v=PASS; shift
  "$@" || { v=FAIL; FAILS=$((FAILS + 1)); }
  echo "V-1r: CHECK $name $v" | tee -a "$S/reading.txt"
}

snapshot red "$RED_SHA" "$GREEN_SHA"
snapshot green "$GREEN_SHA" "$GREEN_SHA"
case "$(grep "^V-1r: direct red .* $TEST " "$S/reading.txt")" in *" failed"*) ;; *) echo "V-1r: HALT red snapshot's first candidate is not RED"; exit 1;; esac
while read -r line; do
  case "$line" in *" failed"*|*" error"*) echo "V-1r: HALT green snapshot is not GREEN: $line"; exit 1;; *" passed"*) ;; *) echo "V-1r: HALT no summary: $line"; exit 1;; esac
done < <(grep '^V-1r: direct green ' "$S/reading.txt")

for snap in red green; do
  cwd="$S/$snap/$SUB"
  gate "$snap" patch "$(jq -cn --arg c "$cwd" --arg p "*** Update File: $PROD
" '{tool_name:"apply_patch",cwd:$c,tool_input:{patch:$p}}')"
  gate "$snap" shell-pytest "$(jq -cn --arg c "$cwd" --arg x ".venv/bin/python -m pytest $TEST" '{tool_name:"shell_command",cwd:$c,tool_input:{command:$x}}')"
  gate "$snap" shell-write "$(jq -cn --arg c "$cwd" --arg x ".venv/bin/python -c \"open('x','w')\"" '{tool_name:"shell_command",cwd:$c,tool_input:{command:$x}}')"
done
check red-patch-allows is_allow red_patch
check green-patch-denies-test-passing is_deny green_patch test-passing
check red-shell-pytest-allows is_allow red_shell_pytest
check green-shell-pytest-allows is_allow green_shell_pytest
check red-shell-write-denies is_deny red_shell_write
check green-shell-write-denies is_deny green_shell_write
V=PASS; [ "$FAILS" = 0 ] || V=FAIL
echo "V-1r: DONE VERDICT=$V fails=$FAILS/6 skills=$(git -C "$SK" rev-parse --short HEAD) hemasuite_red=$RED_SHA hemasuite_green=$GREEN_SHA scratch=$S"
[ "$V" = PASS ] || exit 2
