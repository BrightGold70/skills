#!/usr/bin/env bash
# hmad-dispatch — substrate-agnostic agent transport for the H-MAD skill.
# Verbs: env | resolve | pin | pin-agents | send | read | wait | alive | clear | interrupt | notify | task-create | dispatch | await | gate-create | gate-resolve | gate-wait | report-wait | worktree-comment | worktree-create | worktree-current | worktree-ps | worktree-rm
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
  if [ "$has_orca" = 1 ]; then printf 'orca\n'; return 0; fi   # both present => orca
  if [ "$has_cmux" = 1 ]; then printf 'cmux\n'; return 0; fi
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

_orca_json() {
  # Run `orca "$@"`, then extract with the jq expression in $1 — but ONLY after
  # confirming the response envelope is ok:true. A bare `orca … | _json_extract`
  # pipe hides two failures: `set -o pipefail` catches a non-zero *exit*, but an
  # exit-0 response carrying `"ok":false` (an error envelope) slips through as an
  # empty/garbage extract. Capture-then-check surfaces both. $1 = jq extract expr
  # (may be empty to only assert ok:true), rest = orca args.
  local expr="$1"; shift
  local out rc
  out="$(orca "$@")" || { rc=$?; echo "$out" >&2; return "$rc"; }
  # Reject an explicit error envelope (`"ok":false`) — the exact exit-0 failure a
  # bare pipe swallows. `.ok != false` passes when ok is true or absent, so a real
  # Orca response (always ok:true) proceeds while an error envelope is surfaced.
  printf '%s' "$out" | jq -e '.ok != false' >/dev/null 2>&1 || { echo "$out" >&2; return 1; }
  [ -n "$expr" ] && printf '%s' "$out" | _json_extract "$expr"
  return 0
}

_coordinator() {  # echo the coordinator handle or fail with a message
  if [ -n "${HMAD_ORCA_COORDINATOR_TERMINAL:-}" ]; then printf '%s\n' "$HMAD_ORCA_COORDINATOR_TERMINAL"; return 0; fi
  # Auto-detect (orca): Orca exports ORCA_PANE_KEY="<tabId>:<leafId>" into each
  # pane. The coordinator is THIS pane, whose leafId matches a terminal's `.leafId`
  # in `orca terminal list`. This removes the manual pin as a precondition for
  # orchestration mode; the pin still wins when set.
  if [ -n "${ORCA_PANE_KEY:-}" ]; then
    local leaf handle
    leaf="${ORCA_PANE_KEY##*:}"
    handle="$(orca terminal list --json 2>/dev/null \
      | jq -r --arg l "$leaf" '.result.terminals[]? | select(.leafId == $l) | .handle' 2>/dev/null | head -1)"
    if [ -n "$handle" ]; then printf '%s\n' "$handle"; return 0; fi
  fi
  echo "hmad-dispatch: no coordinator — set HMAD_ORCA_COORDINATOR_TERMINAL (auto-detect from ORCA_PANE_KEY failed)" >&2; return 1
}

