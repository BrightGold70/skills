#!/usr/bin/env bash
# hmad-dispatch — substrate-agnostic agent transport for the H-MAD skill.
# Verbs: env | send | read | wait | alive | clear | notify | task-create | dispatch | await | gate-create | gate-resolve
# Substrate: cmux (manaflow-ai/cmux) or orca (stablyai/orca). Auto-detected.
set -euo pipefail

_detect_substrate() {
  # Precedence: HMAD_SUBSTRATE override > session marker > binary presence > default cmux.
  if [ "${HMAD_SUBSTRATE:-}" = "cmux" ] || [ "${HMAD_SUBSTRATE:-}" = "orca" ]; then
    printf '%s\n' "$HMAD_SUBSTRATE"; return 0
  fi
  # Session marker (best-effort; names to confirm — see agent-substrate.md).
  if [ -n "${ORCA_TERMINAL_ID:-}${ORCA_SESSION:-}" ]; then printf 'orca\n'; return 0; fi
  if [ -n "${CMUX:-}${CMUX_PANE:-}" ]; then printf 'cmux\n'; return 0; fi
  # Binary presence.
  local has_cmux=0 has_orca=0
  command -v cmux >/dev/null 2>&1 && has_cmux=1
  command -v orca >/dev/null 2>&1 && has_orca=1
  if [ "$has_orca" = 1 ] && [ "$has_cmux" = 0 ]; then printf 'orca\n'; return 0; fi
  if [ "$has_cmux" = 1 ]; then printf 'cmux\n'; return 0; fi   # both present => default cmux
  if [ "$has_orca" = 1 ]; then printf 'orca\n'; return 0; fi
  return 1
}

_need() {  # $1 value, $2 name — non-zero + message if empty
  [ -n "${1:-}" ] || { echo "hmad-dispatch: missing required argument: $2" >&2; return 2; }
}

_require_orca() {  # $1 verb-name — non-zero + message unless substrate=orca
  local sub; sub="$(_detect_substrate)" || return 1
  [ "$sub" = "orca" ] || { echo "hmad-dispatch: '$1' requires orchestration mode (substrate=orca); current substrate=$sub" >&2; return 2; }
}

_coordinator() {  # echo the coordinator handle or fail with a message
  if [ -n "${HMAD_ORCA_COORDINATOR_TERMINAL:-}" ]; then printf '%s\n' "$HMAD_ORCA_COORDINATOR_TERMINAL"
  else echo "hmad-dispatch: set HMAD_ORCA_COORDINATOR_TERMINAL (the H-MAD coordinator's Orca terminal handle)" >&2; return 1; fi
}

_orchestration_active() {  # 0 iff substrate=orca AND coordinator pinned
  local sub; sub="$(_detect_substrate)" 2>/dev/null || return 1
  [ "$sub" = "orca" ] && [ -n "${HMAD_ORCA_COORDINATOR_TERMINAL:-}" ]
}

_resolve_target() {
  # $1 = agent (codex|agy). Echo concrete surface/terminal for the active substrate.
  local agent="$1" sub
  sub="$(_detect_substrate)" || return 1
  case "$sub:$agent" in
    cmux:codex) printf '%s\n' "${HMAD_CMUX_CODEX_SURFACE:-surface:5}"; return 0 ;;
    cmux:agy)   printf '%s\n' "${HMAD_CMUX_AGY_SURFACE:-surface:2}";   return 0 ;;
    orca:codex)
      if [ -n "${HMAD_ORCA_CODEX_TERMINAL:-}" ]; then printf '%s\n' "$HMAD_ORCA_CODEX_TERMINAL"; return 0; fi
      _orca_find codex; return $? ;;
    orca:agy)
      if [ -n "${HMAD_ORCA_AGY_TERMINAL:-}" ]; then printf '%s\n' "$HMAD_ORCA_AGY_TERMINAL"; return 0; fi
      _orca_find agy; return $? ;;
    *) echo "hmad-dispatch: unknown agent '$agent'" >&2; return 2 ;;
  esac
}

_orca_find() {
  # Match a terminal whose preview/title contains the agent token.
  local token="$1" ids
  ids="$(orca terminal list --json | jq -r \
    --arg t "$token" '.result.terminals[] | select(((.preview//"") + " " + (.title//"")) | test($t)) | .handle')"
  local n; n="$(printf '%s' "$ids" | grep -c . || true)"
  if [ "$n" -eq 1 ]; then printf '%s\n' "$ids"; return 0; fi
  echo "hmad-dispatch: orca terminal for '$token' resolved to $n candidates; pin HMAD_ORCA_$(printf '%s' "$token" | tr '[:lower:]' '[:upper:]')_TERMINAL" >&2
  return 1
}

_cmd_env() {
  local sub
  if ! sub="$(_detect_substrate)"; then
    echo "hmad-dispatch: no substrate detected (install cmux or orca, or set HMAD_SUBSTRATE)" >&2
    return 1
  fi
  echo "substrate: $sub"
  local a t
  for a in codex agy; do
    if t="$(_resolve_target "$a" 2>/dev/null)"; then echo "$a -> $t"; else echo "$a -> UNRESOLVED"; fi
  done
  if _orchestration_active; then echo "orchestration: on"; else echo "orchestration: off"; fi
  return 0
}

_cmd_task_create() {  # $1 label, $2 specfile
  _require_orca task-create || return $?
  _need "${1:-}" label || return $?; _need "${2:-}" specfile || return $?
  [ -f "$2" ] || { echo "hmad-dispatch: spec file not found: $2" >&2; return 2; }
  local coord spec
  coord="$(_coordinator)" || return 1
  spec="[H-MAD] worker_done coordinator handle (use as --to): ${coord}

$(cat "$2")"
  orca orchestration task-create --spec "$spec" --task-title "$1" --json \
    | jq -r '.result.taskId // .taskId // .result.id // .id // empty'
}

