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

_cmd_env() {
  local sub
  if ! sub="$(_detect_substrate)"; then
    echo "hmad-dispatch: no substrate detected (install cmux or orca, or set HMAD_SUBSTRATE)" >&2
    return 1
  fi
  echo "substrate: $sub"
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
