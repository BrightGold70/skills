#!/bin/bash
# Claude Code PreToolUse gate for production Python writes during H-MAD step 5.
set -euo pipefail
readonly REFUSAL_FORM=b
DECIDED=""
TRC=0 SRC=0 JRC=0
JUDGE=""

_allow() { DECIDED=allow; exit 0; }
_json_str() {
  local value=${1//\\/\\\\}
  value=${value//\"/\\\"}
  printf '%s' "$value" | LC_ALL=C /usr/bin/tr '[:cntrl:]' ' '
}
_refuse() {
  MSG="[H-MAD-TDD-GATE] BLOCK kind=$1: $2"
  printf '%s\n' "$MSG" >&2
  if [ "$REFUSAL_FORM" = b ]; then
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$(_json_str "$MSG")" || exit 2  # M:H5B
    DECIDED=refused
    exit 0
  fi
  DECIDED=refused
  exit 2  # M:H5A
}
_on_exit() {
  local rc=$?
  trap - EXIT
  set +euo pipefail
  case "$DECIDED" in
    allow) exit 0 ;;
    refused) exit "$rc" ;;
  esac
  _refuse judge-error "gate exited rc=$rc before deciding"  # M:T2
  exit 2
}
_lexists() { [ -e "$1" ] || [ -L "$1" ]; }  # M:H7
_absent_at() {
  _lexists "$1/docs/.bkit-memory.json" && return 1
  [ -x "$1" ] || return 1
  _lexists "$1/docs" || return 0
  [ -x "$1/docs" ] && return 0  # M:H10
  [ -e "$1/docs" ] && [ ! -d "$1/docs" ] && return 0
  return 1
}
_chain_may_hold_state() {
  local root=$1 target=$2 d
  if [ -n "$root" ]; then _absent_at "$root" || return 0; fi
  [ -n "$target" ] || return 1
  case "$target" in /*) ;; *) return 0 ;; esac
  case "/$target/" in */./*|*/../*) return 0 ;; esac
  d=$(dirname "$target"); while [ ! -e "$d" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; d=$(cd "$d" 2>/dev/null && pwd -P) || return 0  # M:H8
  if [ -n "$root" ]; then
    case "$d/" in "$root"/*) ;; *) return 1 ;; esac
  fi
  while :; do
    _absent_at "$d" || return 0
    if [ -n "$root" ] && [ "$d" = "$root" ]; then return 1; fi
    [ "$d" = / ] && return 1
    d=$(dirname "$d")
  done
}
_dir_match() { case "$1" in */tests/*|*/fixtures/*) return 0 ;; esac; return 1; }  # M:H15
_pct_decode() { [ "$1" = % ] && return 0; printf '%b' "${1//%/\\x}"; }
_pct_capture() {
  local _pct_v
  _pct_v=$(_pct_decode "$2"; printf '\001')
  printf -v "$1" '%s' "${_pct_v%$'\001'}"
}
_read_canon() {
  local line value index=0 count=0 spelled
  local encoded_re='^([A-Za-z0-9/._-]|%[0-9A-Fa-f]{2})*$'
  CANON_ROOT= CANON_TARGET= CANON_PREFIX= CANON_UNRESOLVABLE=
  CANON_ARM= CANON_COMPONENT= CANON_NAMES=()
  while IFS= read -r line; do
    case "$index" in
      0) [ "$line" = 'CANON 1' ] || _refuse judge-error "invalid CANON header" ;;
      1) case "$line" in 'root '*) value=${line#root } ;; *) _refuse judge-error "invalid CANON root" ;; esac
         [[ $value =~ $encoded_re ]] || _refuse judge-error "invalid CANON root encoding"
         _pct_capture CANON_ROOT "$value" ;;
      2) case "$line" in 'target '*) value=${line#target } ;; *) _refuse judge-error "invalid CANON target" ;; esac
         [[ $value =~ $encoded_re ]] || _refuse judge-error "invalid CANON target encoding"
         _pct_capture CANON_TARGET "$value" ;;
      3) case "$line" in 'prefix '*) value=${line#prefix } ;; *) _refuse judge-error "invalid CANON prefix" ;; esac
         [[ $value =~ $encoded_re ]] || _refuse judge-error "invalid CANON prefix encoding"
         _pct_capture CANON_PREFIX "$value" ;;
      4) case "$line" in 'unresolvable yes'|'unresolvable no') CANON_UNRESOLVABLE=${line#unresolvable } ;;
           *) _refuse judge-error "invalid CANON unresolvable" ;; esac ;;
      5) case "$line" in 'arm 0'|'arm 1'|'arm 2') CANON_ARM=${line#arm } ;;
           *) _refuse judge-error "invalid CANON arm" ;; esac ;;
      6) case "$line" in 'component '*) value=${line#component } ;; *) _refuse judge-error "invalid CANON component" ;; esac
         [[ $value =~ $encoded_re ]] || _refuse judge-error "invalid CANON component encoding"
         _pct_capture CANON_COMPONENT "$value" ;;
      7) case "$line" in 'names '*) value=${line#names } ;; *) _refuse judge-error "invalid CANON names" ;; esac
         [[ $value =~ ^(0|[1-9][0-9]*)$ ]] || _refuse judge-error "invalid CANON names count"
         count=$value ;;
      *) case "$line" in 'name '*) value=${line#name } ;; *) _refuse judge-error "invalid CANON name" ;; esac
         [[ $value =~ $encoded_re ]] || _refuse judge-error "invalid CANON name encoding"
         [ "${#CANON_NAMES[@]}" -lt "$count" ] || _refuse judge-error "CANON name count mismatch"
         _pct_capture CANON_NAME "$value"
         CANON_NAMES[${#CANON_NAMES[@]}]=$CANON_NAME ;;
    esac
    index=$((index + 1))
  done <<< "$CANON_RECORD"
  [ "$index" -ge 8 ] && [ "${#CANON_NAMES[@]}" -eq "$count" ] || _refuse judge-error "CANON field count mismatch"
  [ -n "$CANON_ROOT" ] && [ -n "$CANON_PREFIX" ] || _refuse judge-error "CANON root or prefix missing"
  if [ "$CANON_UNRESOLVABLE" = yes ]; then
    [ "$CANON_ARM" != 0 ] && [ -z "$CANON_TARGET" ] && [ "$count" -eq 0 ] &&
      [ -n "$CANON_COMPONENT" ] || _refuse judge-error "invalid unresolvable CANON record"
  else
    [ "$CANON_ARM" = 0 ] && [ -z "$CANON_COMPONENT" ] || _refuse judge-error "invalid resolvable CANON record"
    if [ -n "$RAW_TARGET" ]; then
      case "$RAW_TARGET" in /*) spelled=$RAW_TARGET ;; *) spelled=${CLAUDE_PROJECT_DIR:-.}/$RAW_TARGET ;; esac
      if [ -d "$spelled" ]; then
        [ "$count" -eq 0 ] && [ -n "$CANON_TARGET" ] || _refuse judge-error "directory CANON name mismatch"
      else
        [ "$count" -gt 0 ] && [ -n "$CANON_TARGET" ] || _refuse judge-error "file CANON name mismatch"
      fi
    fi
  fi
}
_fold_py() {
  case "$2" in
    *.py|*.pY|*.Py|*.PY) printf -v "$1" '%s' "${2%.*}.py" ;;
    *) printf -v "$1" '%s' "$2" ;;
  esac
}
_find_judge() {
  [ -n "$JUDGE" ] && return 0
  JUDGE=$(python3 -c 'import os,sys;print(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[1]))),"scripts","h_mad_tdd_judge.py"))' "${BASH_SOURCE[0]}")  # M:W6
}
_read_state() {
  [ -n "$ROOT_ABS" ] || _refuse judge-error "project root (CLAUDE_PROJECT_DIR) cannot be entered"
  SOUT=$(python3 "$JUDGE" state --root "$ROOT_ABS" "$@" 2>/dev/null; printf 'rc=%s' "$?")  # M:W5B
  SRC=${SOUT##*rc=}; SOUT=${SOUT%rc=*}; SOUT=${SOUT%$'\n'}  # M:H17
  case "$SOUT" in *$'\n'*|"") _refuse judge-error "state verb printed zero or several lines" ;; esac
  [ "$SRC" = 0 ] || _refuse judge-error "state verb exited rc=$SRC"
  if [ "$SOUT" = 'TDD-STATE: none' ]; then _allow; fi
  if [[ $SOUT =~ $STATE_UNREADABLE_RE ]]; then
    local file
    file=$(_pct_decode "${BASH_REMATCH[1]}")
    _refuse judge-error "H-MAD state is unreadable ($file: ${BASH_REMATCH[2]})"
  fi
  [[ $SOUT =~ $STATE_ACTIVE_RE ]] || _refuse judge-error "state verb printed no well-formed state line"
  ESCAPE=${BASH_REMATCH[1]}
  BLOCKER=${BASH_REMATCH[2]}
  RECORDS=${BASH_REMATCH[3]}
  FALLBACK=${BASH_REMATCH[4]}  # M:F3
  FALLBACK_POS=${BASH_REMATCH[6]:-0}
  local word count=0 record="" frecord=""
  set -f
  for word in $SOUT; do
    case "$word" in record=*)
      count=$((count + 1))
      if [ "$count" = "$BLOCKER" ]; then record=${word#record=}; fi
      if [ "$count" = "$FALLBACK_POS" ]; then frecord=${word#record=}; fi
      ;;
    esac
  done
  set +f
  [ "$count" = "$RECORDS" ] || _refuse judge-error "state record count mismatch"
  if [ "$ESCAPE" = yes ]; then
    [ "$BLOCKER" = 0 ] || _refuse judge-error "state blocker mismatch"
  else
    [ "$BLOCKER" != 0 ] || _refuse judge-error "state blocker mismatch"
  fi
  [ "$BLOCKER" -le "$RECORDS" ] || _refuse judge-error "state blocker out of range"
  [ "$FALLBACK_POS" -le "$RECORDS" ] || _refuse judge-error "state fallback position out of range"  # M:F4
  BLOCKER_RECORD=$record
  FALLBACK_RECORD=$frecord
}

trap _on_exit EXIT  # M:T1

READER=$(cat <<'PY'
import json, os, select, sys, time
if os.isatty(0):
    data = b''
else:
    data = b''
    end = time.monotonic() + 2.0
    while True:
        remaining = end - time.monotonic()
        if remaining <= 0:
            break
        ready, _, _ = select.select([0], [], [], remaining)
        if not ready:
            break
        chunk = os.read(0, 65536)
        if not chunk:
            break
        data += chunk
if not data:
    sys.exit(0)
try:
    payload = json.loads(data.decode('utf-8'))
    tool_input = payload.get('tool_input') if isinstance(payload, dict) else None
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    if isinstance(payload, dict):
        for value in (tool_input.get('file_path'), payload.get('file_path'), payload.get('path')):  # M:H1
            if isinstance(value, str) and value:
                if any(ord(c) < 32 or ord(c) == 127 for c in value):
                    sys.exit(3)
                print(value)
                sys.exit(0)
except (UnicodeError, ValueError, TypeError):
    pass
sys.exit(4)  # M:H12
PY
)
TP=$(python3 -c "$READER") || TRC=$?
if [ "$TRC" = 0 ] && [ -n "$TP" ]; then
  TARGET_PATH=$TP  # M:H2
elif [ "$TRC" = 0 ]; then
  TARGET_PATH=${1:-}
else
  TARGET_PATH=""
fi

RAW_TARGET=$TARGET_PATH
CANON_RECORD=$(python3 -c 'import os,sys;sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[1]))),"scripts"));from h_mad_target_identity import canonicalise,emit_canon;emit_canon(canonicalise(sys.argv[2],sys.argv[3]))' "${BASH_SOURCE[0]}" "${CLAUDE_PROJECT_DIR:-.}" "$TARGET_PATH")  # M:H11
_read_canon
ROOT_ABS=$CANON_ROOT
TARGET_PATH=$CANON_TARGET
R=${ROOT_ABS%/}
IN_ROOT=no
if [ -n "$ROOT_ABS" ]; then case "$TARGET_PATH" in "$R"/*) IN_ROOT=yes ;; esac; fi  # M:H18

STATE_UNREADABLE_RE='^TDD-STATE: unreadable file=([^ ]+) error=([A-Za-z_-][A-Za-z0-9_-]*)$'
STATE_ACTIVE_RE='^TDD-STATE: active codex-escape=(yes|no) blocker=(0|[1-9][0-9]*) records=([1-9][0-9]*) fallback=(none|(grok|invalid):([1-9][0-9]*))( record=[^ ,]+,[^ ,]+,[^ ,]+,(absent|null|grok|claude|invalid:[^ ,]+))+$'
JUDGE_ALLOW_RE='^TDD-JUDGE: ALLOW kind=red-measured source=(impl-plan|name-map) test=[^ ]+$'
JUDGE_DENY_RE='^TDD-JUDGE: DENY kind=(no-test-resolved|test-missing|venv-escapes-root|pytest-missing|pytest-error|no-tests-ran|no-summary|test-passing|timeout|judge-timeout|judge-error) reason=(.+)$'

if [ -z "$TARGET_PATH" ]; then
  if [ -z "$RAW_TARGET" ]; then
    _find_judge
    _read_state
    _refuse judge-error "could not identify the write target"  # M:H13
  fi
fi

if [ "$CANON_UNRESOLVABLE" = yes ]; then
  if [ "$CANON_ARM" = 2 ] && [ "$CANON_COMPONENT" = "$CANON_ROOT" ] &&
     { [ ! -d "$CANON_ROOT" ] || [ ! -x "$CANON_ROOT" ]; }; then
    _refuse judge-error "project root (CLAUDE_PROJECT_DIR) cannot be entered"
  fi
  _chain_may_hold_state "$ROOT_ABS" "$CANON_PREFIX" || _allow
  _find_judge
  _read_state
  _refuse judge-error "unresolvable arm=$CANON_ARM component=$CANON_COMPONENT"
fi

_chain_may_hold_state "$ROOT_ABS" "$TARGET_PATH" || _allow

ALL_TEST_NAMES=yes
for NAME in "${CANON_NAMES[@]}"; do
  _fold_py FOLDED_NAME "$NAME"
  case "$FOLDED_NAME" in  # M:H6
    test_*.py|*_test.py|conftest*.py) ;;
    *) ALL_TEST_NAMES=no ;;
  esac
done
[ "$ALL_TEST_NAMES" = yes ] && _allow
if [ "$IN_ROOT" = yes ]; then
  DIR_SUBJECT="/${TARGET_PATH#"$R"/}"; if _dir_match "$DIR_SUBJECT"; then _allow; fi  # M:H19
elif _dir_match "$TARGET_PATH" && _dir_match "$RAW_TARGET"; then  # M:H20
  _allow
fi
ALL_SUFFIX_NAMES=yes
for NAME in "${CANON_NAMES[@]}"; do
  _fold_py FOLDED_NAME "$NAME"
  case "$FOLDED_NAME" in
    *.md|*.yaml|*.yml|*.json|*.toml|*.txt|*.rst|*.cfg|*.ini) ;;
    *.sh|*.bash|Makefile|Dockerfile|*.dockerignore|*.gitignore) ;;
    *) ALL_SUFFIX_NAMES=no ;;
  esac
done
[ "$ALL_SUFFIX_NAMES" = yes ] && _allow

ALL_NON_PY=yes
PRODUCTION_TARGET=
for NAME in "${CANON_NAMES[@]}"; do
  _fold_py FOLDED_NAME "$NAME"
  if [[ "$FOLDED_NAME" != *.py ]]; then continue; fi
  ALL_NON_PY=no
  case "$FOLDED_NAME" in
    test_*.py|*_test.py|conftest*.py) continue ;;
  esac
  [ -n "$PRODUCTION_TARGET" ] || PRODUCTION_TARGET=${CANON_TARGET%/*}/$NAME
done
[ "$ALL_NON_PY" = yes ] && _allow
TARGET_PATH=$PRODUCTION_TARGET

_find_judge
_read_state --target "$TARGET_PATH"  # M:H3
if [ -z "${HMAD_CODEX_UNAVAILABLE:-}" ] && [ "$ESCAPE" = no ] && command -v codex >/dev/null 2>&1; then
  BLOCKER_KEY=${BLOCKER_RECORD%%,*}
  BLOCKER_FILE=${BLOCKER_RECORD#*,}; BLOCKER_FILE=${BLOCKER_FILE#*,}; BLOCKER_FILE=${BLOCKER_FILE%%,*}
  BLOCKER_KEY=$(_pct_decode "$BLOCKER_KEY")
  BLOCKER_FILE=$(_pct_decode "$BLOCKER_FILE")
  _refuse codex-authorship "Phase 5 implementation must be authored by Codex, not Claude.
Dispatch this module to Codex: hmad-dispatch exec codex <promptfile>  (or: send codex).
Codex looks available (codex on PATH). If it is out of quota, record it —
  python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py --feature $BLOCKER_KEY --set codex_status=exhausted \"$BLOCKER_FILE\"
then Claude may author the fallback (still test-first). Or export HMAD_CODEX_UNAVAILABLE=1 for a one-off."
fi

# fallback_agent (FR-2): codex-authorship has already refused every case where codex is available.
if [ "$FALLBACK" != none ]; then
  FB_KEY=$(_pct_decode "${FALLBACK_RECORD%%,*}")
  FB_FILE=${FALLBACK_RECORD#*,}; FB_FILE=${FB_FILE#*,}; FB_FILE=$(_pct_decode "${FB_FILE%%,*}")
  FB_TAG=${FALLBACK_RECORD##*,}
  case "$FALLBACK" in
    grok:*)    [ "$FB_TAG" = grok ] ;;
    invalid:*) [ "${FB_TAG#invalid:}" != "$FB_TAG" ] ;;
  esac || _refuse judge-error "state fallback=$FALLBACK disagrees with its record's tag $FB_TAG"  # M:F1
  case "$FALLBACK" in
    grok:*)
      _refuse fallback-grok "fallback_agent=grok — Phase 5 is authored by grok while codex is out, not by Claude.
Dispatch this module to grok: hmad-dispatch exec grok <promptfile>  (stage it with h_mad_assemble_tdd.py --agent grok).
HMAD_CODEX_UNAVAILABLE does not override fallback_agent=grok. For a one-off Claude escape, record it —
  python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py --feature $FB_KEY --set fallback_agent=claude \"$FB_FILE\"" ;;
    invalid:*)
      FB_VALUE=$(_pct_decode "${FB_TAG#invalid:}")
      _refuse fallback-invalid "fallback_agent=$FB_VALUE is not valid (valid: grok|claude) — refusing the write, fail-closed.
  Fix it: python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py --feature $FB_KEY --set fallback_agent=grok|claude|null \"$FB_FILE\"" ;;
  esac
fi

JOUT=$(python3 "$JUDGE" judge --root "$ROOT_ABS" --target "$TARGET_PATH" 2>/dev/null; printf 'rc=%s' "$?")  # M:W2
JRC=${JOUT##*rc=}; JOUT=${JOUT%rc=*}; JOUT=${JOUT%$'\n'}  # M:H16
case "$JOUT" in *$'\n'*|"") _refuse judge-error "judge verb printed zero or several lines" ;; esac
if [ "$JRC" = 0 ] && [[ $JOUT =~ $JUDGE_ALLOW_RE ]]; then _allow; fi  # M:H4
if [[ $JOUT =~ $JUDGE_DENY_RE ]]; then _refuse "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"; fi
_refuse judge-error "judge verb rc=$JRC printed no well-formed verdict line"
_refuse judge-error "gate fell through without a decision"