_cmd_dispatch() {  # $1 agent, $2 task_id
  _require_orca dispatch || return $?
  _need "${1:-}" agent || return $?; _need "${2:-}" task_id || return $?
  local target; target="$(_resolve_target "$1")" || return 1
  orca orchestration dispatch --task "$2" --to "$target" --return-preamble --json
}

_cmd_await() {  # $1 task_id, [--timeout <s>]
  _require_orca await || return $?
  _need "${1:-}" task_id || return $?
  local task="$1"; shift
  local timeout=600
  while [ $# -gt 0 ]; do case "$1" in --timeout) timeout="$2"; shift 2 ;; *) shift ;; esac; done
  local coord; coord="$(_coordinator)" || return 1
  orca orchestration check --terminal "$coord" --wait --types worker_done --timeout-ms "$(( timeout * 1000 ))" --json \
    | jq -c --arg t "$task" '(.result.messages // .messages // []) | map(select((.taskId // .payload.taskId // .["task-id"]) == $t)) | .[0] // empty'
}

_cmd_gate_create() {  # $1 task_id, $2 question, [$3 options-json]
  _require_orca gate-create || return $?
  _need "${1:-}" task_id || return $?; _need "${2:-}" question || return $?
  if [ -n "${3:-}" ]; then
    orca orchestration gate-create --task "$1" --question "$2" --options "$3" --json | jq -r '.result.gateId // .gateId // .result.id // .id // empty'
  else
    orca orchestration gate-create --task "$1" --question "$2" --json | jq -r '.result.gateId // .gateId // .result.id // .id // empty'
  fi
}

_cmd_gate_resolve() {  # $1 gate_id, $2 resolution
  _require_orca gate-resolve || return $?
  _need "${1:-}" gate_id || return $?; _need "${2:-}" resolution || return $?
  orca orchestration gate-resolve --id "$1" --resolution "$2" --json
}

_send_text() {
  local agent="$1" text="$2" sub target
  sub="$(_detect_substrate)" || return 1
  target="$(_resolve_target "$agent")" || return 1
  case "$sub" in
    cmux) cmux send --surface "$target" "$text"; cmux send-key --surface "$target" Enter ;;
    orca) orca terminal send --terminal "$target" --text "$text" --enter ;;
  esac
}

_cmd_send()  { _send_text "$1" "$(cat "$2")"; }   # $1 agent, $2 promptfile — file CONTENTS, not path
_cmd_clear() { _send_text "$1" "/clear"; }

_cmd_read() {
  local agent="$1"; shift
  local lines=50
  while [ $# -gt 0 ]; do case "$1" in --lines) lines="$2"; shift 2 ;; *) shift ;; esac; done
  local sub target; sub="$(_detect_substrate)" || return 1
  target="$(_resolve_target "$agent")" || return 1
  case "$sub" in
    cmux) cmux read-screen --surface "$target" --lines "$lines" ;;
    orca) orca terminal read --terminal "$target" --limit "$lines" ;;
  esac
}

_cmd_wait() {
  local agent="$1"; shift
  local timeout=300
  while [ $# -gt 0 ]; do case "$1" in --timeout) timeout="$2"; shift 2 ;; *) shift ;; esac; done
  local sub target; sub="$(_detect_substrate)" || return 1
  target="$(_resolve_target "$agent")" || return 1
  case "$sub" in
    orca) orca terminal wait --terminal "$target" --for tui-idle --timeout-ms "$(( timeout * 1000 ))" ;;
    cmux)
      # No native idle in cmux: poll read-screen until two consecutive identical snapshots.
      local prev="" cur elapsed=0
      while [ "$elapsed" -lt "$timeout" ]; do
        cur="$(cmux read-screen --surface "$target" --lines 6)"
        [ "$cur" = "$prev" ] && [ -n "$cur" ] && return 0
        prev="$cur"; sleep 3; elapsed=$((elapsed + 3))
      done
      return 1 ;;
  esac
}

_cmd_alive() {
  local agent="$1" sub target; sub="$(_detect_substrate)" || return 1
  target="$(_resolve_target "$agent")" || return 1
  case "$sub" in
    cmux) cmux tree --all | grep -q -- "$target" ;;
    orca)
      if orca terminal list --json | jq -e --arg id "$target" '.result.terminals[] | select(.handle == $id)' >/dev/null 2>&1; then
        return 0
      else
        return 1
      fi ;;
  esac
}

_cmd_notify() {
  local title="$1" body="$2" sub; sub="$(_detect_substrate)" || sub="cmux"
  case "$sub" in
    cmux) cmux notify --title "$title" --body "$body" || true ;;
    orca) command -v osascript >/dev/null 2>&1 \
            && osascript -e "display notification \"$body\" with title \"$title\"" >/dev/null 2>&1 || true ;;
  esac
  return 0
}

main() {
  local verb="${1:-}"; shift || true
  case "$verb" in
    env)    _cmd_env "$@" ;;
    send)   _cmd_send "$@" ;;
    clear)  _cmd_clear "$@" ;;
    read)   _cmd_read "$@" ;;
    wait)   _cmd_wait "$@" ;;
    alive)  _cmd_alive "$@" ;;
    notify) _cmd_notify "$@" ;;
    task-create) _cmd_task_create "$@" ;;
    dispatch) _cmd_dispatch "$@" ;;
    await) _cmd_await "$@" ;;
    gate-create) _cmd_gate_create "$@" ;;
    gate-resolve) _cmd_gate_resolve "$@" ;;
    *)      echo "hmad-dispatch: unknown verb '$verb'" >&2; return 2 ;;
  esac
}
main "$@"
