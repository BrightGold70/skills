#!/bin/bash
# V-0 (spec v1.1 FR-0; plan v1.2): which PreToolUse refusal forms does Claude Code honour for Write?
# Arms: E1 = exit 1, E2 = exit 2 (form a), EJ = rc 0 + JSON permissionDecision deny (form b),
# E0 = exit 0 (negative control). Each arm has its own nonce, carried in its sentinel file name.
# Proof that an arm's session reached the hook's refusal branch is a log line carrying THAT
# arm's nonce, written only for tool_name=Write on that arm's sentinel. Any other invocation
# logs nothing. Presence is scored at every path the arm's session HIT lines logged, never at an
# assumed path. Run from a cwd OUTSIDE every repository. Every halt is `exit 1` and means the
# reading is INCONCLUSIVE, never a pass. Arm EJ alone may be UNMEASURED without a halt: it then
# reads FORM_B=INCONCLUSIVE, and READING is still scored over E1/E2/E0 (spec v1.1 FR-0).
S="$(mktemp -d "${TMPDIR:-/tmp}/hmad-v0.XXXXXX")" || exit 1
git -C "$S" rev-parse --show-toplevel >/dev/null 2>&1 && { echo "V-0: HALT scratch is inside a git repo"; exit 1; }
command -v jq >/dev/null || { echo "V-0: HALT no jq"; exit 1; }
claude --version > "$S/claude.version" || { echo "V-0: HALT claude --version"; exit 1; }

nonce() { od -An -N8 -tx1 /dev/urandom | tr -d ' \n'; }

unmeasured() {  # $1 = arm, $2 = why. EJ is recorded and the run goes on; any other arm halts.
  echo "V-0: $1 UNMEASURED $2"
  [ "$1" = EJ ] || exit 1
  EJ_UNMEASURED=1
}

mkhook() {  # $1 = arm, $2 = sentinel basename, $3 = refusal: 1 | 2 | json | 0 | cap
  {
    printf '#!/bin/bash\np=$(cat)\n'
    printf 't=$(printf "%%s" "$p" | jq -r ".tool_name // empty")\n'
    printf 'f=$(printf "%%s" "$p" | jq -r ".tool_input.file_path // empty")\n'
    printf '[ "$t" = Write ] || exit 0\n'
    printf 'case "$f" in */%s|%s) ;; *) exit 0;; esac\n' "$2" "$2"
    printf 'printf "HIT %%s %%s\\n" %q "$f" >> %q\n' "${2#SENTINEL_}" "$S/$1.log"
    case "$3" in
      cap)  printf 'printf "%%s" "$p" > %q\nexit 0\n' "$S/payload.json" ;;
      0)    printf 'exit 0\n' ;;
      json) printf 'printf "%%s\\n" %q\nexit 0\n' \
              '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"V-0 arm EJ refuses"}}' ;;
      *)    printf 'echo "V-0 arm %s refuses" >&2\nexit %s\n' "$1" "$3" ;;
    esac
  } > "$S/hook.$1.sh" || exit 1
  chmod +x "$S/hook.$1.sh" || exit 1
  jq -n --arg c "$S/hook.$1.sh" \
    '{hooks:{PreToolUse:[{matcher:"Write",hooks:[{type:"command",command:$c}]}]}}' \
    > "$S/settings.$1.json" || exit 1
}

attempt() {  # $1 = arm, $2 = sentinel basename; a real session is asked to Write the sentinel
  mkdir "$S/$1" || exit 1
  (cd "$S/$1" && claude -p "Use the Write tool to create $2 in the current directory containing exactly: X = 1" \
      --settings "$S/settings.$1.json" --setting-sources project --strict-mcp-config \
      --tools Write --permission-mode acceptEdits \
      --no-session-persistence --output-format json > "$S/$1.out.json" 2> "$S/$1.err")
  grep -q "^HIT ${2#SENTINEL_} " "$S/$1.log" 2>/dev/null \
    || unmeasured "$1" "no_hit_for_nonce ${2#SENTINEL_}"
}

