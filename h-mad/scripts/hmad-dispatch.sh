#!/usr/bin/env bash
# hmad-dispatch — substrate-agnostic agent transport for the H-MAD skill.
# Verbs: env | send | read | wait | alive | clear | notify | task-create | dispatch | await | gate-create | gate-resolve | worktree-create | worktree-ps | worktree-rm
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

_json_extract() {  # $1 = jq alternation expr; stdin JSON -> first non-empty match
  jq -r "${1} // empty"
}

_coordinator() {  # echo the coordinator handle or fail with a message
  if [ -n "${HMAD_ORCA_COORDINATOR_TERMINAL:-}" ]; then printf '%s\n' "$HMAD_ORCA_COORDINATOR_TERMINAL"
  else echo "hmad-dispatch: set HMAD_ORCA_COORDINATOR_TERMINAL (the H-MAD coordinator's Orca terminal handle)" >&2; return 1; fi
}

_orchestration_active() {  # 0 iff substrate=orca AND coordinator pinned
  local sub; sub="$(_detect_substrate)" 2>/dev/null || return 1
  [ "$sub" = "orca" ] && [ -n "${HMAD_ORCA_COORDINATOR_TERMINAL:-}" ]
}

_cmux_find() {
  # Match the single cmux surface whose terminal title contains the agent token
  # (case-insensitive). Mirrors _orca_find; the hardcoded surface:N defaults were
  # stale per-session, so detect by title instead. Pin HMAD_CMUX_<AGENT>_SURFACE to override.
  # Anchor the token to the LEADING title word (the launched command is the first
  # title token, e.g. "agy --…", "Codex - …") + a non-letter boundary, so unrelated
  # panes like `vim codex_result` or `less agy-notes` do not false-match.
  local token="$1" ids n
  ids="$(cmux tree --all 2>/dev/null | grep -iE "\[terminal\] \"${token}[^A-Za-z]" | grep -oE 'surface:[0-9]+')"
  n="$(printf '%s\n' "$ids" | grep -c . || true)"
  if [ "$n" -eq 1 ]; then printf '%s\n' "$ids"; return 0; fi
  echo "hmad-dispatch: cmux surface for '$token' matched $n candidates; pin HMAD_CMUX_$(printf '%s' "$token" | tr '[:lower:]' '[:upper:]')_SURFACE" >&2
  return 1
}