_orchestration_active() {  # 0 iff substrate=orca AND a coordinator resolves (pin or auto-detect)
  local sub; sub="$(_detect_substrate)" 2>/dev/null || return 1
  [ "$sub" = "orca" ] && _coordinator >/dev/null 2>&1
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

_pin_file() {  # path to the session pin file (agent=handle lines)
  printf '%s\n' "${HMAD_ORCA_PIN_FILE:-.h-mad/orca-pins.env}"
}

_pin_lookup() {  # $1 agent -> echo the pinned handle from the pin file, or nothing
  # H4: Codex/agy auto-detect by title/preview decays mid-run (the model-id
  # banner scrolls out of the Orca preview once the agent does work), so a long
  # autonomous run can lose a pane. `pin-agents` records the resolved handles
  # here once; resolution reads them before falling back to auto-detect.
  local pf; pf="$(_pin_file)"
  [ -f "$pf" ] || return 1
  local line; line="$(grep -E "^$1=" "$pf" 2>/dev/null | head -1 || true)"
  [ -n "$line" ] || return 1
  printf '%s\n' "${line#*=}"
}

_resolve_target() {
  # $1 = agent (codex|agy). Echo concrete surface/terminal for the active substrate.
  # Orca precedence: explicit env pin > session pin file (H4) > auto-detect.
  local agent="$1" sub pinned
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
      pinned="$(_pin_lookup codex || true)"; [ -n "$pinned" ] && { printf '%s\n' "$pinned"; return 0; }
      _orca_find codex; return $? ;;
    orca:agy)
      if [ -n "${HMAD_ORCA_AGY_TERMINAL:-}" ]; then printf '%s\n' "$HMAD_ORCA_AGY_TERMINAL"; return 0; fi
      pinned="$(_pin_lookup agy || true)"; [ -n "$pinned" ] && { printf '%s\n' "$pinned"; return 0; }
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
  local token="$1" listing ids n self scope_wt scoped
  listing="$(orca terminal list --json)" || return 1
  # Scope to the coordinator's OWN worktree, and never match its own pane.
  # Orca runs one agent set per worktree; a parallel run in another worktree
  # (a HemaSuite pane also titled "agy") would otherwise make the title match
  # ambiguous (n>1) and resolve nothing. The coordinator is resolved via the
  # pin or the ORCA_PANE_KEY leafId auto-detect (_coordinator); its worktreePath
  # is the scope. When no coordinator is resolvable (manual use, stub tests
  # without ORCA_PANE_KEY), $self and $scope_wt stay empty and matching is
  # global -- identical to the pre-scoping behaviour.
  self="$(_coordinator 2>/dev/null || true)"
  scope_wt=""
  if [ -n "$self" ]; then
    scope_wt="$(printf '%s' "$listing" | jq -r --arg h "$self" \
      '(.result.terminals[]? | select(.handle==$h) | .worktreePath) // empty' | head -1)"
  fi
  # Candidate set: same worktree as the coordinator (when known), coordinator's
  # own pane always excluded (even in Pass 1 -- its title/preview may carry the
  # token because it renders this conversation).
  scoped="$(printf '%s' "$listing" | jq -c --arg wt "$scope_wt" --arg self "$self" \
    '{result:{terminals:[.result.terminals[]?
       | select($self=="" or .handle != $self)
       | select($wt=="" or (.worktreePath // "")==$wt)]}}')"
  # Pass 1 -- anchored, case-insensitive TITLE match (identity, not content).
  ids="$(printf '%s' "$scoped" | jq -r --arg t "$token" \
    '.result.terminals[] | select((.title//"") | test("^" + $t + "([^A-Za-z]|$)"; "i")) | .handle')"
  n="$(printf '%s' "$ids" | grep -c . || true)"
  if [ "$n" -eq 1 ]; then printf '%s\n' "$ids"; return 0; fi
  if [ "$n" -eq 0 ]; then
    # Pass 2 -- preview fallback. Agent panes often carry a generic title (the
    # Codex pane is titled after its worktree) while the preview holds the
    # launch banner. The token alone is not always present: a user-launched
    # Codex shows no "codex" literal, only its model id (e.g. "gpt-5.6-terra")
    # and persona text; agy may show "Gemini"/"Antigravity". Match an
    # agent-specific signature set. The coordinator's own pane is already
    # excluded from $scoped above; a collision yields n>1 -> UNRESOLVED (safe),
    # never a mis-dispatch.
    local pv_re="$token"
    case "$token" in
      codex) pv_re='codex|gpt-[0-9]' ;;
      agy)   pv_re='agy|gemini|antigravity' ;;
    esac
    ids="$(printf '%s' "$scoped" | jq -r --arg t "$pv_re" \
      '.result.terminals[] | select((.preview//"") | test($t; "i")) | .handle')"
    n="$(printf '%s' "$ids" | grep -c . || true)"
    if [ "$n" -eq 1 ]; then printf '%s\n' "$ids"; return 0; fi
  fi
  echo "hmad-dispatch: orca terminal for '$token' resolved to $n candidates${scope_wt:+ in worktree $scope_wt}; pin HMAD_ORCA_$(printf '%s' "$token" | tr '[:lower:]' '[:upper:]')_TERMINAL" >&2
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

_cmd_resolve() {
  # resolve <agent> — print the resolved handle/surface for ONE agent
  # (codex|agy) to stdout and exit 0; empty stdout + stderr diagnostic + exit 1
  # when UNRESOLVED; empty stdout + stderr message + exit 2 for an unknown or
  # missing agent. Single-agent form of what `env` computes for both; delegates
  # to _resolve_target so the two cannot diverge.
  local agent="${1:-}"
  _resolve_target "$agent"
}

_cmd_pin_agents() {  # [--clear] — resolve codex+agy ONCE and persist to the pin file
  # H4: auto-detect by preview decays once an agent does work. Call this after the
  # Phase-5 substrate check to freeze the resolved handles into the session pin
  # file, so every later dispatch is deterministic. Resolves FRESH (explicit env
  # pin wins, else auto-detect) — it never reads the pin file it is about to write.
  # `--clear` removes the pin file. Precedence at read time stays: env > pin file
  # > auto-detect, so an operator env pin always overrides a stale pinned handle.
  _require_orca pin-agents || return $?
  local pf; pf="$(_pin_file)"
  case "${1:-}" in --clear) rm -f "$pf"; echo "[H-MAD] pins cleared: $pf" >&2; return 0 ;; esac
  local dir; dir="$(dirname "$pf")"; [ -d "$dir" ] || mkdir -p "$dir"
  local a U var handle tmp unresolved=""; tmp="$(mktemp)"
  for a in codex agy; do
    U="$(printf '%s' "$a" | tr '[:lower:]' '[:upper:]')"; var="HMAD_ORCA_${U}_TERMINAL"
    if [ -n "${!var:-}" ]; then handle="${!var}"; else handle="$(_orca_find "$a" 2>/dev/null || true)"; fi
    if [ -n "$handle" ]; then
      printf '%s=%s\n' "$a" "$handle" >> "$tmp"; echo "[H-MAD] pinned $a -> $handle" >&2
    else
      unresolved="${unresolved:+$unresolved }$a"
      # Codex especially: title = worktree name and the preview banner decays once
      # the pane works, so auto-detect has no stable signal. The ONLY durable path
      # is an explicit handle pin captured while identity is known (a fresh launch).
      echo "[H-MAD] pin-agents: $a UNRESOLVED — set HMAD_ORCA_${U}_TERMINAL=<handle> (auto-detect fails once the pane's banner decays; \`orca terminal list\` shows the handles)" >&2
    fi
  done
  # Persist whatever resolved — a partial pin still freezes the resolved agent.
  if [ -s "$tmp" ]; then mv "$tmp" "$pf"; printf '%s\n' "$pf"; else rm -f "$tmp"; fi
  # Fail LOUD on ANY unresolved agent: a run must never proceed believing both
  # agents are addressable when one silently is not. rc=1 forces the operator to
  # pin it before dispatching (H4 follow-up — the silent rc=0 partial was the bug).
  [ -z "$unresolved" ] || { echo "[H-MAD] pin-agents: unresolved: $unresolved (run cannot dispatch to it until pinned)" >&2; return 1; }
  return 0
}