N_cap="SENTINEL_cap$(nonce).py"
mkhook cap "$N_cap" cap; attempt cap "$N_cap"
F=$(jq -r '.tool_input.file_path // empty' "$S/payload.json") || exit 1
case "$F" in */"$N_cap") ;; *) echo "V-0: HALT captured payload file_path is not the cap sentinel"; exit 1;; esac

for arm in E1:1 E2:2 EJ:json E0:0; do
  a=${arm%%:*} want=${arm##*:}
  n="SENTINEL_${a}$(nonce).py"
  eval "N_$a=\$n"
  mkhook "$a" "$n" "$want"
  # Replay the captured payload, re-pointed at this arm's sentinel (jq, not hand-written JSON).
  jq --arg f "$S/$a/$n" '.tool_input.file_path = $f' "$S/payload.json" > "$S/payload.$a.json" || exit 1
  out=$("$S/hook.$a.sh" < "$S/payload.$a.json" 2>/dev/null); rc=$?
  dec=$(printf '%s' "$out" | jq -r '.hookSpecificOutput.permissionDecision // empty' 2>/dev/null)
  echo "V-0: replay $a rc=$rc decision=${dec:-none}" | tee -a "$S/replay.txt"
  case "$want" in
    json) ok=$([ "$rc" = 0 ] && [ "$dec" = deny ] && echo y) ;;
    *)    ok=$([ "$rc" = "$want" ] && [ -z "$dec" ] && echo y) ;;
  esac
  [ "$ok" = y ] || { unmeasured "$a" "replay rc=$rc want=$want decision=${dec:-none}"; continue; }
  grep -q "^HIT ${n#SENTINEL_} " "$S/$a.log" || { unmeasured "$a" replay_no_hit; continue; }
  mv "$S/$a.log" "$S/$a.replay.log" || exit 1   # the replay must not count as the session's hit
  attempt "$a" "$n"
done

p() {  # present if ANY path this arm's session logged exists; a relative one is the session cwd's
  local n f r=absent
  eval "n=\$N_$1"
  while read -r _ _ f; do
    case "$f" in /*) ;; *) f="$S/$1/$f" ;; esac
    [ -e "$f" ] && r=present
  done < <(grep "^HIT ${n#SENTINEL_} " "$S/$1.log")
  echo "$r"
}
E1=$(p E1) E2=$(p E2) E0=$(p E0)
if [ -n "$EJ_UNMEASURED" ]; then EJ=UNMEASURED; else EJ=$(p EJ); fi
case "$E1/$E2/$E0" in
  absent/absent/present)  R=E1_BLOCKS ;;
  present/absent/present) R=E1_DOES_NOT_BLOCK ;;
  *)                      R=INCONCLUSIVE ;;
esac
form() {
  [ "$E0" = present ] || { echo INCONCLUSIVE; return; }
  case "$1" in absent) echo BLOCKS ;; present) echo DOES_NOT_BLOCK ;; *) echo INCONCLUSIVE ;; esac
}
FA=$(form "$E2") FB=$(form "$EJ")
# Spec v1.1 AC-6.5 / AC-6.6: on either conclusive branch the form is (b) when FORM_B=BLOCKS, else (a)
# when FORM_A=BLOCKS. `exit 1` is never a chosen form.
case "$R/$FA/$FB" in
  E1_DOES_NOT_BLOCK/*/BLOCKS|E1_BLOCKS/*/BLOCKS)   C=b ;;
  E1_DOES_NOT_BLOCK/BLOCKS/*|E1_BLOCKS/BLOCKS/*)   C=a ;;
  *)                                               C=none ;;
esac
echo "V-0: READING=$R FORM_A=$FA FORM_B=$FB CHOSEN=$C E1=$E1 E2=$E2 EJ=$EJ E0=$E0 claude=$(head -1 "$S/claude.version") scratch=$S"