_resolve_target() {
  # $1 = agent (codex|agy). Echo concrete surface/terminal for the active substrate.
  local agent="$1" sub
  sub="$(_detect_substrate)" || return 1
  case "$sub:$agent" in
    cmux:codex)
      if [ -n "${HMAD_CMUX_CODEX_SURFACE:-}" ]; then printf '%s\n' "$HMAD_CMUX_CODEX_SURFACE"; return 0; fi
      _cmux_find codex; return $? ;;
    cmux:agy)
      if [ -n "${HMAD_CMUX_AGY_SURFACE:-}" ]; then printf '%s\n' "$HMAD_CMUX_AGY_SURFACE"; return 0; fi
      _cmux_find agy; return $? ;;
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
  # Match the single Orca terminal whose TITLE begins with the agent token
  # (case-insensitive), mirroring _cmux_find. Pin HMAD_ORCA_<AGENT>_TERMINAL
  # to override.
  #
  # Identity comes from the title only. The previous matcher tested an
  # unanchored, case-sensitive regex against (preview + title): preview is live
  # scrollback, so any pane that merely rendered the word "codex" matched --
  # including the coordinator's own pane, which could then dispatch to itself.
  # Anchoring to the leading title word also rejects panes like
  # `vim codex_result.py`, exactly as the cmux side does.
  local token="$1" listing ids n
  listing="$(orca terminal list --json)" || return 1
  # Pass 1 -- anchored, case-insensitive TITLE match (identity, not content).
  ids="$(printf '%s' "$listing" | jq -r --arg t "$token" \
    '.result.terminals[] | select((.title//"") | test("^" + $t + "([^A-Za-z]|$)"; "i")) | .handle')"
  n="$(printf '%s' "$ids" | grep -c . || true)"
  if [ "$n" -eq 1 ]; then printf '%s\n' "$ids"; return 0; fi
  if [ "$n" -eq 0 ]; then
    # Pass 2 -- preview fallback. Agent panes often carry a generic title (the
    # Codex pane is titled after its worktree) while the preview holds the
    # launch banner, e.g. "OpenAI Codex (v0.144.6)". Never consider the
    # coordinator's own pane: its preview renders this conversation, so the
    # token appears there whenever it is merely discussed, and matching it
    # would make the coordinator dispatch to itself.
    ids="$(printf '%s' "$listing" | jq -r --arg t "$token" \
      --arg self "${HMAD_ORCA_COORDINATOR_TERMINAL:-}" \
      '.result.terminals[]
       | select(.handle != $self)
       | select((.preview//"") | test($t; "i")) | .handle')"
    n="$(printf '%s' "$ids" | grep -c . || true)"
    if [ "$n" -eq 1 ]; then printf '%s\n' "$ids"; return 0; fi
  fi
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
  # Real shape is .result.task.id; legacy flat keys kept as fallbacks. NEVER
  # fall through to the envelope .id -- that is a per-request correlation uuid
  # that always exists, so it silently yields a plausible but useless id.
  orca orchestration task-create --spec "$spec" --task-title "$1" --json \
    | _json_extract '.result.task.id // .result.taskId // .taskId'
}

_cmd_dispatch() {  # $1 agent, $2 task_id
  _require_orca dispatch || return $?
  _need "${1:-}" agent || return $?; _need "${2:-}" task_id || return $?
  local target; target="$(_resolve_target "$1")" || return 1
  # --inject actually delivers the preamble+task to the worker terminal;
  # without it Orca returns the text and delivers nothing, so worker_done
  # never fires and await times out. --return-preamble additionally echoes
  # the text back to the coordinator for logging.
  orca orchestration dispatch --task "$2" --to "$target" --inject --return-preamble --json
}

_cmd_await() {  # $1 task_id, [--timeout <s>]
  _require_orca await || return $?
  _need "${1:-}" task_id || return $?
  local task="$1"; shift
  local timeout=600
  while [ $# -gt 0 ]; do case "$1" in --timeout) timeout="$2"; shift 2 ;; *) shift ;; esac; done
  local coord; coord="$(_coordinator)" || return 1
  orca orchestration check --terminal "$coord" --wait --types worker_done --timeout-ms "$(( timeout * 1000 ))" --json \
    | jq -c --arg t "$task" '
        (.result.messages // .messages // [])
        | map(select(
            (((.payload // {})
              | if type == "string" then (fromjson? // {}) else . end
              | if type == "object" then .taskId else null end)
             // .taskId // .["task-id"]) == $t))
        | .[0] // empty'
}

_cmd_gate_create() {  # $1 task_id, $2 question, [$3 options-json]
  _require_orca gate-create || return $?
  _need "${1:-}" task_id || return $?; _need "${2:-}" question || return $?
  # .result.gate.id is the real shape; no envelope .id fallback (see task-create).
  if [ -n "${3:-}" ]; then
    orca orchestration gate-create --task "$1" --question "$2" --options "$3" --json \
      | _json_extract '.result.gate.id // .result.gateId // .gateId'
  else
    orca orchestration gate-create --task "$1" --question "$2" --json \
      | _json_extract '.result.gate.id // .result.gateId // .gateId'
  fi
}

_cmd_gate_resolve() {  # $1 gate_id, $2 resolution
  _require_orca gate-resolve || return $?
  _need "${1:-}" gate_id || return $?; _need "${2:-}" resolution || return $?
  orca orchestration gate-resolve --id "$1" --resolution "$2" --json
}

_cmd_worktree_create() {  # <name> [--agent <id>] [--base <ref>] [--prompt-file <path>] [--repo <sel>|--workspace <sel>|--project <id>]
  _require_orca worktree-create || return $?
  _need "${1:-}" name || return $?
  local name="$1"; shift
  local agent="" base="" pf="" repo="" ws="" proj=""
  while [ $# -gt 0 ]; do case "$1" in
    --agent) agent="$2"; shift 2 ;; --base) base="$2"; shift 2 ;;
    --prompt-file) pf="$2"; shift 2 ;;
    --repo) repo="$2"; shift 2 ;; --workspace) ws="$2"; shift 2 ;; --project) proj="$2"; shift 2 ;;
    *) shift ;; esac; done
  local args=(worktree create --name "$name")
  [ -n "$agent" ] && args+=(--agent "$agent")
  [ -n "$base" ] && args+=(--base-branch "$base")
  [ -n "$repo" ] && args+=(--repo "$repo")
  [ -n "$ws" ]   && args+=(--workspace "$ws")
  [ -n "$proj" ] && args+=(--project "$proj")
  if [ -n "$pf" ]; then
    [ -f "$pf" ] || { echo "hmad-dispatch: prompt file not found: $pf" >&2; return 2; }
    args+=(--prompt "$(cat "$pf")")
  fi
  args+=(--json)
  orca "${args[@]}" | _json_extract '.result.worktree.id // .result.worktree.selector // .result.worktree.handle'
}

_cmd_worktree_ps() {  # [--limit <n>]
  _require_orca worktree-ps || return $?
  local args=(worktree ps)
  while [ $# -gt 0 ]; do case "$1" in --limit) args+=(--limit "$2"); shift 2 ;; *) shift ;; esac; done
  args+=(--json)
  orca "${args[@]}" | _json_extract '.result | tojson'
}

_cmd_worktree_rm() {  # <selector> [--force]
  _require_orca worktree-rm || return $?
  _need "${1:-}" selector || return $?
  local sel="$1"; shift
  local args=(worktree rm --worktree "$sel")
  while [ $# -gt 0 ]; do case "$1" in --force) args+=(--force); shift ;; *) shift ;; esac; done
  args+=(--json)
  local rc=0
  orca "${args[@]}" >/dev/null || rc=$?
  [ $rc -eq 0 ] || { echo "[H-MAD] worktree-rm failed selector=$sel rc=$rc" >&2; return $rc; }
}

_cmd_file_diff() {   # <path> [--staged] [--worktree <sel>]
  _require_orca file-diff || return $?
  _need "${1:-}" path || return $?
  local path="$1"; shift
  local args=(file diff "$path")
  while [ $# -gt 0 ]; do case "$1" in
    --staged) args+=(--staged); shift ;;
    --worktree) args+=(--worktree "$2"); shift 2 ;;
    *) shift ;; esac; done
  args+=(--json)
  orca "${args[@]}" | _json_extract '.result | tojson'
}

_cmd_file_open_changed() {   # [--mode edit|diff|both] [--worktree <sel>]
  _require_orca file-open-changed || return $?
  local args=(file open-changed)
  while [ $# -gt 0 ]; do case "$1" in
    --mode) args+=(--mode "$2"); shift 2 ;;
    --worktree) args+=(--worktree "$2"); shift 2 ;;
    *) shift ;; esac; done
  args+=(--json)
  orca "${args[@]}" | _json_extract '.result | tojson'
}