_cmd_pin() {  # <agent> <handle> — record ONE agent's handle in the pin file
  # The durable way to make Codex addressable: capture its handle at a known
  # moment (right after launch, or read from `orca terminal list`) and pin it.
  # Auto-detect can't identify Codex post-decay and `orca terminal rename` does
  # NOT change the `.title` that resolution reads (it sets a separate tab-title
  # layer), so an explicit handle pin is the only reliable identity (H4/H5).
  _require_orca pin || return $?
  _need "${1:-}" agent || return $?; _need "${2:-}" handle || return $?
  case "$1" in codex|agy) ;; *) echo "hmad-dispatch: unknown agent '$1' (codex|agy)" >&2; return 2 ;; esac
  local pf; pf="$(_pin_file)"; local dir; dir="$(dirname "$pf")"; [ -d "$dir" ] || mkdir -p "$dir"
  local tmp; tmp="$(mktemp)"
  [ -f "$pf" ] && { grep -vE "^$1=" "$pf" >> "$tmp" 2>/dev/null || true; }
  printf '%s=%s\n' "$1" "$2" >> "$tmp"
  mv "$tmp" "$pf"
  echo "[H-MAD] pinned $1 -> $2 ($pf)" >&2
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
  _orca_json '.result.task.id // .result.taskId // .taskId' \
    orchestration task-create --spec "$spec" --task-title "$1" --json
}

