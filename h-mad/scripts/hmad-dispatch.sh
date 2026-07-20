#!/usr/bin/env bash
# hmad-dispatch — substrate-agnostic agent transport for the H-MAD skill.
# Verbs: env | send | read | wait | alive | clear | notify
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
  # Match a terminal whose command contains the agent token. Shape of
  # `orca terminal list --json` to confirm against live CLI; tolerate .command|.name.
  local token="$1" ids
  ids="$(orca terminal list --json | jq -r \
    --arg t "$token" '.[] | select(((.command//"") + " " + (.name//"")) | test($t)) | .id')"
  local n; n="$(printf '%s' "$ids" | grep -c . || true)"
  if [ "$n" -eq 1 ]; then printf '%s\n' "$ids"; return 0; fi
  echo "hmad-dispatch: orca terminal for '$token' resolved to $n candidates; pin HMAD_ORCA_${token^^}_TERMINAL" >&2
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
  return 0
}

main() {
  local verb="${1:-}"; shift || true
  case "$verb" in
    env)    _cmd_env "$@" ;;
    *)      echo "hmad-dispatch: unknown verb '$verb'" >&2; return 2 ;;
  esac
}
main "$@"