_cmd_automation_create() {   # --name <n> --trigger <t> --prompt-file <p> [--provider <a>] [--precheck <c>] [--repo|--workspace|--project <sel>]
  _require_orca automation-create || return $?
  local name="" trig="" pf="" prov="" pre="" repo="" ws="" proj=""
  while [ $# -gt 0 ]; do case "$1" in
    --name) name="$2"; shift 2 ;;      --trigger) trig="$2"; shift 2 ;;
    --prompt-file) pf="$2"; shift 2 ;; --provider) prov="$2"; shift 2 ;;
    --precheck) pre="$2"; shift 2 ;;   --repo) repo="$2"; shift 2 ;;
    --workspace) ws="$2"; shift 2 ;;   --project) proj="$2"; shift 2 ;;
    *) shift ;; esac; done
  _need "$name" name || return $?; _need "$trig" trigger || return $?; _need "$pf" prompt-file || return $?
  [ -f "$pf" ] || { echo "hmad-dispatch: prompt file not found: $pf" >&2; return 2; }
  local args=(automations create --name "$name" --trigger "$trig" --prompt "$(cat "$pf")")
  [ -n "$prov" ] && args+=(--provider "$prov")
  [ -n "$pre" ]  && args+=(--precheck "$pre")
  [ -n "$repo" ] && args+=(--repo "$repo")
  [ -n "$ws" ]   && args+=(--workspace "$ws")
  [ -n "$proj" ] && args+=(--project "$proj")
  args+=(--json)
  orca "${args[@]}" | _json_extract '.result.automation.id // .result.automation // .result.automationId'
}

_cmd_automation_run() {   # <id>
  _require_orca automation-run || return $?
  _need "${1:-}" id || return $?
  orca automations run "$1" --json
}