_cmd_dispatch() {  # $1 agent, $2 task_id
  _require_orca dispatch || return $?
  _need "${1:-}" agent || return $?; _need "${2:-}" task_id || return $?
  local target; target="$(_resolve_target "$1")" || return 1
  # --inject actually delivers the preamble+task to the worker terminal;
  # without it Orca returns the text and delivers nothing, so worker_done
  # never fires and await times out. --return-preamble additionally echoes
  # the text back to the coordinator for logging.
  # Routed through _orca_json ('.' re-emits the whole envelope) so an exit-0
  # "ok":false error is surfaced on stderr + non-zero rather than echoed as a
  # phantom-success stdout — otherwise a failed dispatch reads as delivered and
  # await times out with no diagnostic (F11 scope, extended to the raw verbs).
  _orca_json '.' orchestration dispatch --task "$2" --to "$target" --inject --return-preamble --json
}

_cmd_await() {  # $1 task_id, [--timeout <s>]
  _require_orca await || return $?
  _need "${1:-}" task_id || return $?
  local task="$1"; shift
  local timeout=600
  while [ $# -gt 0 ]; do case "$1" in --timeout) timeout="$2"; shift 2 ;; *) shift ;; esac; done
  local coord; coord="$(_coordinator)" || return 1
  # Guard the check response through _orca_json first ('.' re-emits the whole
  # envelope, ok-checked), THEN run the worker_done filter. A raw pipe swallowed
  # an exit-0 "ok":false as `[]` → empty match → indistinguishable from "no
  # worker_done yet" → silent timeout (F11 scope, extended to the raw verbs).
  local checked
  checked="$(_orca_json '.' orchestration check --terminal "$coord" --wait --types worker_done --timeout-ms "$(( timeout * 1000 ))" --json)" || return $?
  printf '%s' "$checked" \
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
  local args=(orchestration gate-create --task "$1" --question "$2")
  [ -n "${3:-}" ] && args+=(--options "$3")
  args+=(--json)
  _orca_json '.result.gate.id // .result.gateId // .gateId' "${args[@]}"
}

_cmd_gate_resolve() {  # $1 gate_id, $2 resolution
  _require_orca gate-resolve || return $?
  _need "${1:-}" gate_id || return $?; _need "${2:-}" resolution || return $?
  # _orca_json guard: an exit-0 "ok":false must surface, not read as a phantom
  # successful resolution (F11 scope, extended to the raw verbs).
  _orca_json '.' orchestration gate-resolve --id "$1" --resolution "$2" --json
}

_cmd_gate_wait() {  # <gate_id> [--timeout <s>] [--interval <s>]
  # Block until a decision gate is resolved (by a human in the Orca UI, or by
  # gate-resolve), then echo its resolution. gate-create only opens a gate; this
  # is the missing half that lets a blocking gate actually block-and-resume.
  # Polls `orchestration gate-list` because there is no push/wait for a gate.
  _require_orca gate-wait || return $?
  _need "${1:-}" gate_id || return $?
  local gate="$1"; shift
  local timeout=600 interval="${HMAD_GATE_POLL_INTERVAL:-5}"
  while [ $# -gt 0 ]; do case "$1" in
    --timeout) timeout="$2"; shift 2 ;; --interval) interval="$2"; shift 2 ;;
    *) shift ;; esac; done
  local elapsed=0 res tick="$interval"
  [ "$tick" -lt 1 ] && tick=1
  while [ "$elapsed" -le "$timeout" ]; do
    # Resolved iff .resolution is set OR .status is explicitly "resolved". This
    # fails CLOSED: any other status (pending/open/created/waiting/…) keeps
    # polling rather than treating "not pending" as resolved — a blocking merge
    # gate must never proceed on an ambiguous state. Worst case is a spurious
    # timeout, the correct bias for a gate. Echo the resolution.
    res="$(orca orchestration gate-list --json 2>/dev/null \
      | jq -r --arg g "$gate" '
          .result.gates[]? | select(.id == $g)
          | select(((.resolution // "") != "") or ((.status // "") == "resolved"))
          | (.resolution // .status) // empty' 2>/dev/null | head -1)"
    if [ -n "$res" ]; then printf '%s\n' "$res"; return 0; fi
    [ "$interval" -gt 0 ] && sleep "$interval"
    elapsed=$((elapsed + tick))
  done
  echo "[H-MAD] gate-wait timed out after ${timeout}s (gate=$gate still pending)" >&2
  return 1
}

_cmd_report_wait() {  # <report-path> [--timeout <s>] [--interval <s>]
  # Wait for a dispatched agent to DROP a report file, then emit it. This is the
  # reliable alternative to wait+read+sentinel-extract under Orca: the agent writes
  # its full report to <report-path> and signals completion by creating
  # <report-path>.done; the coordinator polls the marker and reads the file. No
  # tui-idle guess, no screen scrape, no BEGIN/END sentinel — the file is complete
  # by construction. Substrate-agnostic: any agent that shares the filesystem and
  # can write a file works (cmux or orca), so it needs no _require_orca.
  # The .done marker (not just file existence) is the signal, so a half-written
  # report is never read; the file must also be non-empty.
  #
  # H3 decoupling: the polling loop lives in the standalone stdlib script
  # h_mad_report_wait.py, which this verb delegates to. When the dispatched
  # implementer is editing THIS wrapper (e.g. adding a verb), poll with the
  # script DIRECTLY — `python3 <skill>/scripts/h_mad_report_wait.py <path> …` —
  # so the coordinator's poll never re-parses a half-saved hmad-dispatch.sh and
  # can't die on a transient syntax error. Both paths share one implementation.
  local here; here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  python3 "$here/h_mad_report_wait.py" "$@"
}

_cmd_worktree_comment() {  # [<selector>] <text>
  _require_orca worktree-comment || return $?
  local sel text
  if [ "$#" -ge 2 ]; then sel="$1"; text="$2"; else sel="active"; text="${1:-}"; fi
  _need "$text" text || return $?
  _orca_json '' worktree set --worktree "$sel" --comment "$text" --json
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
  _orca_json '.result.worktree.id // .result.worktree.selector // .result.worktree.handle' "${args[@]}"
}

_cmd_worktree_current() {  # (no args)
  _require_orca worktree-current || return $?
  _orca_json '.result | tojson' worktree current --json
}

_cmd_worktree_ps() {  # [--limit <n>]
  _require_orca worktree-ps || return $?
  local args=(worktree ps)
  while [ $# -gt 0 ]; do case "$1" in --limit) args+=(--limit "$2"); shift 2 ;; *) shift ;; esac; done
  args+=(--json)
  _orca_json '.result | tojson' "${args[@]}"
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
  _orca_json '.result | tojson' "${args[@]}"
}

_cmd_file_open_changed() {   # [--mode edit|diff|both] [--worktree <sel>]
  _require_orca file-open-changed || return $?
  local args=(file open-changed)
  while [ $# -gt 0 ]; do case "$1" in
    --mode) args+=(--mode "$2"); shift 2 ;;
    --worktree) args+=(--worktree "$2"); shift 2 ;;
    *) shift ;; esac; done
  args+=(--json)
  _orca_json '.result | tojson' "${args[@]}"
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
  _orca_json '.result.automation.id // .result.automation // .result.automationId' "${args[@]}"
}

_cmd_automation_run() {   # <id>
  _require_orca automation-run || return $?
  _need "${1:-}" id || return $?
  orca automations run "$1" --json
}

_cmd_automation_list() {
  _require_orca automation-list || return $?
  _orca_json '.result | tojson' automations list --json
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

# Cancel a running/wedged agent turn by sending Ctrl-C (0x03). A bare Enter is
# NOT a safe nudge — for a TUI REPL like Antigravity it submits a blank turn and
# starts junk generation. Ctrl-C interrupts generation (and, sent twice, exits the
# REPL to the shell, which freezes the scrollback for a clean full-buffer read).
_cmd_interrupt() {   # <agent>
  local agent="$1" sub target; sub="$(_detect_substrate)" || return 1
  target="$(_resolve_target "$agent")" || return 1
  case "$sub" in
    cmux) cmux send-key --surface "$target" C-c ;;
    orca) orca terminal send --terminal "$target" --text $'\x03' ;;
  esac
}

_cmd_read() {
  # --lines <n> tails the last n lines (default 50). --cursor <n> reads from an
  # absolute cursor offset (orca only) so a report longer than the retained
  # viewport can be recovered; --from-start is shorthand for --cursor 0 with a
  # large limit, for capturing a full sentinel-framed report the tail truncated.
  local agent="$1"; shift
  local lines=50 cursor=""
  while [ $# -gt 0 ]; do case "$1" in
    --lines) lines="$2"; shift 2 ;;
    --cursor) cursor="$2"; shift 2 ;;
    --from-start) cursor="0"; lines="4000"; shift ;;
    *) shift ;; esac; done
  local sub target; sub="$(_detect_substrate)" || return 1
  target="$(_resolve_target "$agent")" || return 1
  case "$sub" in
    cmux) cmux read-screen --surface "$target" --lines "$lines" ;;
    orca)
      if [ -n "$cursor" ]; then
        orca terminal read --terminal "$target" --cursor "$cursor" --limit "$lines"
      else
        orca terminal read --terminal "$target" --limit "$lines"
      fi ;;
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
    resolve) _cmd_resolve "$@" ;;
    pin) _cmd_pin "$@" ;;
    pin-agents) _cmd_pin_agents "$@" ;;
    send)   _cmd_send "$@" ;;
    clear)  _cmd_clear "$@" ;;
    interrupt) _cmd_interrupt "$@" ;;
    read)   _cmd_read "$@" ;;
    wait)   _cmd_wait "$@" ;;
    alive)  _cmd_alive "$@" ;;
    notify) _cmd_notify "$@" ;;
    task-create) _cmd_task_create "$@" ;;
    dispatch) _cmd_dispatch "$@" ;;
    await) _cmd_await "$@" ;;
    gate-create) _cmd_gate_create "$@" ;;
    gate-resolve) _cmd_gate_resolve "$@" ;;
    gate-wait) _cmd_gate_wait "$@" ;;
    report-wait) _cmd_report_wait "$@" ;;
    worktree-comment) _cmd_worktree_comment "$@" ;;
    worktree-create) _cmd_worktree_create "$@" ;;
    worktree-current) _cmd_worktree_current "$@" ;;
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