_cmd_automation_list() {
  _require_orca automation-list || return $?
  orca automations list --json | _json_extract '.result | tojson'
}

_cmd_automation_remove() {   # <id>
  _require_orca automation-remove || return $?
  _need "${1:-}" id || return $?
  orca automations remove "$1" --json
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

# $1 agent, $2 promptfile.
#
# Small prompts are inlined. Above HMAD_SEND_INLINE_MAX bytes (default 8192)
# the agent is told to read the staged file instead: pasting a 32-61 KB audit
# prompt into a TUI is what the file-indirection rule exists to prevent, and
# inlining unconditionally put the documented dispatch step in direct conflict
# with it at exactly the sizes that occur in practice.
_cmd_send() {
  local agent="$1" promptfile="$2"
  local max="${HMAD_SEND_INLINE_MAX:-8192}"

  if [ ! -f "$promptfile" ]; then
    echo "hmad-dispatch: no such prompt file: $promptfile" >&2
    return 2
  fi

  local size
  size=$(wc -c < "$promptfile" | tr -d ' ')

  if [ "$size" -le "$max" ]; then
    _send_text "$agent" "$(cat "$promptfile")"
    return $?
  fi

  # Canonical path — the agent resolves it from its own cwd, not ours.
  local abs
  abs="$(cd "$(dirname "$promptfile")" && pwd -P)/$(basename "$promptfile")"
  _send_text "$agent" "Read $abs and follow the instructions in it. It is ${size} bytes; read the whole file before responding."
}
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

_snapshot() {   # $1 substrate, $2 target
  case "$1" in
    cmux) cmux read-screen --surface "$2" --lines 6 ;;
    orca) orca terminal read --terminal "$2" --limit 6 ;;
  esac
}

# Two consecutive identical snapshots. A single read can catch a pane
# mid-write; two matching ones cannot.
_wait_stable() {   # $1 substrate, $2 target, $3 timeout-seconds
  local sub="$1" target="$2" timeout="$3"
  local interval="${HMAD_WAIT_POLL_INTERVAL:-3}"
  local prev="" cur elapsed=0

  # The clock must advance even when the interval is 0 (tests use that to run
  # without sleeping); otherwise a pane that never stabilises loops forever.
  local tick="$interval"
  [ "$tick" -lt 1 ] && tick=1

  while [ "$elapsed" -le "$timeout" ]; do
    cur="$(_snapshot "$sub" "$target")"
    # An empty read is not evidence of idleness — only two identical
    # non-empty snapshots are.
    [ -n "$cur" ] && [ "$cur" = "$prev" ] && return 0
    prev="$cur"
    [ "$interval" -gt 0 ] && sleep "$interval"
    elapsed=$((elapsed + tick))
  done
  return 1
}

_cmd_wait() {
  local agent="$1"; shift
  local timeout=300
  while [ $# -gt 0 ]; do case "$1" in --timeout) timeout="$2"; shift 2 ;; *) shift ;; esac; done
  local sub target; sub="$(_detect_substrate)" || return 1
  target="$(_resolve_target "$agent")" || return 1
  case "$sub" in
    orca)
      # Orca's native `--for tui-idle` has been observed reporting satisfied
      # while an agent was still generating, so it is a fast first gate, not
      # proof: its "not idle" is authoritative, its "idle" is not. Confirm
      # with the same stability comparison cmux has always relied on.
      orca terminal wait --terminal "$target" --for tui-idle --timeout-ms "$(( timeout * 1000 ))" || return 1
      _wait_stable "$sub" "$target" "$timeout" ;;
    cmux)
      # No native idle in cmux at all — stability is the only signal.
      _wait_stable "$sub" "$target" "$timeout" ;;
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
    worktree-create) _cmd_worktree_create "$@" ;;
    worktree-ps) _cmd_worktree_ps "$@" ;;
    worktree-rm) _cmd_worktree_rm "$@" ;;
    file-diff) _cmd_file_diff "$@" ;;
    file-open-changed) _cmd_file_open_changed "$@" ;;
    automation-create) _cmd_automation_create "$@" ;;
    automation-run) _cmd_automation_run "$@" ;;
    automation-list) _cmd_automation_list "$@" ;;
    automation-remove) _cmd_automation_remove "$@" ;;
    *)      echo "hmad-dispatch: unknown verb '$verb'" >&2; return 2 ;;
  esac
}
main "$@"
