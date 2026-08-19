#!/usr/bin/env bash
# hmad-dispatch — substrate-agnostic agent transport for the H-MAD skill.
# Verbs: env | resolve | launch | pin | pin-agents | send | read | wait | alive | clear | interrupt | notify | run-ensure | task-create | dispatch | await | gate-create | gate-resolve | gate-wait | report-wait | worktree-comment | worktree-create | worktree-current | worktree-list | worktree-ps | worktree-rm
# Substrate: cmux (manaflow-ai/cmux) or orca (stablyai/orca). Auto-detected.
set -euo pipefail

# Reject an unrecognised flag instead of dropping it. Every arg loop below
# consumes its POSITIONALS before the loop starts, so anything still present
# when the loop runs is meant to be a flag -- which is what makes failing safe
# for positional-taking verbs too.
#
# Silently shifting past a typo hands back a plausible answer to a question
# nobody asked: `worktree-rm <sel> --bse main` drops the base and checks
# unmerged-ness against the wrong ref (the J15/J17 family, reached by a spelling
# mistake), `read <agent> --form-start` returns a 50-line tail while the caller
# believes it asked for the whole buffer (J3), and `wait <agent> --timeut 2`
# blocks for the 300s default instead of 2s -- measured.
#
# Exit 2, not a verdict token: a malformed request is an operational error, per
# invariants.base.md §"Audit-gate signal discipline".
_unknown_opt() {  # $1 verb, $2 token
  echo "hmad-dispatch: $1: unknown option '$2'" >&2
  return 2
}

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

_run_bound() {  # echo bound Run id (rc 0) | rc 1 = genuinely unbound | rc 2 = unknown
  # `task-list` is the cheapest read that reports the binding: bound terminals get
  # `.result.runId`, unbound ones get `{"ok":false,"error":{"code":"run_required"}}`.
  #
  # The three outcomes are kept DISTINCT on purpose. Collapsing "unbound" and
  # "something else went wrong" into one empty string means any transient probe
  # failure looks like "no Run yet" and silently creates a second Run — which
  # scatters one fanout's tasks across two namespaces, so the coordinator's `check`
  # never sees half its workers. Only the documented `run_required` code may be
  # read as unbound; anything else refuses to guess.
  local out code rid
  out="$(orca orchestration task-list --json 2>/dev/null)" || true
  if printf '%s' "$out" | jq -e '.ok != false' >/dev/null 2>&1; then
    rid="$(printf '%s' "$out" | jq -r '.result.runId // empty' 2>/dev/null | head -1)"
    # A bound terminal ALWAYS reports runId; ok:true without one is a shape we do
    # not recognise, not evidence of "unbound". Fall through to the refusal below
    # rather than inventing a Run from a response we cannot read.
    if [ -n "$rid" ]; then printf '%s\n' "$rid"; return 0; fi
    echo "hmad-dispatch: Run probe returned ok with no runId; refusing to create a Run on a guess" >&2
    return 2
  fi
  code="$(printf '%s' "$out" | jq -r '.error.code // empty' 2>/dev/null)"
  [ "$code" = "run_required" ] && return 1
  echo "hmad-dispatch: Run probe failed (${code:-unrecognised response}); refusing to create a Run on a guess" >&2
  return 2
}

_run_ensure() {  # guarantee this coordinator terminal has a bound Run; echo its id
  # WHY THIS EXISTS: every orchestration mutation belongs to an explicitly bound
  # Run ("New orchestration messages and tasks belong to one explicitly bound Run"
  # — orchestration guide §Ownership; "Create or bind a Run once before the common
  # loop" — §Tasks And Dispatch). Without one the FIRST call of the flow fails:
  #
  #   $ orca orchestration task-list --json
  #   {"ok":false,"error":{"code":"run_required",
  #    "message":"No Run is bound. Use orchestration run-create or run-use first."}}
  #
  # This wrapper never bound one, so task-create — the entry point of
  # task-create → dispatch → worker_done → await → gate — returned ok:false and the
  # whole structured path died at step one. The Run model became mandatory in a
  # contract migration after this wrapper was written (`run-list` still shows the
  # `run_legacy_local` tombstone and a "Recovered orchestration work from a contract
  # update" Run), which is why stub-only tests never noticed.
  #
  # Binding is per-coordinator-terminal runtime state and PERSISTS ACROSS separate
  # CLI processes (verified live: run-create, then task-list from a fresh process,
  # returns the same runId). So binding once per session is enough — this is called
  # from task-create, the first mutation in the flow.
  local rid
  if [ -n "${HMAD_ORCA_RUN:-}" ]; then
    # Explicit pin wins, same precedence as HMAD_ORCA_COORDINATOR_TERMINAL. Bind to
    # it rather than assuming it is already bound — the pin may name a Run created
    # by another pane.
    _orca_json '' orchestration run-use --id "$HMAD_ORCA_RUN" --json || {
      echo "hmad-dispatch: HMAD_ORCA_RUN=$HMAD_ORCA_RUN could not be bound (run-use failed)" >&2; return 1; }
    printf '%s\n' "$HMAD_ORCA_RUN"; return 0
  fi
  local rc=0
  rid="$(_run_bound)" || rc=$?
  # rc 2 = the probe itself failed. Creating a Run here would be acting on a guess,
  # so propagate instead (the message is already on stderr).
  [ "$rc" -eq 2 ] && return 1
  if [ "$rc" -eq 0 ] && [ -n "$rid" ]; then printf '%s\n' "$rid"; return 0; fi
  # Unbound: create one. run-create binds it to the creating terminal automatically
  # (the response carries coordinator_handle + coordinator_pane_key), so no separate
  # run-use is needed here.
  local objective="${HMAD_ORCA_RUN_OBJECTIVE:-H-MAD orchestration ($(basename "$PWD"))}"
  rid="$(_orca_json '.result.run.id // .result.runId' orchestration run-create --objective "$objective" --json)" || return $?
  [ -n "$rid" ] || { echo "hmad-dispatch: run-create returned no run id; cannot bind a Run" >&2; return 1; }
  echo "[H-MAD] orchestration run bound: $rid ($objective)" >&2
  printf '%s\n' "$rid"
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
  # J2: this used to be the bare relative path `.h-mad/orca-pins.env`, resolved
  # against the CURRENT DIRECTORY. So a coordinator sitting in repo B while
  # driving a run in repo A read B's pins and reported UNRESOLVED, and a plain
  # `cd` into a subdirectory silently started a second, empty pin file.
  # Cross-repo and subdirectory work are both normal modes.
  #
  # The blast radius was larger than the pins: _receipt_file() derives from
  # dirname(_pin_file), so the Wave-3 preflight receipt moved with the cwd too --
  # `env` in one directory and `send` in another could disagree about whether a
  # receipt existed at all.
  #
  # Anchor to the enclosing git repository, which is where `.h-mad/` lives by
  # convention, so every directory inside one repo agrees. Outside a repo there
  # is nothing better than the cwd, and that stays the old behaviour rather than
  # inventing a location.
  if [ -n "${HMAD_ORCA_PIN_FILE:-}" ]; then
    printf '%s\n' "$HMAD_ORCA_PIN_FILE"; return 0
  fi
  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -n "$root" ]; then
    printf '%s\n' "$root/.h-mad/orca-pins.env"
  else
    printf '%s\n' ".h-mad/orca-pins.env"
  fi
}

# Path to the preflight receipt. Anchored to the pin file's directory so that a
# caller isolating HMAD_ORCA_PIN_FILE isolates the receipt too (test harness
# already does this per-invocation); an explicit override wins outright.
_receipt_file() {  # -> path
  printf '%s\n' "${HMAD_PREFLIGHT_RECEIPT_FILE:-$(dirname "$(_pin_file)")/preflight.receipt}"
}

# Deterministic identity of the current agent resolution. Deliberately NOT hashed:
# it is not a secret, a plain value is diagnosable by reading the file, and it
# avoids a shasum/sha256sum portability dependency. An unresolvable agent
# contributes the literal UNRESOLVED, so pinning one invalidates the receipt.
_fingerprint() {  # -> "codex=<v>;agy=<v>"
  local a v out=""
  for a in codex agy; do
    v="$(_resolve_target "$a" 2>/dev/null)" || v="UNRESOLVED"
    [ -n "$v" ] || v="UNRESOLVED"
    out="${out:+$out;}$a=$v"
  done
  printf '%s\n' "$out"
}

_receipt_write() {  # no args; writes verdict/fingerprint/ts
  local rf; rf="$(_receipt_file)"
  local dir; dir="$(dirname "$rf")"; [ -d "$dir" ] || mkdir -p "$dir"
  { printf 'verdict=PASS\n'
    printf 'fingerprint=%s\n' "$(_fingerprint)"
    printf 'ts=%s\n' "$(date +%s)"
  } > "$rf"
}

_receipt_clear() { rm -f "$(_receipt_file)"; }

# Validate the receipt. Prints a reason token on stdout for the caller to compose
# into its stderr message; returns 0 only when the receipt exists, says PASS, is
# within the TTL, and still matches resolution NOW.
#
# Note this compares RESOLVED VALUES, not liveness: _resolve_target consults the
# env pin, then the pin file, then auto-detect, and never calls `orca terminal
# list` when a pin exists. So an unreadable listing leaves resolution unchanged
# and cannot spuriously invalidate a receipt -- the rc=2 "unknown" contract of
# _orca_handle_live is honoured structurally, with no special case.
_receipt_valid() {  # -> 0 valid; 1 + reason token on stdout
  local rf ttl now v fp ts
  rf="$(_receipt_file)"
  [ -f "$rf" ] || { echo "preflight_not_run"; return 1; }
  v="$(grep -E '^verdict=' "$rf" 2>/dev/null | head -n 1)"; v="${v#*=}"
  [ "$v" = "PASS" ] || { echo "preflight_not_run"; return 1; }
  ts="$(grep -E '^ts=' "$rf" 2>/dev/null | head -n 1)"; ts="${ts#*=}"
  case "$ts" in ''|*[!0-9]*) echo "preflight_not_run"; return 1 ;; esac
  ttl="${HMAD_PREFLIGHT_TTL_SEC:-3600}"
  now="$(date +%s)"
  [ "$(( now - ts ))" -le "$ttl" ] || { echo "preflight_expired"; return 1; }
  # strip through the FIRST '=' only: the value itself contains '='
  fp="$(grep -E '^fingerprint=' "$rf" 2>/dev/null | head -n 1)"; fp="${fp#*=}"
  [ "$fp" = "$(_fingerprint)" ] || { echo "preflight_handles_rotated"; return 1; }
  return 0
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

_agent_pv_re() {
  # Program-banner signature for an agent: strings the AGENT ITSELF prints, which
  # a pane merely *discussing* the agent does not.
  #
  # The bare tokens "codex"/"agy" failed that test and let a coordinator resolve as
  # Codex. A bare `gpt-[0-9]` failed it too, just more narrowly: prose like
  # "comparing gpt-5 output with ours" matched. What Codex actually prints is a
  # product line ("OpenAI Codex (v0.145.0)  model: gpt-5.6-terra") or a status line
  # pairing the model id with a reasoning effort ("gpt-5.6-terra high · ~/repo").
  # Both are structured; neither occurs in ordinary prose about a model.
  case "$1" in
    codex) printf '%s\n' 'openai codex|model: *gpt-|gpt-[0-9][^ ]* +(low|medium|high|xhigh)([^a-z]|$)' ;;
    agy)   printf '%s\n' 'antigravity cli|gemini [0-9]' ;;
    *)     printf '%s\n' "$1" ;;
  esac
}

_agent_proc_name() {
  # h-mad agent token -> the executable name the OS reports for that agent.
  # Kept separate from _orca_agent_type (Orca's `agentType`, "antigravity") and
  # from the token itself, because all three namespaces have already diverged
  # once: token `agy`, agentType `antigravity`, binary `agy`.
  case "$1" in
    *) printf '%s\n' "$1" ;;
  esac
}

_agent_procs_in() {  # $1 agent token, $2 worktree path -> pids, one per line
  # OS-level evidence that an agent is RUNNING in a worktree (J18).
  #
  # `lsof -a -d cwd -c <name>` lists processes whose current directory is open,
  # restricted to that command name; the NAME column (last field) is the cwd.
  # We match it exactly against the worktree path.
  #
  # Deliberately NOT `ps`: `ps -e` was measured returning a PARTIAL process list
  # on this host (1374 pids on one call, 31 on the next, with `ps -p <pid>`
  # finding a process `ps -ax | grep` could not). A liveness check that silently
  # enumerates a subset is worse than none. `lsof` reported both live agents
  # correctly and repeatably.
  #
  # rc 2 = no lsof (no evidence available, distinct from "no process found"),
  # so the caller can stay silent instead of claiming the agent is absent.
  local token="$1" wt="$2" name
  [ -n "$wt" ] || return 2
  command -v lsof >/dev/null 2>&1 || return 2
  name="$(_agent_proc_name "$token")"
  lsof -a -d cwd -c "$name" 2>/dev/null \
    | awk -v w="$wt" 'NR>1 && $NF==w {print $2}' | sort -u
}

_orca_unclaimed_panes() {  # $1 scoped terminals envelope -> handles Orca names nowhere
  # A pane is a J18 candidate only when `worktree ps` agents[] does NOT claim it.
  # A claimed pane already has an authoritative agentType: if it matched the
  # wanted agent the paneKey join would have returned it, so a claimed pane
  # reaching here is provably a DIFFERENT agent. Binding one would re-open the
  # exact silent swap the join was built to close.
  #
  # Claimed-ness is computed across ALL worktrees, not just the scoped one: a
  # paneKey named anywhere is named, and being lenient here would only ever add
  # candidates -- the direction that risks a wrong bind.
  local scoped="$1" ps claimed
  ps="$(orca worktree ps --limit 200 --json 2>/dev/null)" || ps=""
  # `|| claimed=""` for the same `set -e`/pipefail reason as above: an older
  # runtime, a missing verb, or unparseable JSON makes jq non-zero, and that is
  # the expected "no claim data" case, not a fatal error.
  claimed="$(printf '%s' "$ps" | jq -c '[.result.worktrees[]?|(.agents//[])[]|.paneKey]' 2>/dev/null)" || claimed=""
  # No/!unparseable ps => nothing is claimed. That only widens the candidate set,
  # which cannot cause a wrong bind on its own: the bind still requires the set to
  # hold EXACTLY ONE pane, and extra candidates make that condition harder, not
  # easier. Failing the other way (treating everything as claimed) would silently
  # disable the pass on any runtime whose `worktree ps` is unavailable.
  [ -n "$claimed" ] || claimed='[]'
  printf '%s' "$scoped" | jq -r --argjson claimed "$claimed" '
    .result.terminals[]?
    | select((((.tabId // "") + ":" + (.leafId // "")) as $k
              | ($k != ":") and ($claimed | index($k) | not)))
    | .handle' 2>/dev/null
}

_orca_agent_type() {
  # h-mad agent token -> the `agentType` Orca reports in `worktree ps`.
  # Orca names the Antigravity CLI "antigravity"; h-mad calls it "agy" after the
  # binary. Without this alias the J16 join matches nothing for agy and silently
  # degrades to the heuristics it exists to replace.
  case "$1" in
    agy) printf '%s\n' 'antigravity' ;;
    *)   printf '%s\n' "$1" ;;
  esac
}

_orca_find_by_pane() {
  # J16 -- resolve identity by joining `orca worktree ps` to `orca terminal list`.
  # $1 = agent token, $2 = the already-scoped terminals envelope, $3 = scope
  # worktree path (may be empty). Echoes exactly one handle + rc 0, else rc 1.
  #
  # `terminal list` carries no field naming the running program (orca#9870):
  # `.title` is the enclosing TAB's title -- shared by every leaf, so it names a
  # tab, not a pane -- and `.preview` empties once the agent works. But
  # `worktree ps` returns `.result.worktrees[].agents[]` with an explicit
  # `agentType` keyed by a `paneKey` of "<tabId>:<leafId>", and `terminal list`
  # returns `.tabId` and `.leafId`. The join is therefore both title- and
  # preview-independent: it is the missing field, in a different call.
  #
  # Measured live 2026-07-23 at the exact ambiguity H5 documents -- an
  # antigravity pane titled "Codex - skills repo" beside the real Codex pane,
  # both previews reset to empty, both passes below resolving 0 candidates for
  # both agents. The join separated them correctly.
  local token="$1" scoped="$2" scope_wt="$3" want ps ids n
  want="$(_orca_agent_type "$token")"
  # --limit mirrors _worktree_path. Failure (older runtime, no such verb, bad
  # JSON) is not an error here: Pass 0 is an ENRICHMENT, and the caller's
  # heuristics remain the contract when it cannot run.
  ps="$(orca worktree ps --limit 200 --json 2>/dev/null)" || return 1
  printf '%s' "$ps" | jq -e '.result.worktrees' >/dev/null 2>&1 || return 1
  # The cap drops whole WORKTREES, never agents within one, so a same-worktree
  # rival can never be hidden from a scoped match. Unscoped (no coordinator, cwd
  # inside no known worktree) matching is global, and there a dropped worktree
  # could hide the very rival that makes this ambiguous -- so refuse instead.
  if [ -z "$scope_wt" ]; then
    printf '%s' "$ps" | jq -e '.result.truncated != true' >/dev/null 2>&1 || return 1
  fi
  ids="$(printf '%s' "$ps" | jq -r --arg want "$want" --arg wt "$scope_wt" \
           --argjson tl "$scoped" '
    [ .result.worktrees[]?
      | select($wt == "" or (.path // "") == $wt)
      | (.agents // [])[]
      | select((.agentType // "") == $want)
      | .paneKey ] as $keys
    | $tl.result.terminals[]?
    | select(((.tabId // "") + ":" + (.leafId // "")) as $k
             | ($k != ":") and ($keys | index($k)))
    | .handle' 2>/dev/null)" || return 1
  n="$(printf '%s' "$ids" | grep -c . || true)"
  # Exactly one, or decline. Two agents of one type in scope is real ambiguity;
  # falling through to weaker evidence would be guessing with extra steps.
  [ "$n" -eq 1 ] || return 1
  printf '%s\n' "$ids"
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
  if [ -z "$scope_wt" ]; then
    # No coordinator (no ORCA_PANE_KEY, no pin): fall back to the worktree that
    # ENCLOSES the current directory rather than searching every worktree. Going
    # global is the dangerous default -- it is how a HemaSuite pane competes with
    # a skills pane for the same token. cwd is weaker evidence than the
    # coordinator's own pane but far better than none; when cwd is inside no known
    # worktree (stub tests, use outside any checkout) matching stays global.
    scope_wt="$(printf '%s' "$listing" | jq -r --arg cwd "$PWD" '
      [.result.terminals[]? | (.worktreePath // "")
       | select(. != "" and ($cwd == . or ($cwd | startswith(. + "/"))))]
      | sort_by(length) | last // empty' 2>/dev/null || true)"
  fi
  # Candidate set: same worktree as the coordinator (when known), coordinator's
  # own pane always excluded (even in Pass 1 -- its title/preview may carry the
  # token because it renders this conversation).
  scoped="$(printf '%s' "$listing" | jq -c --arg wt "$scope_wt" --arg self "$self" \
    '{result:{terminals:[.result.terminals[]?
       | select($self=="" or .handle != $self)
       | select($wt=="" or (.worktreePath // "")==$wt)]}}')"
  # Pass 0 (J16) -- exact identity via the worktree-ps paneKey join. Runs FIRST
  # because it is the only evidence here that actually names the running program;
  # everything below infers it from strings a pane may carry for other reasons.
  # It declines silently (rc 1) when unavailable or ambiguous, leaving Passes 1
  # and 2 exactly as they were.
  local by_pane
  if by_pane="$(_orca_find_by_pane "$token" "$scoped" "$scope_wt")" && [ -n "$by_pane" ]; then
    printf '%s\n' "$by_pane"; return 0
  fi
  # Pass 1 -- anchored, case-insensitive TITLE match (identity, not content).
  #
  # Only run for agents that actually EMIT a title. Orca's `.title` is the pane
  # program's OSC title when it sets one, and otherwise the enclosing TAB's title
  # -- and a tab title is shared by every leaf in that tab, so it names a tab, not
  # a pane. Two consequences, both observed live on 2026-07-22:
  #
  #   * Codex sets no OSC title. Therefore ANY `.title` matching "^codex" is
  #     necessarily inherited (tab title, or the worktree basename) and carries no
  #     information about what runs in that pane. Matching it is not merely
  #     unreliable, it is meaningless -- an *agy* pane sitting in a tab named
  #     "Codex - skills repo" matched "^codex" and would have been handed Codex's
  #     work. Both agents produce a well-formed sentinel report, so the
  #     mis-dispatch is silent: the wrong model answers and the gate scores it.
  #     Codex therefore skips Pass 1 entirely and relies on the preview signature
  #     or, properly, on a pin/launch.
  #   * agy DOES set an OSC title ("agy --dangerously-skip-permissions"), so its
  #     title is real identity -- except when inherited. A title shared by two or
  #     more leaves of the SAME tab is provably the tab's, so reject it.
  #
  # There is no field distinguishing an OSC title from an inherited one; that is
  # https://github.com/stablyai/orca/issues/9870. Until it exists we use the two
  # available forms of evidence:
  #
  #   a) "shared across leaves of one tab" proves inheritance -- but only when the
  #      tab has more than one leaf. A SINGLE-leaf tab named "agy - worker" proves
  #      nothing, and a Codex pane sitting in one resolved as agy (verified).
  #   b) A rival's PROGRAM BANNER in the preview is strong evidence of what
  #      actually runs there, and strong evidence beats a weak inherited title. A
  #      candidate whose preview carries the other agent's banner is rejected,
  #      which closes (a)'s single-leaf hole: the Codex pane in the "agy - worker"
  #      tab is printing "gpt-5.6-terra high", so it cannot be agy.
  local rival_re=""
  case "$token" in
    codex) rival_re="$(_agent_pv_re agy)" ;;
    agy)   rival_re="$(_agent_pv_re codex)" ;;
  esac
  ids=""
  if [ "$token" != "codex" ]; then
    ids="$(printf '%s' "$scoped" | jq -r --arg t "$token" --arg rival "$rival_re" '
      [.result.terminals[]] as $all
      | $all[]
      | select((.title//"") | test("^" + $t + "([^A-Za-z]|$)"; "i"))
      # Drop titles proven to be tab-inherited: same tabId, same title, >1 leaf.
      | . as $c
      | select([$all[] | select((.tabId//"") != "" and (.tabId//"") == ($c.tabId//"")
                                and (.title//"") == ($c.title//""))] | length < 2)
      # Drop a pane the OTHER agent is demonstrably running.
      | select($rival == "" or ((.preview//"") | test($rival; "i") | not))
      | .handle')"
  fi
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
    # Signatures live in _agent_pv_re: strings the AGENT PROGRAM emits, never
    # words a pane can render while merely talking about the agent. A candidate
    # also carrying the rival's banner is ambiguous, so it is rejected rather than
    # guessed at.
    local pv_re; pv_re="$(_agent_pv_re "$token")"
    ids="$(printf '%s' "$scoped" | jq -r --arg t "$pv_re" --arg rival "$rival_re" \
      '.result.terminals[]
       | select((.preview//"") | test($t; "i"))
       | select($rival == "" or ((.preview//"") | test($rival; "i") | not))
       | .handle')"
    n="$(printf '%s' "$ids" | grep -c . || true)"
    if [ "$n" -eq 1 ]; then printf '%s\n' "$ids"; return 0; fi
  fi
  # Pass 3 (J18) -- OS evidence for panes Orca did not spawn.
  #
  # Reached only when every pass above found nothing, which is the measured state
  # for a pane that survived an Orca restart: absent from agents[] (Pass 0 blind),
  # tab-inherited or skipped title (Pass 1), empty renderer buffer (Pass 2). The
  # agent may nonetheless be very much alive -- two were, for 9 hours.
  #
  # The OS can prove the agent is RUNNING here; it cannot say which PANE holds it
  # (Orca exposes no tty/pid/ptyId -- orca#9870 -- and macOS blocks `ps e`). So
  # bind only when the mapping is FORCED: one candidate pane, and a live process
  # that must therefore be in it. Any other shape reports the evidence and
  # declines, because a wrong bind here is silent -- both agents emit a
  # well-formed report, so the gate would score the wrong model's work.
  local os_pids os_rc cands cn
  # Guarded: under `set -e` a bare `x="$(cmd)"` aborts the moment cmd is non-zero,
  # and BOTH non-zero returns here are normal control flow (rc 2 = no lsof, rc 1 =
  # lsof found no such process). Unguarded, `resolve` died with rc 2 and an empty
  # stderr before it could print any diagnosis at all -- the same trap already
  # documented twice in this file.
  os_rc=0; os_pids="$(_agent_procs_in "$token" "$scope_wt")" || os_rc=$?
  if [ "$os_rc" -eq 0 ] && [ -n "$os_pids" ]; then
    cands="$(_orca_unclaimed_panes "$scoped")"
    cn="$(printf '%s' "$cands" | grep -c . || true)"
    if [ "$cn" -eq 1 ]; then
      echo "[H-MAD] $token: bound $cands by OS evidence (pid $(printf '%s' "$os_pids" | tr '\n' ' ' | sed 's/ $//'); sole pane in $scope_wt that \`worktree ps\` does not name)" >&2
      printf '%s\n' "$cands"; return 0
    fi
    # Live agent, but the pane is not determined. Say exactly that -- the message
    # this replaces ("resolved to 0 candidates") reads as "no agent is running",
    # which was measurably false and sent the operator looking in the wrong place.
    {
      printf '[H-MAD] %s: %s process IS live in %s (pid %s), but %s pane(s) there carry no identifying evidence:\n' \
        "$token" "$token" "$scope_wt" "$(printf '%s' "$os_pids" | tr '\n' ' ' | sed 's/ $//')" "$cn"
      # Every line carries the [H-MAD] prefix on purpose: `env` replays only
      # prefixed lines (the generic candidate-count noise stays suppressed), so
      # an indented continuation line would be filtered out and the operator
      # would be told candidates exist without being told which.
      # '%s\n', not '%s': command substitution stripped the trailing newline from
      # $cands, so the last handle ran into the following line ("term_7d59…[H-MAD]
      # codex: Orca names none of them") -- observed live before this fix.
      printf '%s\n' "$cands" | sed "s/^/[H-MAD] $token:     /"
      printf '[H-MAD] %s: Orca names none of them (absent from `worktree ps` agents[]) and their previews are empty,\n' "$token"
      printf '[H-MAD] %s: so the pane cannot be inferred. Pin it explicitly:\n' "$token"
      printf '[H-MAD] %s:   hmad-dispatch pin %s <handle>\n' "$token" "$token"
    } >&2
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
  # J2: name the pin file. Reading the wrong project's pins used to be silent --
  # it surfaced only as a puzzling UNRESOLVED, with no hint that the answer came
  # from another repo. This is the line an operator already reads before a run.
  [ "$sub" = "orca" ] && echo "pin file: $(_pin_file)"
  local a t _id stale="" seen_codex="" seen_agy="" conflict_handle="" verdict="PASS" fields=""
  local unresolved="" orch_on=1
  # J18: resolution stderr was discarded wholesale, which also discarded the OS
  # evidence pass's report -- the one place that can say "the agent IS running,
  # here is its pid, here are the panes it could be in". Capture instead of
  # suppress, and replay only the `[H-MAD]` lines: the generic
  # "resolved to N candidates" noise (prefix `hmad-dispatch:`) stays hidden, so
  # `env` output is unchanged for every case that has nothing new to say.
  local _rerr; _rerr="$(mktemp)"
  for a in codex agy; do
    if t="$(_resolve_target "$a" 2>"$_rerr")"; then
      case "$a" in codex) seen_codex="$t" ;; agy) seen_agy="$t" ;; esac
      # A pin file records intent, not state. `env` is the preflight an operator
      # reads before committing a run, so a handle whose pane is gone must not
      # print as if it were addressable -- a dispatch into one vanishes with no
      # error, no report, and no work done.
      if [ "$sub" = "orca" ] && { _orca_handle_live "$t"; [ $? -eq 1 ]; }; then
        echo "$a -> $t STALE (no such terminal — re-pin or relaunch)"
        stale="${stale:+$stale }$a"
      else
        echo "$a -> $t"
        # TUI-independent identity, from the paneKey join (never preview/cursor).
        # Lets an operator confirm the pin lands on the right program WITHOUT a
        # `terminal read` -- which reads empty for a live full-screen TUI and has
        # been misread as a wrong pin. Best-effort; absent when ps is unreadable.
        _id="$(_orca_identity "$t" 2>/dev/null || true)"
        [ -n "$_id" ] && echo "        id: $_id"
      fi
    else
      echo "$a -> UNRESOLVED"
      unresolved="${unresolved:+$unresolved,}$a"
    fi
    grep '^\[H-MAD\]' "$_rerr" >&2 || true
    : > "$_rerr"
  done
  rm -f "$_rerr"
  [ -z "$stale" ] || echo "stale pins: $stale"
  # Two agents cannot be the same pane, so identical handles prove at least one
  # resolution is wrong -- and that is exactly the shape a tab-inherited title
  # produces (one pane whose tab name matches one agent while it runs the other).
  # Free to detect, and it catches inheritance cases no single-agent check can.
  if [ -n "$seen_codex" ] && [ "$seen_codex" = "$seen_agy" ]; then
    conflict_handle="$seen_codex"
    echo "CONFLICT: codex and agy both resolve to $seen_codex — at least one is wrong; pin them explicitly"
  fi
  if _orchestration_active; then
    orch_on=0
    echo "orchestration: on"
    # Report the Run binding too. `orchestration: on` alone was misleading: it means
    # substrate+coordinator are present, which says nothing about whether a Run is
    # bound — and with no Run every mutation fails `run_required`. Read-only here;
    # task-create binds on demand. "(none — will bind on task-create)" is the normal
    # pre-flow state, not a fault.
    if [ "$sub" = "orca" ]; then
      # `|| _rid=""` is load-bearing: _run_bound returns 1 for "unbound" and 2 for
      # "probe failed", and under `set -e` a bare assignment would abort `env`
      # outright — turning a diagnostic command into a hard failure exactly when
      # you are running it to diagnose something.
      local _rid; _rid="$(_run_bound 2>/dev/null)" || _rid=""
      echo "orchestration run: ${_rid:-(none — will bind on task-create)}"
    fi
  else
    echo "orchestration: off"
  fi
  # PREFLIGHT verdict — the machine-consumable form of the STALE/CONFLICT lines above.
  # A FAIL is something an orchestrator must ACT on.
  #
  # An UNRESOLVED agent used to be exempt on the grounds that it "is not a failure,
  # it is an ordinary un-set-up session". That holds only while nothing is about to
  # dispatch. Measured live 2026-08-03: `PREFLIGHT: PASS` printed with BOTH agents
  # UNRESOLVED in a session whose coordinator and Run were bound — i.e. a session
  # one step from dispatching, with nowhere to dispatch to. A preflight that passes
  # there is not reporting readiness, it is withholding the one fact that matters.
  #
  # So the exemption is kept exactly where its reasoning applies: `_orchestration_active`
  # (orca AND a coordinator resolves) separates "wired up, about to dispatch" from
  # "ordinary un-set-up session". Unresolved agents FAIL only in the former.
  #
  # This MUST NOT become a non-zero exit. A non-zero exit registers as a Claude Code
  # PostToolUseFailure and leaks into coexisting plugins' error handling, which is why
  # invariants.base.md §"Audit-gate signal discipline" reserves non-zero for genuine
  # operational errors only (here: the no-substrate early return above). GATE: and
  # ASSEMBLE: follow the same rule. Strengthen this signal by mandating a READ of the
  # token, never by changing $?.
  [ -z "$stale" ] || { verdict="FAIL"; fields=" stale=$(printf '%s' "$stale" | tr ' ' ',')"; }
  [ -z "$conflict_handle" ] || { verdict="FAIL"; fields="$fields conflict=$conflict_handle"; }
  if [ -n "$unresolved" ] && [ "$orch_on" -eq 0 ]; then
    verdict="FAIL"; fields="$fields unresolved=$unresolved"
  fi
  echo "PREFLIGHT: ${verdict}${fields}"
  if [ "$verdict" = "PASS" ]; then _receipt_write; else _receipt_clear; fi
  return 0
}

_cmd_resolve() {
  # resolve <agent> — print the resolved handle/surface for ONE agent
  # (codex|agy) to stdout and exit 0; empty stdout + stderr diagnostic + exit 1
  # when UNRESOLVED; empty stdout + stderr message + exit 2 for an unknown or
  # missing agent. Single-agent form of what `env` computes for both; delegates
  # to _resolve_target so the two cannot diverge.
  # `--verify` additionally requires the resolved handle to be a live terminal,
  # i.e. it behaves as `verify`. The default stays unverified on purpose: a pin's
  # value is that it depends on no listing, which is what lets it survive the
  # auto-detect decay it exists to replace.
  local agent="${1:-}"
  case "$agent" in
    --verify) _cmd_verify "${2:-}"; return $? ;;
  esac
  case "${2:-}" in
    --verify) _cmd_verify "$agent"; return $? ;;
  esac
  _resolve_target "$agent"
}

_cmd_verify() {
  # verify <agent> — resolve, then confirm the handle still names a live pane.
  #
  # `resolve` deliberately does NOT do this. A pin's whole value is that it costs
  # nothing and depends on no listing: it is what survives when auto-detect
  # cannot see the pane at all, so making resolution contingent on a successful
  # `orca terminal list` would put the fallback back under the failure it exists
  # to survive. But that means `resolve` echoes a pinned handle it has never
  # checked -- a fabricated or dead pin prints happily with exit 0.
  #
  # In practice every consumer catches it: send/read/alive each exit 1 with
  # `terminal_handle_stale`. This verb closes the reporting gap for callers that
  # want to know BEFORE dispatching (and for stale pin files left by a crashed
  # run, which otherwise surface only as a mid-run failure).
  #
  # Exit: 0 live, 1 unresolved or stale, 2 unknown agent.
  local agent="${1:-}" target sub rc
  case "$agent" in codex|agy) ;; *) echo "hmad-dispatch: unknown agent '$agent' (codex|agy)" >&2; return 2 ;; esac
  target="$(_resolve_target "$agent")" || return 1
  sub="$(_detect_substrate)" || return 1
  if [ "$sub" != "orca" ]; then printf '%s\n' "$target"; return 0; fi
  # Guarded: under `set -e` a bare `cmd; rc=$?` aborts the script the moment cmd
  # returns non-zero, which is exactly the case this verb exists to report.
  rc=0; _orca_handle_live "$target" || rc=$?
  case "$rc" in
    0) printf '%s\n' "$target"; return 0 ;;
    2) echo "hmad-dispatch: cannot verify '$agent' — 'orca terminal list' unreadable" >&2; return 1 ;;
  esac
  echo "hmad-dispatch: stale_pin — '$agent' resolves to $target, which is not a live terminal; re-pin (hmad-dispatch pin $agent <handle>) or relaunch (hmad-dispatch launch $agent)" >&2
  return 1
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
    if [ -n "${!var:-}" ]; then
      handle="${!var}"
      # An auto-detected handle came out of the listing and is live by
      # construction; an operator-supplied env pin did not, and pinning a handle
      # that is already dead just defers the failure to the first dispatch.
      if [ -n "$handle" ] && { _orca_handle_live "$handle"; [ $? -eq 1 ]; }; then
        echo "[H-MAD] pin-agents: $var=$handle is not a live terminal — ignoring it" >&2
        handle=""
      fi
    else
      handle="$(_orca_find "$a" 2>/dev/null || true)"
    fi
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
  # Auto-detect can't identify Codex at all by title -- Codex emits no OSC title,
  # so any `.title` matching it was inherited from the tab -- and `orca terminal
  # rename` does NOT change the `.title` that resolution reads. An explicit handle
  # pin is the only reliable identity (H4/H5).
  _require_orca pin || return $?
  local force=""
  case "${1:-}" in --force) force=1; shift ;; esac
  _need "${1:-}" agent || return $?; _need "${2:-}" handle || return $?
  case "$1" in codex|agy) ;; *) echo "hmad-dispatch: unknown agent '$1' (codex|agy)" >&2; return 2 ;; esac
  # Pinning is the moment identity is supposed to be known, so it is the cheapest
  # place to catch a wrong handle -- otherwise the mistake is discovered much
  # later as a dispatch that silently goes nowhere. Only a readable listing that
  # lacks the handle blocks the pin; `--force` covers pinning a pane that does not
  # exist yet.
  if [ -z "$force" ] && { _orca_handle_live "$2"; [ $? -eq 1 ]; }; then
    echo "hmad-dispatch: refusing to pin $1 -> $2 — no such terminal in 'orca terminal list'. Check the handle, or pass --force to pin it anyway." >&2
    return 1
  fi
  local pf; pf="$(_pin_file)"; local dir; dir="$(dirname "$pf")"; [ -d "$dir" ] || mkdir -p "$dir"
  local tmp; tmp="$(mktemp)"
  [ -f "$pf" ] && { grep -vE "^$1=" "$pf" >> "$tmp" 2>/dev/null || true; }
  printf '%s=%s\n' "$1" "$2" >> "$tmp"
  mv "$tmp" "$pf"
  echo "[H-MAD] pinned $1 -> $2 ($pf)" >&2
}

_cmd_launch() {  # <agent> [--worktree <sel>] [--focus]
  # H5 durable path: h-mad OWNS the agent launch, so its identity is captured at
  # spawn from the create response (`.result.terminal.handle`) — never from the
  # decaying title/preview — and pinned immediately. Zero manual step. Use this
  # to start a fresh Codex/agy for a run; reuse an operator-launched pane via
  # `pin`/`pin-agents` instead. The launch command is overridable per agent.
  _require_orca launch || return $?
  _need "${1:-}" agent || return $?
  local agent="$1"; shift
  case "$agent" in codex|agy) ;; *) echo "hmad-dispatch: unknown agent '$agent' (codex|agy)" >&2; return 2 ;; esac
  local wt="active" focus="" cmd
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;; --focus) focus="--focus"; shift ;; *) _unknown_opt launch "$1"; return $? ;; esac; done
  case "$agent" in
    codex) cmd="${HMAD_ORCA_CODEX_LAUNCH_CMD:-codex}" ;;
    agy)   cmd="${HMAD_ORCA_AGY_LAUNCH_CMD:-agy --dangerously-skip-permissions}" ;;
  esac
  local args=(terminal create --worktree "$wt" --command "$cmd" --title "$agent" --json)
  [ -n "$focus" ] && args+=("$focus")
  # J1: `.result.terminal.handle` is NOT the handle the pane ends up with. It is
  # a pre-adoption placeholder -- confirmed three times, most recently by a direct
  # probe where create said term_d1f7a348…, the pane was term_f0966e2b…, and the
  # create handle never appeared in `terminal list` at all. Pinning it made every
  # later dispatch vanish into a handle that did not exist (the 912b93a liveness
  # check caught it, so launch always failed loud and could not pin).
  #
  # `paneKey` from the SAME response is stable, and is the `<tabId>:<leafId>` J16
  # already joins on. So: create, then resolve the real handle from `terminal
  # list` by that key. Identity is still owned at spawn -- it is just read from
  # the field that survives adoption.
  local resp pane_key handle
  resp="$(_orca_json '.result.terminal | tojson' "${args[@]}")" || return $?
  pane_key="$(printf '%s' "$resp" | jq -r '.paneKey // empty' 2>/dev/null)"
  if [ -z "$pane_key" ]; then
    echo "hmad-dispatch: launch $agent — create response carries no paneKey, so the pane cannot be identified; nothing was pinned. The create-response handle is a pre-adoption placeholder (J1) and must not be pinned. Pin manually after confirming the pane: hmad-dispatch pin $agent <handle>" >&2
    return 1
  fi
  # Adoption is not instantaneous; a live probe resolved in under 5s.
  local deadline=$(( $(date +%s) + ${HMAD_LAUNCH_RESOLVE_TIMEOUT:-20} ))
  while :; do
    handle="$(orca terminal list --json 2>/dev/null \
      | jq -r --arg k "$pane_key" \
          '.result.terminals[]? | select(((.tabId//"")+":"+(.leafId//"")) == $k) | .handle' \
          2>/dev/null | head -1)"
    [ -n "$handle" ] && break
    [ "$(date +%s)" -ge "$deadline" ] && break
    sleep 1
  done
  if [ -z "$handle" ]; then
    echo "hmad-dispatch: launch $agent — paneKey $pane_key did not appear in 'orca terminal list' within ${HMAD_LAUNCH_RESOLVE_TIMEOUT:-20}s; the pane may not have started. Nothing was pinned." >&2
    return 1
  fi
  _cmd_pin "$agent" "$handle" >/dev/null || { echo "hmad-dispatch: launch $agent — pin failed" >&2; return 1; }
  printf '%s\n' "$handle"
  echo "[H-MAD] launched $agent -> $handle (resolved via paneKey $pane_key, pinned)" >&2
}

_cmd_task_create() {  # $1 label, $2 specfile
  _require_orca task-create || return $?
  _need "${1:-}" label || return $?; _need "${2:-}" specfile || return $?
  [ -f "$2" ] || { echo "hmad-dispatch: spec file not found: $2" >&2; return 2; }
  local coord spec
  coord="$(_coordinator)" || return 1
  # Bind a Run before the first mutation of the flow. Without this the CLI rejects
  # task-create with `run_required` and the whole structured path dies here.
  _run_ensure >/dev/null || return $?
  spec="[H-MAD] worker_done coordinator handle (use as --to): ${coord}

$(cat "$2")"
  # Real shape is .result.task.id; legacy flat keys kept as fallbacks. NEVER
  # fall through to the envelope .id -- that is a per-request correlation uuid
  # that always exists, so it silently yields a plausible but useless id.
  _orca_json '.result.task.id // .result.taskId // .taskId' \
    orchestration task-create --spec "$spec" --task-title "$1" --json
}

_cmd_dispatch() {  # $1 agent, $2 task_id
  # J22: this verb deliberately does NOT pre-flight pane readiness. Measured
  # 2026-08-03 (Orca 1.4.164): `--inject` into a pane with no agent CLI is
  # refused ATOMICALLY -- non-zero exit, stdout empty, and `dispatch-show --task`
  # afterwards returns `dispatch: null`. No task row, no terminal binding,
  # nothing to clean up, pane still free for a later dispatch. Orca's message
  # names the terminal, the cause, and both remedies.
  #
  # A wrapper-side check could only make things worse on three counts: it opens
  # a TOCTOU window the atomic path does not have (the agent can exit between
  # check and dispatch); it would have to re-derive "is an agent here" from
  # signals separately proven unreliable -- `terminal read` yields 0 lines for an
  # idle restart-surviving pane (docs/orca-bug-terminal-read-empty-after-restart.md)
  # and hand-started panes are absent from `worktree ps`'s `agents[]` -- so it
  # would false-refuse healthy panes, the exact call `_orca_find` Pass 3 already
  # declines to make; and it protects no state, because there is none to protect.
  #
  # The readiness failure that DOES bite is a different one a pre-flight cannot
  # catch either: an agent that is present but still booting passes detection and
  # swallows the prompt. That is what the J19 `injected=false` guard below and
  # report-file completion are for -- never the launch response.
  #
  # The reliance is pinned by test_dispatch_surfaces_the_agentless_refusal_intact,
  # which asserts the message CONTENT, not just the exit code (mutation-verified
  # ALL_CAUGHT 5/5, including two mutations that keep exit+stream and strip only
  # the text). If that test is ever weakened, this decision is void.
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
  local resp
  resp="$(_orca_json '.' orchestration dispatch --task "$2" --to "$target" --inject --return-preamble --json)" || return $?
  # J19: `ok:true` is not delivery. Measured 2026-08-03: a dispatch can return
  # ok:true, status:"dispatched", `injected:false` and exit 0 — the task row is
  # created and the worker is never told, so `await` sits until timeout with no
  # diagnostic. We always pass --inject, so this is a latent guard rather than a
  # live bug; it costs one jq and converts a silent no-op into a loud failure.
  #
  # Explicit `false` ONLY. An older runtime that omits the field must keep
  # working — treating absent as false would break every such dispatch.
  # `has()`, NOT `//`. jq's alternative operator treats FALSE as null-ish, so
  # `.result.injected // "absent"` yields "absent" for exactly the value we are
  # hunting — the guard silently never fired (caught by its own test).
  if [ "$(printf '%s' "$resp" | jq -r '
        if (.result? | objects | has("injected")) then (.result.injected | tostring)
        elif (. | objects | has("injected")) then (.injected | tostring)
        else "absent" end' 2>/dev/null)" = "false" ]; then
    echo "hmad-dispatch: dispatch of $2 to $target returned injected=false — the task row exists but the worker was NOT given the prompt; await would time out. Re-dispatch after confirming the pane accepts input." >&2
    return 1
  fi
  printf '%s\n' "$resp"
}

_await_cache_dir() {  # where reports acked off the queue are parked
  printf '%s\n' "${HMAD_AWAIT_CACHE_DIR:-$(dirname "$(_pin_file)")/await-cache}"
}

_await_cache_put() {  # $1 = a `check` envelope — park every worker_done it carries
  # J19: acking a delivery to advance the queue DISCARDS every message in it,
  # not just the ones we looked at. Measured live: a 2-message batch acked to
  # `count: 0`, and `await <the other task>` then timed out for a module that had
  # genuinely reported. In a fanout modules finish in one order and are awaited
  # in another, so this is the normal path, not an edge case.
  #
  # The ack is still mandatory (an un-acked delivery replays forever), so the
  # fix is to park the reports BEFORE they are acked away, keyed by task id.
  local dir; dir="$(_await_cache_dir)"
  mkdir -p "$dir" 2>/dev/null || return 0   # best-effort: never fail an await
  printf '%s' "$1" | jq -c 'def pl: (.payload // {})
                              | if type == "string" then (fromjson? // {}) else . end
                              | if type == "object" then . else {} end;
      (.result.messages // .messages // [])[]?
      | select((.type // "") == "worker_done")
      | {k: ((pl | .taskId) // .taskId // .["task-id"] // empty),
         # J20: a lifecycle-REJECTED report is never parked as a valid one --
         # that would launder a rejection into a later await success. J21: it is
         # parked SEPARATELY instead of dropped, because it carries the only
         # explanation of why this module will never report, and whoever awaits
         # first would otherwise ack that explanation off the queue for good.
         rej: (pl | has("_orcaLifecycleRejection")),
         why: (pl | ._orcaLifecycleRejection // null),
         m: .}
      | select(.k != null)' 2>/dev/null \
  | while IFS= read -r row; do
      local key rej; key="$(printf '%s' "$row" | jq -r '.k' 2>/dev/null)" || continue
      # Guard the filename: a task id is `task_<hex>`, but never build a path out
      # of unvalidated remote input.
      case "$key" in ''|*/*|*..*) continue ;; esac
      rej="$(printf '%s' "$row" | jq -r '.rej' 2>/dev/null)"
      if [ "$rej" = "true" ]; then
        printf '%s' "$row" | jq -c '.why' > "$dir/$key.rejected.json" 2>/dev/null || true
      else
        printf '%s' "$row" | jq -c '.m' > "$dir/$key.json" 2>/dev/null || true
      fi
    done
  return 0
}

_await_rejection_take() {  # $1 task_id — echo a parked rejection and consume it
  local f; f="$(_await_cache_dir)/$1.rejected.json"
  [ -f "$f" ] || return 1
  cat "$f" || return 1
  rm -f "$f"
  return 0
}

_await_report_rejection() {  # $1 task_id, $2 rejection JSON — explain and remedy
  local code reason
  code="$(printf '%s' "$2" | jq -r '.code // "unknown"' 2>/dev/null)"
  reason="$(printf '%s' "$2" | jq -r '.reason // ""' 2>/dev/null)"
  echo "[H-MAD] await: the runtime REJECTED $1's worker_done (${code})${reason:+: $reason}" >&2
  echo "[H-MAD] await: the worker DID report — Orca refused the report, so waiting longer cannot help." >&2
  case "$code" in
    missing_dispatch_id)
      echo "[H-MAD] await: the callback omitted --dispatch-id. The <ctx-id> is in the dispatch preamble Orca injects; see references/orchestration-mode.md §Worker identity resolution." >&2 ;;
    sender_not_assignee)
      echo "[H-MAD] await: the callback came from a terminal that is not the dispatch's assignee. It must be sent FROM the dispatched pane." >&2 ;;
  esac
}

_await_cache_take() {  # $1 task_id — echo a parked report and consume it, else rc 1
  local f; f="$(_await_cache_dir)/$1.json"
  [ -f "$f" ] || return 1
  cat "$f" || return 1
  rm -f "$f"
  return 0
}

_cmd_await() {  # $1 task_id, [--timeout <s>]
  _require_orca await || return $?
  _need "${1:-}" task_id || return $?
  local task="$1"; shift
  local timeout=600
  while [ $# -gt 0 ]; do case "$1" in --timeout) timeout="$2"; shift 2 ;; *) _unknown_opt await "$1"; return $? ;; esac; done
  # J19: a report parked by an earlier await (which had to ack it off the queue
  # to advance) is served from the cache. Checked FIRST — the queue no longer has
  # it, so going to the runtime for it would time out on work that is finished.
  local cached
  if cached="$(_await_cache_take "$task")" && [ -n "$cached" ]; then
    printf '%s\n' "$cached"; return 0
  fi
  local coord; coord="$(_coordinator)" || return 1
  # Guard the check response through _orca_json first ('.' re-emits the whole
  # envelope, ok-checked), THEN run the worker_done filter. A raw pipe swallowed
  # an exit-0 "ok":false as `[]` → empty match → indistinguishable from "no
  # worker_done yet" → silent timeout (F11 scope, extended to the raw verbs).
  #
  # A coordinator `check` returns the bound Run's OLDEST UNACKNOWLEDGED Delivery
  # and REPLAYS that exact batch until `--ack <delivery_id>` — stated by both the
  # orchestration guide (§Messaging: "replays that exact batch until --ack") and
  # `orca orchestration check --help` ("default: return the bound Run's oldest
  # unacknowledged FIFO batch"). A single un-acked call is therefore NOT a wait:
  # once any delivery is outstanding, every later check returns that same stale
  # batch immediately. In a Phase-5 fanout (up to HMAD_ORCA_MAX_WORKTREES
  # concurrent modules, each awaited in turn) modules 2..N got module 1's batch
  # back at once, the taskId filter missed, and the old `jq '.[0] // empty'`
  # exited 0 on an empty match — so a worker that had NOT reported read as a
  # successful await. That is a false completion, the worst failure a gate can
  # have. So: loop to an absolute deadline, ack each batch once inspected, and
  # exit NON-ZERO on timeout instead of echoing nothing and returning 0.
  local deadline=$(( SECONDS + timeout ))
  # J21: a rejection seen for OUR task explains the whole wait. Remember it and
  # report it at the end rather than failing fast — a worker may resend a valid
  # callback after a rejected attempt (measured: both in one batch), so the
  # rejection is a diagnosis for the timeout path, not a reason to stop waiting.
  local our_rejection="" rejection_reported=0
  our_rejection="$(_await_rejection_take "$task" 2>/dev/null || true)"
  if [ -n "$our_rejection" ]; then
    # Say it NOW, not at the timeout. An earlier await already parked this, so
    # the runtime refused this task's report before we even started waiting --
    # and the loop below has three exits that never reach the timeout block
    # (replay-stuck, unackable batch, empty-batch break). Reporting only there
    # left a cache-only rejection silent on exactly those paths.
    _await_report_rejection "$task" "$our_rejection"
    rejection_reported=1
  fi
  local ack="" checked match count remaining
  while :; do
    remaining=$(( deadline - SECONDS ))
    [ "$remaining" -gt 0 ] || break
    local args=(orchestration check --terminal "$coord")
    # `check --ack <id> --wait` acknowledges, checks, and waits in one call, so
    # the ack rides along with the next wait rather than costing a round trip.
    [ -n "$ack" ] && args+=(--ack "$ack")
    args+=(--wait --types worker_done --timeout-ms "$(( remaining * 1000 ))" --json)
    checked="$(_orca_json '.' "${args[@]}")" || return $?
    match="$(printf '%s' "$checked" \
      | jq -c --arg t "$task" '
          def pl: (.payload // {})
                  | if type == "string" then (fromjson? // {}) else . end
                  | if type == "object" then . else {} end;
          (.result.messages // .messages // [])
          # J20: Orca lifecycle-validates worker_done and can REJECT one while
          # still delivering it here (observed: missing_dispatch_id,
          # sender_not_assignee). The runtime refused the report, so the module
          # did not report -- matching it would be a false completion.
          | map(select((pl | has("_orcaLifecycleRejection")) | not))
          | map(select(((pl | .taskId) // .taskId // .["task-id"]) == $t))
          | .[0] // empty')"
    if [ -n "$match" ]; then printf '%s\n' "$match"; return 0; fi
    count="$(printf '%s' "$checked" | jq -r '(.result.messages // .messages // []) | length')"
    # Empty batch ⇒ `--wait` blocked the whole remaining window and no worker_done
    # arrived, so the deadline is spent: break to the timeout path. Do NOT `continue`
    # here — a CLI (or stub) that returns empty immediately instead of blocking would
    # turn that into a hot spin for the full timeout. Breaking fails CLOSED: worst case
    # is a spurious timeout, which is the correct bias for a gate (cf. gate-wait).
    [ "${count:-0}" -gt 0 ] || break
    # Non-empty batch with no match for OUR task — it belongs to a sibling module.
    # Park every report in it BEFORE acking, because the ack destroys them all
    # (J19, see _await_cache_put). Best-effort by design: a cache failure must
    # degrade to the previous lossy behaviour, never abort a live await.
    _await_cache_put "$checked" || true
    # A rejection for OUR task in this batch: capture it before the ack, and
    # before _await_cache_put's copy is consumed by anyone else.
    if [ -z "$our_rejection" ]; then
      our_rejection="$(printf '%s' "$checked" | jq -c --arg t "$task" '
        def pl: (.payload // {})
                | if type == "string" then (fromjson? // {}) else . end
                | if type == "object" then . else {} end;
        [ (.result.messages // .messages // [])[]?
          | select(((pl | .taskId) // .taskId // .["task-id"]) == $t)
          | (pl | ._orcaLifecycleRejection)
          | select(. != null) ] | .[0] // empty' 2>/dev/null || true)"
      # We just took it out of the batch; drop the parked copy so a later await
      # for this task does not report a rejection this one already owns.
      if [ -n "$our_rejection" ]; then
        _await_rejection_take "$task" >/dev/null 2>&1 || true
        # Report the MOMENT it is known, not only on the timeout path: this loop
        # has three other non-zero exits (replay-stuck, unackable batch, and the
        # empty-batch break), and a diagnosis that only prints on one of them is
        # the same silence this change exists to remove. Caught by its own test —
        # the replay-stuck exit swallowed it.
        _await_report_rejection "$task" "$our_rejection"
        rejection_reported=1
      fi
    fi
    # Ack it so the next check advances past it.
    #
    # OBSERVED LIVE 2026-08-03 (this comment previously said the field "could not
    # be observed live" — it needs a bound Run AND pending mail, which a full
    # orchestration e2e finally produced). The real envelope is:
    #
    #   {"result":{"runId":…,"deliveryId":"delivery_5ac615390583","count":1,
    #              "replayed":true,"acknowledged":null,"timedOut":false,
    #              "cancelled":false,"connectionLost":false,"mutation":{…},
    #              "messages":[…]}}
    #
    # So `.result.deliveryId` is the real key and leads the chain. `replayed:true`
    # confirms the replay semantics this loop is built around, and `--ack` drains
    # the queue (count 1 -> 0, `acknowledged` echoing the id).
    #
    # The remaining keys stay as version tolerance, NOT as equal candidates: they
    # are unobserved spellings kept cheap against an older/newer runtime. Note the
    # snake_case `delivery_id` was the guess every test pinned before this, so the
    # suite covered only the spelling Orca does not send.
    local prev="$ack"
    ack="$(printf '%s' "$checked" | jq -r '
      .result.deliveryId // .result.delivery_id // .result.delivery.id
      // .deliveryId // .delivery_id // empty')"
    if [ -n "$prev" ] && [ "$ack" = "$prev" ]; then
      # We already acked this exact delivery and got it back. The ack is not
      # advancing the queue, so every further iteration is a hot spin that would
      # end in a misleading plain timeout. Stop and name the stuck id.
      echo "[H-MAD] await: delivery ${ack} replayed after --ack (task=$task); the queue is not advancing." >&2
      return 1
    fi
    if [ -z "$ack" ]; then
      # Cannot ack ⇒ the identical batch replays forever. Spinning here would burn
      # the whole timeout re-reading one stale delivery and then report a plain
      # timeout, hiding the real cause. Fail LOUD with the shape we actually got.
      echo "[H-MAD] await: delivery of ${count} message(s) carried no recognisable ack id (task=$task)." >&2
      echo "[H-MAD] await: without --ack this batch replays forever; check the response shape:" >&2
      printf '%s' "$checked" | jq -c '.result | keys' >&2 2>/dev/null || true
      return 1
    fi
  done
  # J21: name the rejection FIRST when there is one. "no matching worker_done"
  # alone says the module never reported; a rejection says it did and the runtime
  # refused it — opposite fixes, and only one of them is waiting longer.
  if [ -z "$our_rejection" ]; then
    our_rejection="$(_await_rejection_take "$task" 2>/dev/null || true)"
  fi
  if [ -n "$our_rejection" ] && [ "$rejection_reported" -eq 0 ]; then
    _await_report_rejection "$task" "$our_rejection"
  fi
  echo "[H-MAD] await timed out after ${timeout}s (task=$task; no matching worker_done)" >&2
  return 1
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
    *) _unknown_opt gate-wait "$1"; return $? ;; esac; done
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

_cmd_worktree_create() {  # <name> [--agent <id>] [--base <ref>] [--prompt-file <path>] [--repo <sel>|--project <id>]
  # NOTE: no --workspace here. `orca automations create` accepts --workspace (and
  # --workspace-mode), but `orca worktree create` does NOT -- its full option set is
  # --repo/--project/--project-host-setup/--host for targeting. Forwarding --workspace
  # made the CLI reject the whole create. Verified by enumerating both --help surfaces.
  _require_orca worktree-create || return $?
  _need "${1:-}" name || return $?
  local name="$1"; shift
  local agent="" base="" pf="" repo="" proj="" setup="run"
  while [ $# -gt 0 ]; do case "$1" in
    --agent) agent="$2"; shift 2 ;; --base) base="$2"; shift 2 ;;
    --prompt-file) pf="$2"; shift 2 ;;
    --repo) repo="$2"; shift 2 ;; --project) proj="$2"; shift 2 ;;
    --setup) setup="$2"; shift 2 ;;
    *) _unknown_opt worktree-create "$1"; return $? ;; esac; done
  local args=(worktree create --name "$name")
  [ -n "$agent" ] && args+=(--agent "$agent")
  [ -n "$base" ] && args+=(--base-branch "$base")
  [ -n "$repo" ] && args+=(--repo "$repo")
  [ -n "$proj" ] && args+=(--project "$proj")
  # --setup defaults to `run`, not to the CLI's own default. The CLI default is
  # `inherit`, which follows the REPO's setup policy -- so whether a fanout worker
  # gets a prepared tree depends on a per-repo Orca setting this wrapper does not
  # control. Every repo on the current host happens to be `run-by-default`, so this
  # is not a live bug; it is the latent one where a repo configured otherwise starts
  # a worker in an unprepared checkout and the coordinator only sees the failure
  # downstream. The orchestration guide says to pass `run` for every new worktree and
  # to use skip/inherit "only when there is a concrete task-specific reason" -- which
  # is what the explicit `--setup <policy>` override is for.
  args+=(--setup "$setup")
  if [ -n "$pf" ]; then
    [ -f "$pf" ] || { echo "hmad-dispatch: prompt file not found: $pf" >&2; return 2; }
    args+=(--prompt "$(cat "$pf")")
  fi
  args+=(--json)

  local sel rc=0
  sel="$(_orca_json '.result.worktree.id // .result.worktree.selector // .result.worktree.handle' "${args[@]}")" || rc=$?
  [ $rc -eq 0 ] || return $rc
  [ -n "$sel" ] && printf '%s\n' "$sel"

  if [ -n "$pf" ]; then
    local tid
    if tid="$(_cmd_task_create "worktree:$name" "$pf" 2>/dev/null)" && [ -n "$tid" ]; then
      echo "[H-MAD] worktree_task task=$tid selector=$sel" >&2
    else
      echo "[H-MAD] worktree_task_skipped selector=$sel" >&2
    fi
  fi
  return 0
}

_cmd_worktree_current() {  # (no args)
  _require_orca worktree-current || return $?
  _orca_json '.result | tojson' worktree current --json
}

_cmd_worktree_ps() {  # [--limit <n>]
  _require_orca worktree-ps || return $?
  local args=(worktree ps)
  while [ $# -gt 0 ]; do case "$1" in --limit) args+=(--limit "$2"); shift 2 ;; *) _unknown_opt worktree-ps "$1"; return $? ;; esac; done
  args+=(--json)
  _orca_json '.result | tojson' "${args[@]}"
}

# `list` is NOT an alias for `ps`. `ps` is a compact orchestration summary; `list`
# carries the full worktree records -- including `childWorktreeIds` and `lineage`,
# which is what a resume needs to recover where a parked item actually lives. The
# handoff skill required exactly that field and, with no verb exposing it, had to
# prescribe a raw `orca worktree list` in violation of its own "all Orca access
# goes through hmad-dispatch" rule.
_cmd_worktree_list() {  # [--limit <n>]
  _require_orca worktree-list || return $?
  local args=(worktree list)
  while [ $# -gt 0 ]; do case "$1" in --limit) args+=(--limit "$2"); shift 2 ;; *) _unknown_opt worktree-list "$1"; return $? ;; esac; done
  args+=(--json)
  _orca_json '.result | tojson' "${args[@]}"
}

# Selector -> filesystem path, or empty when it cannot be resolved to exactly one
# existing directory. Empty is "cannot check", never "safe to destroy".
_worktree_path() {  # $1 selector -> path on stdout, or empty + rc 1
  # Understands the selector grammar `orca worktree rm --help` documents:
  # `id:<repo-id>::<path>`, `name:<displayName>`, `branch:<branch>`,
  # `issue:<number>`, `path:<path>`, `active`/`current` -- plus the bare forms
  # this function has always accepted.
  #
  # J17: it previously understood ONLY the bare forms, so every documented
  # prefixed selector failed to resolve. That mattered because the caller
  # treated "cannot resolve" as "no guard needed" and removed the worktree
  # anyway: `worktree-rm "path:<p>"` destroyed a worktree holding an unmerged
  # commit, silently (verified live 2026-07-23). Orca's own refusal covers a
  # dirty working tree only, never an unmerged branch, so this resolution IS
  # the unmerged guard's reach.
  local sel="$1" path listing matches key val
  # `active`/`current` name the caller's own worktree; only Orca knows which.
  case "$sel" in
    active|current)
      path="$(orca worktree current --json 2>/dev/null \
              | jq -r '.result.worktree.path // empty' 2>/dev/null)"
      [ -n "$path" ] && [ -d "$path" ] && { printf '%s\n' "$path"; return 0; }
      return 1 ;;
  esac
  key=""; val="$sel"
  case "$sel" in
    path:*)   key=path;        val="${sel#path:}" ;;
    name:*)   key=displayName; val="${sel#name:}" ;;
    branch:*) key=branch;      val="${sel#branch:}" ;;
    issue:*)  key=issue;       val="${sel#issue:}" ;;
    id:*)     val="${sel#id:}" ;;
  esac
  # `id:<repo-id>::<path>` (and the bare `<repo-id>::<path>`) carry the path
  # inline, so they need no listing.
  case "$val" in
    *::*) path="${val#*::}"
          [ -d "$path" ] && { printf '%s\n' "$path"; return 0; } ;;
  esac
  # `path:` is likewise self-describing. An explicit path that does not exist is
  # unresolvable -- never a reason to fall through to a fuzzier match.
  if [ "$key" = "path" ]; then
    [ -d "$val" ] && { printf '%s\n' "$val"; return 0; }
    return 1
  fi
  listing="$(orca worktree ps --limit 200 --json 2>/dev/null)" || return 1
  printf '%s' "$listing" | jq -e '.result.truncated != true' >/dev/null 2>&1 || return 1
  matches="$(printf '%s' "$listing" | jq -r --arg v "$val" --arg k "$key" '
    [ .result.worktrees[]?
      | select(
          if   $k == "displayName" then .displayName == $v
          elif $k == "branch"      then (.branch == $v
                                         or ((.branch // "")|sub("^refs/heads/";"")) == $v)
          elif $k == "issue"       then (.linkedIssue != null
                                         and ((.linkedIssue|tostring) == $v))
          else (.worktreeId==$v or .path==$v or .displayName==$v
                or .branch==$v or ((.branch // "")|sub("^refs/heads/";""))==$v)
          end)
      | .path ] | unique' 2>/dev/null)" || return 1
  [ "$(printf '%s' "$matches" | jq -r 'length' 2>/dev/null)" = "1" ] || return 1
  path="$(printf '%s' "$matches" | jq -r '.[0]' 2>/dev/null)"
  [ -n "$path" ] && [ -d "$path" ] || return 1
  printf '%s\n' "$path"
}

# First of origin/HEAD, main, master that this repo actually has.
_worktree_default_base() {  # $1 path -> ref on stdout, or empty
  local path="$1" r
  for r in origin/HEAD main master; do
    git -C "$path" rev-parse --verify -q "$r" >/dev/null 2>&1 && { printf '%s\n' "$r"; return 0; }
  done
  return 1
}

# Reason token on stdout + rc 1 when the worktree holds work; rc 0 otherwise.
_worktree_holds_work() {  # $1 path, $2 base ref (may be empty)
  local path="$1" base="${2:-}"
  [ -z "$(git -C "$path" status --porcelain 2>/dev/null)" ] || {
    echo "worktree_has_uncommitted_work"; return 1; }
  [ -n "$base" ] || return 0
  [ -z "$(git -C "$path" log --oneline "$base..HEAD" 2>/dev/null)" ] || {
    echo "worktree_has_unmerged_commits"; return 1; }
  return 0
}

_cmd_worktree_rm() {  # <selector> [--force] [--base <ref>]
  _require_orca worktree-rm || return $?
  _need "${1:-}" selector || return $?
  local sel="$1"; shift
  local force="" base=""
  while [ $# -gt 0 ]; do case "$1" in
    --force) force=1; shift ;;
    --base) base="$2"; shift 2 ;;
    *) _unknown_opt worktree-rm "$1"; return $? ;;
  esac; done
  # What actually gets forwarded. J17: this used to be the caller's string
  # verbatim, and `repo::<path>` -- the form 8 tests pinned -- is not a selector
  # Orca accepts at all (`selector_not_found` from a live runtime). Forward the
  # RESOLVED path in a documented form instead, so the guard and the removal can
  # never disagree about which worktree is meant.
  local target="$sel"
  if [ -n "$force" ]; then
    echo "[H-MAD] worktree-rm forced selector=$sel — guards skipped" >&2
  else
    local path reason
    # An unresolvable selector is "cannot check", which for a destructive verb
    # must mean refuse -- not, as before, skip the guard and delete anyway.
    if ! path="$(_worktree_path "$sel")" || [ -z "$path" ]; then
      echo "hmad-dispatch: worktree_selector_unresolvable — '$sel' does not resolve to exactly one existing worktree; nothing was removed. Use a documented selector (path:<path>, name:<displayName>, branch:<branch>, issue:<number>, id:<repo-id>::<path>, active) or pass --force to remove without guards." >&2
      return 1
    fi
    [ -n "$base" ] || base="$(_worktree_default_base "$path" || true)"
    if ! reason="$(_worktree_holds_work "$path" "$base")"; then
      echo "hmad-dispatch: $reason — '$sel' still holds work at $path; nothing was removed. Commit or merge it, or pass --force to discard." >&2
      return 1
    fi
    target="path:$path"
  fi
  local args=(worktree rm --worktree "$target")
  [ -n "$force" ] && args+=(--force)
  args+=(--json)
  # Capture rather than discard: the reason for a failure travels in the
  # response envelope, and sending it to /dev/null left the operator a bare
  # `rc=1`. An `ok:false` envelope with exit 0 also has to fail here -- the F11
  # class every other orca-calling verb was already guarded against.
  local out rc=0
  out="$(orca "${args[@]}" 2>&1)" || rc=$?
  if [ $rc -ne 0 ] || ! printf '%s' "$out" | jq -e '.ok == true' >/dev/null 2>&1; then
    [ $rc -ne 0 ] || rc=1
    echo "[H-MAD] worktree-rm failed selector=$target rc=$rc: $(printf '%s' "$out" | jq -r '
      if (.error|type) == "object" then (.error.message // .error.code // "error")
      elif (.error|type) == "string" then .error
      else "error" end' 2>/dev/null || printf '%s' "$out" | head -c 200)" >&2
    return $rc
  fi
}

_cmd_file_diff() {   # <path> [--staged] [--worktree <sel>]
  _require_orca file-diff || return $?
  _need "${1:-}" path || return $?
  local path="$1"; shift
  local args=(file diff "$path")
  while [ $# -gt 0 ]; do case "$1" in
    --staged) args+=(--staged); shift ;;
    --worktree) args+=(--worktree "$2"); shift 2 ;;
    *) _unknown_opt file-diff "$1"; return $? ;; esac; done
  args+=(--json)
  _orca_json '.result | tojson' "${args[@]}"
}

_cmd_file_open_changed() {   # [--mode edit|diff|both] [--worktree <sel>]
  _require_orca file-open-changed || return $?
  local args=(file open-changed)
  while [ $# -gt 0 ]; do case "$1" in
    --mode) args+=(--mode "$2"); shift 2 ;;
    --worktree) args+=(--worktree "$2"); shift 2 ;;
    *) _unknown_opt file-open-changed "$1"; return $? ;; esac; done
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
    *) _unknown_opt automation-create "$1"; return $? ;; esac; done
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

_orca_handle_live() {
  # $1 = handle. 0 = present in the listing, 1 = provably absent, 2 = unknown
  # (the listing itself could not be read).
  #
  # The three-way answer matters: a pin exists precisely so dispatch survives when
  # auto-detect cannot see the pane, so "I could not check" must never be treated
  # as "dead". Only a readable listing that does NOT contain the handle is
  # evidence of death.
  local handle="$1" listing
  listing="$(orca terminal list --json 2>/dev/null)" || return 2
  [ -n "$listing" ] || return 2
  if printf '%s' "$listing" | jq -e --arg h "$handle" \
       '.result.terminals[]? | select(.handle==$h)' >/dev/null 2>&1; then
    return 0
  fi
  # Distinguish "listing parsed and lacks the handle" from "listing was garbage".
  printf '%s' "$listing" | jq -e '.result.terminals' >/dev/null 2>&1 || return 2
  return 1
}

_orca_identity() {
  # $1 = handle. Echo a one-line, TUI-INDEPENDENT identity/liveness summary for the
  # pane, sourced from the SAME `worktree ps` paneKey join the resolver trusts in
  # Pass 0 (_orca_find_by_pane) -- NOT from `.preview` or `terminal read`.
  #
  # That distinction is the whole point. A full-screen TUI (Codex, agy) runs on the
  # alternate screen buffer, so `terminal read` reports `cursor: 0` and `.preview`
  # reads empty even while the agent is live and mid-audit. Measured live
  # 2026-07-28: agy's preview was <empty> and both panes read cursor: 0, which
  # looked like two idle/wrong shells -- but the paneKey join landed on the exact
  # two handles pin-agents had picked, and agy's lastAssistantMessage still held
  # last session's plan-cycle-4 audit, independently confirming the reviewer. The
  # emptiness was an artifact of the API's view of the alt-screen buffer, not
  # evidence of a wrong pin. `worktree ps` carries agentType/state/updatedAt/
  # lastAssistantMessage regardless of screen buffer, so it is the signal to
  # confirm a pin by -- and the reason `env` prints it, so an operator never has to
  # (mis)read a preview to check identity.
  #
  # Diagnostic only: silent (no output, rc 1) when either listing is unreadable.
  local handle="$1" tl key ps line
  tl="$(orca terminal list --json 2>/dev/null)" || return 1
  key="$(printf '%s' "$tl" | jq -r --arg h "$handle" \
    '(.result.terminals[]? | select(.handle==$h) | ((.tabId//"")+":"+(.leafId//""))) // empty' 2>/dev/null | head -1)"
  [ -n "$key" ] && [ "$key" != ":" ] || return 1
  ps="$(orca worktree ps --limit 200 --json 2>/dev/null)" || return 1
  line="$(printf '%s' "$ps" | jq -r --arg k "$key" '
    .result.worktrees[]?.agents[]? | select(.paneKey==$k)
    | (.agentType//"?") + " state=" + (.state//"?")
      + " last=\"" + ((.lastAssistantMessage//"") | gsub("\\s+";" ") | .[0:72]) + "\""' 2>/dev/null | head -1)"
  [ -n "$line" ] || return 1
  printf '%s\n' "$line"
}

_send_text() {
  local agent="$1" text="$2" sub target
  sub="$(_detect_substrate)" || return 1
  target="$(_resolve_target "$agent")" || return 1
  case "$sub" in
    cmux) cmux send --surface "$target" "$text"; cmux send-key --surface "$target" Enter ;;
    orca)
      # Refuse to send into a handle the listing proves is gone. Orca does not
      # always reject a rotated handle -- a dispatch has been observed printing
      # "Sent 7293 bytes" into a dead pane and simply vanishing: no error, no
      # report file, no work done. "Sent N bytes" is not delivery, and a
      # resolvable pin is not a live pane. Only positive evidence blocks the
      # send; an unreadable listing (rc 2) still sends, because a pin has to keep
      # working when the listing cannot be read.
      if _orca_handle_live "$target"; [ $? -eq 1 ]; then
        echo "hmad-dispatch: terminal_handle_stale — '$agent' resolves to $target, which is not a live terminal; nothing was sent. Re-pin (hmad-dispatch pin $agent <handle>) or relaunch (hmad-dispatch launch $agent)." >&2
        return 1
      fi
      orca terminal send --terminal "$target" --text "$text" --enter ;;
  esac
}

# Two agents cannot be one pane, so equal non-empty resolutions prove at least one
# is wrong -- the exact shape a tab-inherited title produces. Not suppressed by
# HMAD_SKIP_PREFLIGHT: that bypass exists to permit dispatching without a
# preflight, not to permit dispatching into a provably wrong pane.
_preflight_conflict_check() {  # -> 0 ok, 1 conflict (message on stderr)
  local c a
  c="$(_resolve_target codex 2>/dev/null)" || c=""
  a="$(_resolve_target agy 2>/dev/null)" || a=""
  [ -n "$c" ] && [ -n "$a" ] && [ "$c" = "$a" ] || return 0
  echo "hmad-dispatch: preflight_agent_conflict — codex and agy both resolve to $c; at least one is wrong and nothing was sent. Pin them explicitly (hmad-dispatch pin <agent> <handle>)." >&2
  return 1
}

_dispatch_boundary() {
  # ONE definition of the marker, shared by `send` (pane path) and `exec`
  # (exit-code path). It used to live only inside `_cmd_send`, which is how the two
  # paths came to disagree about whether prompt echo was guarded at all: `send`
  # sliced past it, `exec` had never heard of it. Single-source, per
  # invariants.base.md §Single-source contract.
  printf '%s\n' "${HMAD_DISPATCH_BOUNDARY:-===HMAD-DISPATCH-BOUNDARY===}"
}

# ---------------------------------------------------------------------------
# Live-progress channel for the headless `exec` path.
#
# WHY THIS EXISTS. `exec` is the dispatch path h-mad defaults to precisely
# because the pane path could not resolve agy/codex surfaces reliably. But the
# headless path traded that away for total blindness: a foreground `exec` inside
# an orchestrator's shell tool prints nothing until the process exits, so a
# 15-minute audit is a blank screen, indistinguishable from a wedged one.
#
# The two backends were NOT equally blind, and the docs said they were:
#   codex — `codex exec` writes its transcript to stdout as it runs, and
#           `_cmd_exec` redirects that straight into $log. `--log` really was
#           live here. Measured: log grew 811 -> 1446 bytes across a 48s run.
#   agy   — `agy --print` (text) emits NOTHING until the turn completes, and
#           `_cmd_exec` captured it to a temp file and only THEN appended to
#           $log. So agy's `--log` held zero bytes for the whole run and a
#           `tail -f` on it showed nothing until the end. That is the defect the
#           operator saw as "no process visible for agy".
#           `agy --log-file` is not a substitute: it is language-server noise
#           (auth/gRPC/http traces), carrying no step or tool information.
#
# THE FIX. agy grows `--output-format stream-json`, which emits one NDJSON event
# per line, flushed live (measured: 2 -> 5 -> 6 -> 9 -> 11 -> 12 lines across a
# 48s run). That stream goes append-direct into $log, so `--log` is now live for
# BOTH backends and the doc's claim becomes true.
#
# THE COST, AND WHY IT IS CONTAINED. stream-json changes agy's stdout format,
# and agy's stdout WAS the verdict. So the verdict is no longer read from the
# stream: it is extracted from the `result` event's `.response` field, which
# carries byte-identical text to what `--print` text mode printed. The external
# contract is unchanged on every channel a caller reads -- `exec` stdout is the
# response text, `--out` is the response text, `$?` is still "did the CLI run".
# Only the LOG's format changed, and only for agy.

# Extract agy's final response from an NDJSON transcript region.
#
# Scoped to lines AFTER $2 so a caller-supplied --log holding a PRIOR dispatch's
# stream cannot donate its stale `result` event to this one -- the same
# last-writer hazard J29 records for --out, arriving here by a different route.
# `fromjson? // empty` tolerates non-JSON lines, which the log legitimately
# carries: pre-existing caller content, and our own `#hmad-beat` lines.
#
# Falls back to concatenated `agent_response` text_delta when no `result` event
# exists -- the shape a watchdog KILL leaves behind, where the turn produced text
# but never got to announce completion.
#
# Deliberately reads `.response` regardless of `.status`: agy emits
# status "ERROR" alongside a perfectly good response when a single tool call was
# denied mid-turn (measured: a blocked read_file produced status ERROR, rc 0, and
# the full correct answer). Dropping that response would manufacture a
# no_verdict halt out of a run that answered.
_agy_ndjson_response() {  # <logfile> <lines-before-this-dispatch>
  local log="$1" skip="${2:-0}" region resp
  [ -s "$log" ] || return 0
  command -v jq >/dev/null 2>&1 || return 0
  region="$(tail -n "+$(( skip + 1 ))" "$log" 2>/dev/null)" || return 0
  [ -n "$region" ] || return 0
  # `-Rs` (raw + slurp) reads the whole region as ONE string, splits it, and runs
  # `fromjson?` per line. That combination is load-bearing in both directions:
  #
  #   * plain `-s` aborts the entire slurp on the first non-JSON line, and the
  #     region legitimately contains them (`#hmad-beat`, caller-supplied text).
  #   * per-line `-r` streaming survives those lines but emits the response as
  #     SEPARATE OUTPUT LINES, so any downstream `tail -1` silently truncates a
  #     multi-line verdict to its final line. Measured on a fixture whose
  #     response was "ASSESSMENT: READY_TO_MERGE\nSome detail here." — the
  #     verdict line was dropped and only the detail survived, which would have
  #     turned a passing architectural review into an unextractable one.
  #
  # Selecting the last matching EVENT and printing its response whole keeps the
  # response an opaque blob at every step.
  resp="$(printf '%s\n' "$region" | jq -Rs '
      split("\n")
      | map(fromjson? // empty)
      | map(select(.event == "result") | .result.response // empty)
      | last // empty' -r 2>/dev/null)" || resp=""
  if [ -z "$resp" ]; then
    resp="$(printf '%s\n' "$region" | jq -Rs '
        split("\n")
        | map(fromjson? // empty)
        | map(select(.event == "step_update")
              | .step_update
              | select(.step_type == "agent_response")
              | .text_delta // empty)
        | join("")' -r 2>/dev/null)" || resp=""
  fi
  printf '%s' "$resp"
}

# Classify a transcript so `progress` renders it with the right lens.
_exec_log_format() {  # <logfile> -> agy-ndjson | codex-text | empty | missing
  local log="$1"
  [ -f "$log" ] || { printf 'missing'; return 0; }
  [ -s "$log" ] || { printf 'empty'; return 0; }
  # Whitespace-tolerant on purpose. Real agy emits compact JSON, but a
  # serializer that inserts a space after the colon would otherwise be
  # classified as a codex text transcript and rendered with the wrong lens —
  # which is exactly what a test fixture built with `json.dumps` did, silently
  # exercising the codex branch in a test named for the agy one.
  if grep -aqE '^[[:space:]]*\{[[:space:]]*"event"[[:space:]]*:[[:space:]]*"(init|step_update|result)"' "$log" 2>/dev/null; then
    printf 'agy-ndjson'
  else
    printf 'codex-text'
  fi
}

# Seconds since the file was last written. The liveness signal that separates
# "thinking for a long time" from "died": a live agent keeps touching its
# transcript, a dead one does not. Portable across BSD (-f %m) and GNU (-c %Y).
_exec_log_age() {  # <logfile> -> seconds, or empty when unknowable
  local log="$1" mt now
  [ -f "$log" ] || return 0
  mt="$(stat -f %m "$log" 2>/dev/null || stat -c %Y "$log" 2>/dev/null)" || return 0
  [ -n "$mt" ] || return 0
  now="$(date +%s)"
  printf '%s' "$(( now - mt ))"
}

# ---------------------------------------------------------------------------
_verdict_after_boundary() {  # $1 = transcript, $2 = boundary, $3 = echo_expected (1|0)
  # Recover the agent's LAST verdict line, reading only the region the agent could
  # have written — everything after the final echo of our own boundary.
  #
  # J23: this exists because `exec` recovery used to grep the WHOLE transcript.
  # `codex exec ... -` echoes the piped prompt into that transcript, and a dispatch
  # prompt states its output contract by listing the legal STATUS values one per
  # line (references/codex-implementer-prompt.md requires it). So on a dispatch that
  # never ran, `tail -1` returned the LAST option of our own contract block --
  # deterministically `STATUS: NEEDS_CONTEXT` -- and the caller wrote it to --out,
  # where h_mad_extract_verdict.py accepts it. Measured on a real 401-auth failure:
  # the only four STATUS lines in a 20,770-byte log were the prompt's own, at
  # 268/271/274/277. The "must start the line" guard cannot help; echoed contract
  # lines do start the line.
  #
  # What a MISSING boundary means depends on the backend, so the caller says which:
  #
  #   $3=1 (codex) -- codex echoes its stdin, so our boundary is expected in the
  #     transcript. If it is absent, the echo is absent or TRUNCATED, and a truncated
  #     echo can still carry the contract block while losing the trailing boundary.
  #     Grepping the whole log there would reopen the exact defect. Refuse instead:
  #     no verdict is the honest answer, and silence is what the caller can act on.
  #   $3=0 (agy) -- the prompt is an ARG, never echoed; the transcript is the response
  #     alone, or content a caller pre-loaded into --log. There is no echo to skip and
  #     no boundary to expect, so the whole transcript is fair game, exactly as before.
  #
  # Bias in both directions is toward silence: if the agent QUOTES the boundary back,
  # the last occurrence lands inside its reply and we may slice past a real verdict.
  # That fails to silence, not to a fabricated answer -- the whole point of the change.
  local start=0 last
  last="$(grep -aFn -- "$2" "$1" 2>/dev/null | tail -1 | cut -d: -f1)"
  if [ -n "$last" ]; then
    start="$last"
  elif [ "${3:-0}" = "1" ]; then
    return 0
  fi
  tail -n "+$((start + 1))" "$1" 2>/dev/null \
    | grep -aE '^(STATUS|VERDICT):' | tail -1 || true
}

# $1 agent, $2 promptfile.
#
# Small prompts are inlined. Above HMAD_SEND_INLINE_MAX bytes (default 8192)
# the agent is told to read the staged file instead: pasting a 16-90 KB audit
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

  _preflight_conflict_check || return 1

  if [ -n "${HMAD_SKIP_PREFLIGHT:-}" ]; then
    echo "hmad-dispatch: HMAD_SKIP_PREFLIGHT set — dispatching without a preflight receipt." >&2
  else
    local _reason
    if ! _reason="$(_receipt_valid)"; then
      echo "hmad-dispatch: $_reason — no valid preflight receipt for this dispatch; nothing was sent. Run 'hmad-dispatch env' and confirm 'PREFLIGHT: PASS', then retry." >&2
      return 1
    fi
  fi

  local size
  size=$(wc -c < "$promptfile" | tr -d ' ')

  # Boundary appended as the FINAL line of everything we send. The agent's reply
  # renders after the echoed prompt, so verdict/report extraction slices to the
  # region past this marker's last occurrence and never re-reads the prompt's own
  # `STATUS: DONE`/sentinel exemplar as the agent's answer (the false-DONE trap).
  # Kept out of the >8192 file-read branch's file body ON PURPOSE: it must land in
  # the text that is actually TYPED into the pane (and thus echoed), which for a
  # large prompt is the "Read <abs>" line, not the untyped file.
  local boundary; boundary="$(_dispatch_boundary)"

  if [ "$size" -le "$max" ]; then
    _send_text "$agent" "$(cat "$promptfile")

$boundary"
    return $?
  fi

  # Canonical path — the agent resolves it from its own cwd, not ours.
  local abs
  abs="$(cd "$(dirname "$promptfile")" && pwd -P)/$(basename "$promptfile")"
  _send_text "$agent" "Read $abs and follow the instructions in it. It is ${size} bytes; read the whole file before responding.

$boundary"
}
_cmd_ask() {  # <agent> <promptfile> [--timeout <s>] [--out <file>]
  # The scrape-path dispatch, composed from the three verbs an audit/review
  # always uses together (recurrence 12+): send -> wait-idle -> read the full
  # buffer. The orchestration path is `dispatch`+`await`; the report-file path is
  # `report-wait`; this is their screen-scrape sibling. Verdict extraction stays
  # a separate `h_mad_extract_verdict.py` call -- it needs --feature/--phase for
  # its contract and belongs to python. `ask` hands you the buffer to extract.
  #
  # Composed from the existing commands on purpose (single-source): send's
  # preflight-receipt guard and inline-vs-file delivery, wait's full-buffer idle
  # check (J3), and read --from-start all carry unchanged.
  _need "${1:-}" agent || return $?
  _need "${2:-}" promptfile || return $?
  local agent="$1" promptfile="$2"; shift 2
  local timeout="" out=""
  while [ $# -gt 0 ]; do case "$1" in
    --timeout) timeout="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) _unknown_opt ask "$1"; return $? ;;
  esac; done
  # 1. Dispatch. send refuses without a fresh preflight receipt, so fail fast --
  #    never wait on or read a pane we did not dispatch into. send/wait chatter
  #    ("Sent N bytes", the native-idle line) goes to stderr so ask's STDOUT is
  #    exactly the reply buffer -- the thing a caller pipes into the extractor.
  _cmd_send "$agent" "$promptfile" >&2 || return $?
  # 2. Block until idle (full-buffer stability, not a tail).
  local wargs=("$agent"); [ -n "$timeout" ] && wargs+=(--timeout "$timeout")
  _cmd_wait "${wargs[@]}" >&2 || return $?
  # 3. Capture the whole buffer.
  if [ -n "$out" ]; then
    _cmd_read "$agent" --from-start > "$out"
  else
    _cmd_read "$agent" --from-start
  fi
}

_exec_comment_compose() {
  local current="$1" stamp="$2"
  [ -n "$current" ] || { printf '%s' "$stamp"; return 0; }

  # Find the first complete span by its contents.  In particular, do not treat a
  # lead-in without its terminator as a span: replacing that would make a
  # malformed comment consume everything through an unbounded end offset.
  case "$current" in
    *"h-mad: "*)
      local rest prefix suffix
      rest="${current#*h-mad: }"
      # QUOTE $rest. In `${var%pattern}` the pattern is glob-matched, so an unquoted
      # $rest carrying `*`, `[`, `?` or `\` is read as a pattern rather than a literal
      # suffix. Production verdicts embed the agent's markdown report -- links
      # `[x](y)`, bold `**x**` -- so the strip silently failed, `prefix` stayed equal
      # to `current`, and the result was the whole comment twice. Measured live: the
      # real worktree card reached 513 spans / 38,329 bytes, doubling on every stamp.
      # Every unit test used short glob-free strings, so none of them fired it.
      prefix="${current%"$rest"}"
      prefix="${prefix%h-mad: }"
      case "$rest" in
        *"⟦/h-mad⟧"*)
          suffix="${rest#*⟦/h-mad⟧}"
          printf '%s%s%s' "$prefix" "$stamp" "$suffix"
          return 0
          ;;
      esac
      ;;
  esac
  printf '%s · %s' "$current" "$stamp"
}

_exec_wt_target() {  # <cd_dir> — selector and base64 comment, or rc 1
  local cd_dir="$1" payload line tmp pid ticks=0 read_rc=0
  local stamp_timeout="${HMAD_EXEC_STAMP_TIMEOUT:-2}"
  tmp="$(mktemp -t hmad_exec_wt.XXXXXX)" || return 1
  # Keep the bounded runner as the production watchdog, with an outer reap guard
  # so an isolated test shim (or a stale replacement) cannot defeat the bound.
  ( _exec_run "$stamp_timeout" orca worktree ps --limit 200 --json </dev/null >"$tmp" 2>/dev/null ) &
  pid=$!
  while kill -0 "$pid" 2>/dev/null && [ "$ticks" -lt 25 ]; do
    sleep 0.1; ticks=$((ticks + 1))
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
    kill -KILL -"$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    rm -f "$tmp"
    return 1
  fi
  wait "$pid" 2>/dev/null || read_rc=$?
  [ "$read_rc" -eq 0 ] || { rm -f "$tmp"; return 1; }
  payload="$(cat "$tmp")"
  rm -f "$tmp"
  [ -n "$payload" ] || return 1

  line="$(printf '%s' "$payload" | jq -r --arg cd "$cd_dir" '
    def norm: if . == "/" then "/" else sub("/+$"; "") end;
    . as $root
    | (($cd | norm) as $c
       | (($root.result.worktrees // [])
       | map(.path = ((.path // "") | norm)
             | . as $w
             | select($w.path != "" and
                      ($c == $w.path or ($c | startswith($w.path + "/")))))
       | sort_by(.path | length) | reverse | .[0])
      )
      // (($root.result.worktrees // []) | map(select(.isActive == true)) | .[0])
    | select((.worktreeId // "") != "")
    | [.worktreeId, ((.comment // "") | @base64)] | @tsv' 2>/dev/null)" || return 1
  [ -n "$line" ] || return 1
  printf '%s\n%s\n' "${line%%$'\t'*}" "${line#*$'\t'}"
}

_exec_stamp() {  # <kind> <agent> <label> <cd_dir> [rc] [verdict]
  local kind="$1" agent="$2" label="$3" cd_dir="$4" rc="${5:-0}" verdict="${6:-}"

  # Sanitise the verdict before it can reach a worktree comment. `_cmd_exec` sets
  # verdict to the agent's ENTIRE final message (`verdict="$(cat "$last")"`), which
  # is a multi-line markdown report. Two consequences, both measured live on the real
  # card: the comment became a transcript sink, and -- because the agent's text can
  # itself contain `⟦/h-mad⟧` -- it forged a span terminator and broke the very
  # boundary the composer keys on. So: first line only, span markers stripped, capped.
  if [ -n "$verdict" ]; then
    verdict="${verdict%%$'\n'*}"
    verdict="${verdict//h-mad: /}"
    verdict="${verdict//$'\342\237\246'\/h-mad$'\342\237\247'/}"
    [ "${#verdict}" -le 48 ] || verdict="${verdict:0:45}..."
  fi

  local sub="${HMAD_SUBSTRATE:-}"
  if declare -F _detect_substrate >/dev/null 2>&1; then
    sub="$(_detect_substrate 2>/dev/null || true)"
  fi
  [ "$sub" = "orca" ] || return 0

  local target selector comment_b64 current stamp state composed
  target="$(_exec_wt_target "$cd_dir" 2>/dev/null)" || return 0
  selector="$(printf '%s\n' "$target" | sed -n '1p')"
  comment_b64="$(printf '%s\n' "$target" | sed -n '2p')"
  [ -n "$selector" ] || return 0
  if [ -n "$comment_b64" ]; then
    current="$(printf '%s' "$comment_b64" | base64 -D 2>/dev/null ||
      printf '%s' "$comment_b64" | base64 -d 2>/dev/null || true)"
  else
    current=""
  fi

  # Elapsed is measured from the dispatch start recorded by `_cmd_exec`, NOT from
  # this function's entry. It is reported in SECONDS below a minute and minutes
  # above it: a heartbeat exists to tell "still working" from "died", and a
  # minute-granularity counter reads `0m` for the whole first minute, so the first
  # informative change would arrive 60s after the operator started wondering.
  local elapsed=0
  if [ -n "${_HMAD_EXEC_T0:-}" ]; then elapsed=$(( SECONDS - _HMAD_EXEC_T0 )); fi
  [ "$elapsed" -ge 0 ] || elapsed=0
  local elapsed_txt
  if [ "$elapsed" -lt 60 ]; then elapsed_txt="${elapsed}s"; else elapsed_txt="$(( elapsed / 60 ))m"; fi

  case "$kind" in
    start) state="running · 0s" ;;
    beat)  state="running · $elapsed_txt" ;;
    exit)  state="rc=$rc · ${verdict:-no-verdict}" ;;
    *) return 0 ;;
  esac
  stamp="h-mad: $agent $label · $state"$'\342\237\246'"/h-mad"$'\342\237\247'
  if declare -F _exec_comment_compose >/dev/null 2>&1; then
    composed="$(_exec_comment_compose "$current" "$stamp")" || return 0
  else
    # The helper is normally available; this keeps the leaf callable in
    # isolation (as the shell-level unit tests do).
    composed="$current"
    if [ -z "$composed" ]; then composed="$stamp"
    elif [[ "$composed" == *"h-mad: "* ]]; then
      local rest prefix suffix
      rest="${composed#*h-mad: }"; prefix="${composed%$rest}"; prefix="${prefix%h-mad: }"
      if [[ "$rest" == *"⟦/h-mad⟧"* ]]; then
        suffix="${rest#*⟦/h-mad⟧}"; composed="$prefix$stamp$suffix"
      else composed="$composed · $stamp"; fi
    else composed="$composed · $stamp"; fi
  fi

  local stamp_timeout="${HMAD_EXEC_STAMP_TIMEOUT:-2}"
  if declare -F _exec_run >/dev/null 2>&1; then
    _exec_run "$stamp_timeout" orca worktree set --worktree "$selector" --comment "$composed" --json </dev/null >/dev/null 2>&1 || true
  else
    # Isolated leaf invocation fallback; production uses _exec_run above.
    ( orca worktree set --worktree "$selector" --comment "$composed" --json </dev/null >/dev/null 2>&1 ) &
    local pid=$! ticks=0
    while kill -0 "$pid" 2>/dev/null && [ "$ticks" -lt 20 ]; do sleep 0.1; ticks=$((ticks + 1)); done
    kill -KILL "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  fi
  return 0
}

_exec_run() {  # [--heartbeat <agent> <label> <cd_dir> <interval>] <seconds> <cmd...>
  local heartbeat=0
  local hb_agent="" hb_label="" hb_cd_dir="" hb_interval=0
  if [ "${1:-}" = "--heartbeat" ]; then
    hb_agent="${2:-}" hb_label="${3:-}" hb_cd_dir="${4:-}" hb_interval="${5:-0}"
    heartbeat=1
    shift 5
  fi
  local secs="${1:-}"; shift
  # Returns the child's exit code, or 124 if it had to be killed at the deadline
  # (the GNU `timeout` convention). stdin/stdout/stderr are inherited by the child,
  # so a `< promptfile` / `>&2` on the CALL site applies to the backgrounded cmd.
  # Run the child in its OWN process group so a timeout kills the whole subprocess
  # tree, not just the direct child — codex/agy fork grandchildren that would
  # otherwise orphan and survive past the 124. `set -m` (job control) makes bash
  # place each backgrounded job in a fresh process group; the pgid is fixed at
  # fork, so restoring the prior -m state afterwards is safe. macOS ships no
  # `setsid`, so `set -m` is the portable way to get a new pgroup here.
  local had_m=0; case "$-" in *m*) had_m=1 ;; esac
  set -m
  # `<&0` explicitly hands the child our stdin. Without it, bash redirects a
  # backgrounded command's stdin from /dev/null — which silently starved
  # `codex exec -` of its piped prompt ("No prompt provided via stdin").
  # Absolute deadline off bash's SECONDS, NOT a count of completed sleeps: each
  # iteration costs slightly more than its sleep, so counting ticks lets a long
  # timeout drift late by the accumulated loop overhead. `secs` is now the real
  # wall-clock bound. 0.25s polling caps the post-deadline overshoot instead of
  # the 1s a whole-second sleep leaves.
  local deadline=0 poll=0.25
  if [ -n "$secs" ]; then deadline=$(( SECONDS + secs )); fi
  local last_beat="$SECONDS"
  "$@" <&0 &
  local pid=$!
  if [ "$had_m" -eq 0 ]; then set +m; fi
  while kill -0 "$pid" 2>/dev/null; do
    if [ -n "$secs" ] && [ "$SECONDS" -ge "$deadline" ]; then
      # Signal the whole group (`-$pid`; child is group leader) so grandchildren
      # die too. Bare pid if the group is already gone.
      kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
      # Poll out the TERM grace period rather than blocking on a flat `sleep 2`,
      # so a child that honours SIGTERM is reaped immediately; 2s is the cap.
      local ticks=0
      while [ "$ticks" -lt 20 ] && kill -0 "$pid" 2>/dev/null; do
        sleep 0.1; ticks=$(( ticks + 1 ))
      done
      kill -KILL -"$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null; return 124
    fi
    if [ "$heartbeat" -eq 1 ] && [ "$hb_interval" -gt 0 ] \
      && [ $(( SECONDS - last_beat )) -ge "$hb_interval" ]; then
      _exec_stamp beat "$hb_agent" "$hb_label" "$hb_cd_dir" || true
      # Also beat into the TRANSCRIPT, not only the Orca worktree comment. The
      # comment is the mobile-visible channel; the transcript is the one a
      # terminal watcher and `progress` read. Without a beat here, a long silent
      # tool call and a dead process look identical in the log — the transcript
      # simply stops growing in both cases. Non-JSON by design and prefixed `#`,
      # which every reader of an NDJSON log already tolerates.
      if [ -n "${_HMAD_EXEC_BEAT_LOG:-}" ]; then
        printf '#hmad-beat %s %s running %ss\n' \
          "$(date -u +%H:%M:%SZ)" "$hb_agent" "$(( SECONDS - ${_HMAD_EXEC_T0:-0} ))" \
          >> "${_HMAD_EXEC_BEAT_LOG}" 2>/dev/null || true
      fi
      last_beat="$SECONDS"
    fi
    sleep "$poll"
  done
  wait "$pid"
}

# J29: `--out` is last-writer-wins across concurrent dispatches, silently. Two
# `exec` runs pointed at one path both exit 0 and the file keeps only the SECOND
# responder's answer, so a caller who reads `--out` loses a verdict with nothing
# to distinguish that from a dispatch that never ran. (`--log` has no such defect:
# both backends APPEND to a caller-supplied log, which is what let the lost half
# be recovered at all.)
#
# Fingerprint at dispatch start, re-check at write time. An ABSENT and an EMPTY
# file collapse to the same state deliberately -- neither holds a verdict, so
# neither is worth preserving.
_out_fingerprint() {  # <file>
  [ -s "$1" ] || return 0
  cksum < "$1" 2>/dev/null || true
}

# Refuse to overwrite an `--out` whose content changed since this dispatch
# started. Returns 0 when writing is safe.
#
# The check is at WRITE time and keyed on CHANGE, not a pre-flight
# `[ -s "$out" ]` refusal -- that distinction is load-bearing.
# references/failure-recovery.md's `<phase>:no_verdict` remedy is to re-dispatch,
# and SKILL.md's --out paths are templated per feature+module, so a legitimate
# retry arrives at the same path holding the failed attempt's own short
# narration. Refusing on merely non-empty would refuse the documented recovery.
# Only a change between start and write implies a second writer.
#
# Deliberately does NOT touch rc: this function's caller returns the AGENT's exit
# code ("did the CLI run"), which _exec_stamp and _cmd_notify both consume. The
# verdict still reaches stdout and the transcript, so nothing is lost -- what J29
# records is the SILENCE, and this stderr line is what cures it.
_out_clobber_ok() {  # <file> <fingerprint-at-dispatch-start>
  local f="$1" fp0="$2" fp_now
  fp_now="$(_out_fingerprint "$f")"
  [ "$fp_now" = "$fp0" ] && return 0
  echo "hmad-dispatch: exec: REFUSING to overwrite --out $f — its content changed while this dispatch ran (another dispatch wrote there; J29). Existing file preserved; this dispatch's answer is on stdout and in the transcript." >&2
  return 1
}

# Render a bounded digest of an exec transcript. Shared by the `progress` verb
# and by the auto-log dump at the end of an agy dispatch.
#
# BOUNDED IS THE POINT. The caller of `progress` is usually an orchestrator
# polling every 30-60s, and an unbounded dump would spend more context on
# watching the work than on doing it. One line per event, tool payloads reduced
# to a name and a short argument, output capped at <lines>.
_render_progress() {  # <logfile> [lines]
  local log="$1" n="${2:-25}" fmt
  fmt="$(_exec_log_format "$log")"
  case "$fmt" in
    missing) echo "  (no transcript at $log — dispatch not started, or --log not passed)"; return 0 ;;
    empty)   echo "  (transcript empty — agent started, nothing emitted yet)"; return 0 ;;
  esac
  if [ "$fmt" = agy-ndjson ] && command -v jq >/dev/null 2>&1; then
    # `fromjson? // empty` skips our own #hmad-beat lines and any pre-existing
    # caller content without aborting the stream.
    tail -n 400 "$log" 2>/dev/null | jq -R -r '
      fromjson? // empty
      | if .event == "init" then
          "  · session start (cwd " + ((.init.cwd // "?") | split("/") | last) + ")"
        elif .event == "step_update" then
          (.step_update // {}) as $u
          | ($u.duration_seconds // 0 | floor | tostring) as $d
          | if $u.step_type == "tool" then
              "  · tool " + ($u.tool_name // "?") + " " + ($u.state // "?")
              + (if $u.state == "ACTIVE" then ""
                 else " (" + $d + "s)" end)
              + (($u.tool_info.parameters // {} | tostring | .[0:70]) as $p
                 | if $p == "{}" then "" else " " + $p end)
            elif $u.step_type == "agent_response" then
              "  · agent thinking/reply (" + $d + "s"
              + (if ($u.usage.total_tokens // 0) > 0
                 then ", " + ($u.usage.total_tokens | tostring) + " tok" else "" end) + ")"
            else
              "  · " + ($u.step_type // "step") + " " + ($u.state // "")
            end
        elif .event == "result" then
          "  · RESULT status=" + (.result.status // "?")
          + " turns=" + ((.result.num_turns // 0) | tostring)
          + " " + ((.result.duration_seconds // 0) | floor | tostring) + "s"
        else empty end' 2>/dev/null | tail -n "$n"
  else
    # codex text transcript, rendered ONLY past the echoed prompt.
    #
    # J23, arriving by a new route. `codex exec ... -` echoes its stdin into the
    # transcript, and a dispatch prompt states its output contract by listing the
    # legal STATUS values one per line. So a naive tail of a codex log shows
    # `STATUS: <something>` seconds into the run — measured live at t=14s on a
    # 45s dispatch, before the agent had run a single command. A watcher reading
    # that as "the verdict already arrived" is the exact misreading
    # `_verdict_after_boundary` exists to prevent; a progress view that
    # resurrects it would be worse than no progress view, because it fabricates
    # confidence.
    #
    # Same boundary, same single source, same last-occurrence bias toward silence.
    local bpat bline body
    bpat="$(_dispatch_boundary)"
    # `|| true` is load-bearing under `set -euo pipefail`: grep exits 1 on NO
    # MATCH, which is the normal early-run state here (the boundary has not been
    # echoed yet), and a bare assignment propagates that status straight into
    # `set -e`. Without it `progress` died silently mid-render and exited 1 —
    # turning the watch verb into another thing that tells you nothing.
    bline="$(grep -aFn -- "$bpat" "$log" 2>/dev/null | tail -1 | cut -d: -f1)" || true
    if [ -z "$bline" ]; then
      # No echoed boundary yet means codex is still echoing our prompt: every
      # byte in the file so far is OURS. Say so rather than showing it back.
      echo "  (prompt still echoing — no agent output yet)"
      return 0
    fi
    # `hook:` lines are pure framework bookkeeping and outnumber the real events
    # roughly 2:1; dropping them is what makes a 25-line window actually cover
    # the last 25 things the agent DID.
    body="$(tail -n "+$(( bline + 1 ))" "$log" 2>/dev/null \
      | grep -av '^hook: ' | grep -a . | tail -n "$n" | sed 's/^/  /')"
    if [ -n "$body" ]; then printf '%s\n' "$body"
    else echo "  (agent has not emitted output yet)"; fi
  fi
}

# `progress <logfile>` — a bounded, NON-BLOCKING snapshot of a running dispatch.
#
# WHY A VERB AND NOT `tail -f`. The documented way to watch an exec used to be
# `tail -f <log>`, which an orchestrating agent cannot run: it never exits, so it
# consumes the whole shell-tool timeout and returns nothing useful. `progress`
# returns immediately, which makes it pollable in a loop between other work, and
# bounded, which makes polling affordable.
#
# The header answers the question the operator actually has — "is it alive?" —
# before any transcript content: a live agent keeps touching its transcript, so
# time-since-last-write separates "thinking hard" from "died". STALE is a
# threshold on that age, not on total runtime; it deliberately sits above the
# heartbeat interval so a healthy silent run cannot be reported as stale.
_cmd_progress() {  # <logfile> [--lines <n>] [--pid <pid>]
  _need "${1:-}" logfile || return $?
  local log="$1"; shift
  local n=25 pid="" stale="${HMAD_PROGRESS_STALE_SEC:-}"
  while [ $# -gt 0 ]; do case "$1" in
    --lines) n="$2"; shift 2 ;;
    --pid) pid="$2"; shift 2 ;;
    *) _unknown_opt progress "$1"; return $? ;;
  esac; done
  # Default the stale threshold to 2x the heartbeat, so a beat that lands on
  # schedule always refutes staleness even if the agent itself is silent.
  [ -n "$stale" ] || stale=$(( ${HMAD_EXEC_HEARTBEAT_SEC:-120} * 2 ))

  local fmt age lines_n size proc="unknown"
  fmt="$(_exec_log_format "$log")"
  age="$(_exec_log_age "$log")"
  lines_n=0; size=0
  if [ -f "$log" ]; then
    lines_n="$(wc -l < "$log" 2>/dev/null | tr -d ' ')"
    size="$(wc -c < "$log" 2>/dev/null | tr -d ' ')"
  fi
  if [ -n "$pid" ]; then
    if kill -0 "$pid" 2>/dev/null; then proc="alive"; else proc="exited"; fi
  fi

  local liveness="unknown"
  if [ -n "$age" ]; then
    if [ "$age" -le "$stale" ]; then liveness="LIVE (last write ${age}s ago)"
    else liveness="STALE (no write for ${age}s — exceeded ${stale}s)"; fi
  fi

  echo "hmad-dispatch: progress $log"
  echo "  format: $fmt · lines: ${lines_n:-0} · bytes: ${size:-0}"
  echo "  liveness: $liveness${pid:+ · pid $pid: $proc}"
  echo "  --- last $n events ---"
  _render_progress "$log" "$n"
  # Exit 0 on every observable state on purpose. `progress` REPORTS liveness; it
  # is not a gate. A non-zero here would invite `progress ... && continue`, which
  # is the `$?`-branching habit the audit-gate signal discipline forbids — read
  # the `liveness:` line, do not branch on the exit code.
  return 0
}

_cmd_exec() {  # <codex|agy> <promptfile> [--cd <dir>] [--model <m>] [--out <file>] [--log <file>] [--timeout <s>] [codex: --sandbox <mode>] [agy: --effort <e> --sandbox]
  # The exit-code dispatch path (alternative to the pane REPL). The agent runs
  # HEADLESS as a real subprocess, so — unlike send+wait+read — there IS a process
  # to reap: this verb returns the agent's own exit code, no idle poll. The agent's
  # final response (the STATUS:/VERDICT: carrier) goes to OUR stdout; run chatter to
  # stderr. So a caller gets both signals cleanly: `$?` for "did the CLI run", and a
  # stdout token to pipe into h_mad_extract_verdict.py for "did the WORK pass" (exit
  # 0 never means the task passed — always extract).
  #
  #   codex — `codex exec`, prompt via stdin, final message via --output-last-message.
  #           The 5d/5e IMPLEMENTER path (writes tests/impl; default --sandbox
  #           workspace-write).
  #   agy   — `agy --print "<prompt>"`, response printed straight to stdout. The
  #           AUDIT/REVIEW path (Phases 3/4/5b + 5e-review); a headless replacement
  #           for the agy `ask` pane scrape. Pane-independent, so it sidesteps agent
  #           identity resolution (orca#9870) entirely.
  #
  # Tradeoff vs the pane path: no cross-dispatch conversation context (each exec is
  # a fresh session), and no human-visible Orca pane. Chosen where the task is
  # self-contained and the exit code is the point.
  _need "${1:-}" agent || return $?
  _need "${2:-}" promptfile || return $?
  local agent="$1" promptfile="$2"; shift 2
  case "$agent" in codex|agy) ;;
    *) echo "hmad-dispatch: exec: unknown agent '$agent' (expected codex|agy)" >&2; return 2 ;;
  esac
  [ -f "$promptfile" ] || { echo "hmad-dispatch: no such prompt file: $promptfile" >&2; return 2; }

  local cd_dir="" model="" out="" timeout="" sandbox="" effort="" log=""
  [ "$agent" = codex ] && sandbox="workspace-write"   # codex default; agy has none
  while [ $# -gt 0 ]; do case "$1" in
    --cd) cd_dir="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    --log) log="$2"; shift 2 ;;             # stream live transcript here for `tail -f`
    --timeout) timeout="$2"; shift 2 ;;
    --sandbox) sandbox="$2"; shift 2 ;;   # codex: read-only|workspace-write|danger…; agy: any value enables its --sandbox
    --effort) effort="$2"; shift 2 ;;      # agy only
    *) _unknown_opt exec "$1"; return $? ;;
  esac; done
  [ "$agent" = codex ] && [ -n "$effort" ] && {
    echo "hmad-dispatch: exec: --effort is agy-only" >&2; return 2; }
  command -v "$agent" >/dev/null 2>&1 || {
    echo "hmad-dispatch: exec requires the $agent CLI on PATH" >&2; return 2; }
  [ -n "$cd_dir" ] || cd_dir="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  local label; label="$(basename "$cd_dir")"

  local auto_log=""
  if [ -z "$log" ]; then
    log="$(mktemp -t hmad_exec_log.XXXXXX)" || return 1
    auto_log=1
    echo "hmad-dispatch: exec: transcript -> $log" >&2
  fi

  # J29: snapshot --out BEFORE the agent runs, so each write site below can tell
  # "the caller handed us a stale file" (legitimate — the no_verdict remedy
  # re-dispatches to the same templated path) from "another dispatch wrote here
  # while we ran" (the clobber). Empty for an absent/empty file.
  local out_fp=""
  [ -n "$out" ] && out_fp="$(_out_fingerprint "$out")"

  # `|| rc=$?` keeps a non-zero agent exit from tripping `set -e` before we capture
  # it — the exit code is the whole point of this verb. rc stays 0 on success.
  local rc=0 final_empty=0 verdict="" pre_lines=0
  # J23: append the SAME boundary `send` appends, so verdict recovery can tell our
  # echoed prompt from the agent's answer. Delivered to both backends: codex echoes
  # its stdin into the transcript (the defect), and agy does not — but a caller can
  # point --log at a file that already holds echoed content. Both backends append
  # their transcript to a caller-supplied log, preserving its existing content.
  local boundary; boundary="$(_dispatch_boundary)"
  local bounded_prompt; bounded_prompt="$(mktemp -t hmad_exec_prompt.XXXXXX)" || return 1
  { cat "$promptfile"; printf '\n%s\n' "$boundary"; } > "$bounded_prompt"
  # Dispatch-start marker for the heartbeat's elapsed field. Set before the start
  # stamp so every stamp in this dispatch measures from the same origin.
  _HMAD_EXEC_T0="$SECONDS"
  _exec_stamp start "$agent" "$label" "$cd_dir" || true
  local heartbeat_sec="${HMAD_EXEC_HEARTBEAT_SEC:-120}"
  if [ "$agent" = codex ]; then
    local last; last="$(mktemp -t hmad_exec_last.XXXXXX)" || { rm -f "$bounded_prompt"; return 1; }
    local args=(exec --cd "$cd_dir" --sandbox "$sandbox"
                --output-last-message "$last" --skip-git-repo-check)
    [ -n "$model" ] && args+=(--model "$model")
    # Prompt via stdin ('-') — no keystroke cap. Transcript is the live progress
    # signal (the --output-last-message file only lands at completion, so it is
    # NOT tailable). Transcript always goes to the log (a direct redirect, not a
    # pipe, so the codex exit code survives) so a watcher can `tail -f` a headless
    # run. rc comes from the codex process.
    _HMAD_EXEC_BEAT_LOG="$log"
    _exec_run --heartbeat "$agent" "$label" "$cd_dir" "$heartbeat_sec" \
      "$timeout" codex "${args[@]}" - < "$bounded_prompt" >> "$log" 2>&1 || rc=$?
    _HMAD_EXEC_BEAT_LOG=""
    if [ -s "$last" ]; then
      verdict="$(cat "$last")"
      [ -n "$out" ] && _out_clobber_ok "$out" "$out_fp" && cp "$last" "$out"
      cat "$last"
      [ -n "$auto_log" ] && cat "$log" >&2 || true
      [ -n "$auto_log" ] && rm -f "$log"
    else
      final_empty=1
    fi
    rm -f "$last"
  else
    # agy `--print` prints ONLY the response to stdout (verified), so no last-message
    # file. Headless needs --dangerously-skip-permissions or a tool request blocks
    # until the print timeout; agy is already launched that way in panes. cwd is agy's
    # workspace root, so cd there. Prompt is an arg, bounded only by ARG_MAX (~1MB);
    # audit prompts run 16-90KB and a >90KB exec prompt was confirmed answered, so the
    # arg is never the limit. --timeout maps to BOTH agy's native --print-timeout and the watchdog.
    # `--print` consumes the NEXT token as the prompt, so it MUST come last with the
    # prompt adjacent — every other flag goes before it. (A `--print` not adjacent to
    # the prompt silently ate the following flag as its prompt and dropped the real
    # one; agy then just greeted. Verified live.)
    local prompt; prompt="$(cat "$bounded_prompt")"
    local args=(--dangerously-skip-permissions)
    [ -n "$model" ] && args+=(--model "$model")
    [ -n "$effort" ] && args+=(--effort "$effort")
    [ -n "$sandbox" ] && args+=(--sandbox)
    [ -n "$timeout" ] && args+=(--print-timeout "${timeout}s")
    # stream-json BEFORE --print, like every other flag: `--print` consumes the
    # next token as its prompt, so a flag placed after it is eaten as the prompt
    # and the real prompt is dropped (the failure documented above — agy just
    # greeted). This is the live-progress channel; see `_agy_ndjson_response`.
    args+=(--output-format stream-json)
    args+=(--print "$prompt")
    local resp
    # Line count of any PRE-EXISTING log content, captured before the agent runs.
    # Everything the response extractor reads is scoped past this mark, so a
    # caller pointing --log at a file that already holds a previous dispatch's
    # stream cannot have that run's `result` event mistaken for this one's.
    if [ -f "$log" ]; then pre_lines="$(wc -l < "$log" 2>/dev/null | tr -d " ")"; fi
    [ -n "$pre_lines" ] || pre_lines=0
    # Append-direct into $log, NOT into a private temp file: that indirection is
    # exactly what made agy's --log dead-until-exit. Direct redirect (no pipe, no
    # process substitution) so agy's exit code survives and every NDJSON line is
    # on disk the moment agy flushes it — which is what makes `tail -f "$log"`
    # and `hmad-dispatch progress "$log"` show work in flight.
    # Appending (>>) preserves any caller-supplied content already in the file.
    _HMAD_EXEC_BEAT_LOG="$log"
    ( cd "$cd_dir" && _exec_run --heartbeat "$agent" "$label" "$cd_dir" "$heartbeat_sec" \
      "$timeout" agy "${args[@]}" ) >> "$log" 2>/dev/null || rc=$?
    _HMAD_EXEC_BEAT_LOG=""
    resp="$(_agy_ndjson_response "$log" "$pre_lines")"
    verdict="$resp"
    if [ -n "$resp" ]; then
      [ -n "$out" ] && _out_clobber_ok "$out" "$out_fp" && printf '%s\n' "$resp" > "$out"
      printf '%s\n' "$resp"
      # An auto-log is dumped as a DIGEST, not raw: the raw stream is NDJSON with
      # full tool payloads embedded, and spraying that at stderr buries the very
      # signal the operator opened it for. `progress` renders the same events as
      # one line each.
      [ -n "$auto_log" ] && _render_progress "$log" 40 >&2 || true
      [ -n "$auto_log" ] && rm -f "$log"
    else
      final_empty=1
    fi
  fi
  rm -f "$bounded_prompt"

  if [ "$final_empty" -eq 1 ]; then
    local msg
    if [ "$rc" -eq 0 ]; then
      rc=3
      msg="reporting channel failed (agent exited 0, no final message)"
    else
      msg="agent exited ${rc} with no final message"
    fi
    echo "hmad-dispatch: exec: EMPTY final message — ${msg}; transcript: $log" >&2
    local recovered
    local echo_expected=0
    [ "$agent" = codex ] && echo_expected=1
    if [ "$agent" = agy ]; then
      # agy's transcript is NDJSON now, so the line-oriented recovery below finds
      # nothing: a `^STATUS:` anchor cannot match text nested inside a JSON
      # string. Recover through the stream's own structure instead. This is also
      # STRICTLY better than what the text-mode path could do — a watchdog KILL
      # used to leave an empty capture file and nothing else, whereas the stream
      # has every completed agent_response already on disk.
      recovered="$(_agy_ndjson_response "$log" "$pre_lines")"
      # Only a verdict-carrying line is worth promoting to --out; a partial
      # narration is not, and writing one would hand the caller a fabricated
      # answer of exactly the kind J23 records.
      if [ -n "$recovered" ] \
        && ! printf '%s\n' "$recovered" | grep -aqE '^(STATUS|VERDICT|ASSESSMENT):'; then
        recovered=""
      fi
      # DEGRADED fallback, kept deliberately. The structured read above assumes
      # the transcript is the NDJSON stream this wrapper asked for, and there are
      # real ways for it not to be: an agy build that does not know
      # `--output-format`, a caller-supplied --log holding plain-text content, or
      # a stream that died before its first event. The line-oriented scan is what
      # `exec agy` recovery has always used and it costs nothing to keep behind
      # the structured path, so the change is additive rather than a swap.
      [ -n "$recovered" ] || recovered="$(_verdict_after_boundary "$log" "$boundary" 0)"
    else
      recovered="$(_verdict_after_boundary "$log" "$boundary" "$echo_expected")"
    fi
    if [ -n "$recovered" ]; then
      echo "hmad-dispatch: exec: verdict recovered from log ($log)" >&2
      verdict="$recovered"
      printf '%s\n' "$recovered"
      [ -n "$out" ] && _out_clobber_ok "$out" "$out_fp" && printf '%s\n' "$recovered" > "$out" || true
    fi
    if git -C "$cd_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      local delta
      # J23: the `-- .` pathspec is load-bearing. `git -C <subdir> status --porcelain`
      # reports the ENTIRE work tree, so a --cd into a subdirectory counted unrelated
      # dirt elsewhere in the repo. Measured: `--cd .../hematology-paper-writer` said
      # "1 changed" for a pre-existing file one directory ABOVE it, while
      # `git status --short .` there was empty. The recovery protocol reads a non-zero
      # delta as "the work landed, only the report failed", so a false non-zero argues
      # against re-dispatching a task that in fact never ran.
      delta="$(git -C "$cd_dir" status --porcelain -- . 2>/dev/null | grep -c . || true)"
      echo "hmad-dispatch: exec: tree delta: ${delta} changed in $cd_dir" >&2
    else
      echo "hmad-dispatch: exec: tree delta: n/a ($cd_dir not a git repo)" >&2
    fi
  fi

  _exec_stamp exit "$agent" "$label" "$cd_dir" "$rc" "${verdict:-no-verdict}" || true
  _cmd_notify "$agent exec" "rc=$rc verdict=${verdict:-no-verdict}" || true

  echo "hmad-dispatch: $agent exec rc=$rc" >&2
  return "$rc"
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
    *) _unknown_opt read "$1"; return $? ;; esac; done
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
  # J3: this took a 6-line TAIL, and _wait_stable returns idle as soon as two
  # snapshots match -- so two identical *stale* tails read as proof of idleness.
  # That is exactly what J3 observed: an unchanged boot screen across three polls
  # while the pane was actually at a ready prompt, because the tail was rendering
  # an overdrawn region of the frame. During the J13 probes a pane likewise sat
  # unchanged at "Thought for 5s, 305 tokens" for minutes before producing
  # output. A `wait` built on tails can therefore report idle mid-generation, and
  # the orchestrator then reads a report that has not been written.
  #
  # A bigger tail is not the fix -- J3's was already 40 lines. Reading from the
  # start of the buffer is, because it cannot be an overdrawn slice of one frame.
  # The extra bytes cost nothing that matters at a 3s poll interval.
  case "$1" in
    # cmux has no cursor addressing; a deeper read is the best available there.
    cmux) cmux read-screen --surface "$2" --lines "${HMAD_SNAPSHOT_LINES:-400}" ;;
    orca) orca terminal read --terminal "$2" --cursor 0 --limit "${HMAD_SNAPSHOT_LINES:-4000}" ;;
  esac
}

# True when *frame* clears every gate: each newline-separated until-pattern must
# match (AND, since grep -E cannot express conjunction), and the not-while
# alternation must NOT match. Empty gates are vacuously satisfied.
_frame_satisfies() {   # $1 frame, $2 until-regex(newline-joined), $3 not-while-regex(|-joined)
  local frame="$1" until_re="$2" not_while_re="$3" pat
  if [ -n "$not_while_re" ] && printf '%s' "$frame" | grep -Eq -- "$not_while_re"; then
    return 1
  fi
  if [ -n "$until_re" ]; then
    while IFS= read -r pat; do
      [ -z "$pat" ] && continue
      printf '%s' "$frame" | grep -Eq -- "$pat" || return 1
    done <<EOF
$until_re
EOF
  fi
  return 0
}

# Two consecutive identical snapshots. A single read can catch a pane
# mid-write; two matching ones cannot.
#
# Stability alone is not completion. A pane parked on "Waiting for background
# terminal" (Codex delegated the real work to a background terminal) is a static
# frame: two snapshots match and native tui-idle is satisfied while generation is
# still in flight. So two optional gates promote a stable frame to "done":
#   $4 until-regex     — required positive evidence; a stable frame that lacks it
#                        keeps polling (silence/echo never satisfy it).
#   $5 not-while-regex — a known-busy marker; while it matches, a stable frame is
#                        NOT done, mirroring "tui-idle's not-idle is authoritative".
_wait_stable() {   # $1 substrate, $2 target, $3 timeout, [$4 until-regex] [$5 not-while-regex]
  local sub="$1" target="$2" timeout="$3" until_re="${4:-}" not_while_re="${5:-}"
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
    if [ -n "$cur" ] && [ "$cur" = "$prev" ]; then
      if _frame_satisfies "$cur" "$until_re" "$not_while_re"; then
        return 0
      fi
    fi
    prev="$cur"
    [ "$interval" -gt 0 ] && sleep "$interval"
    elapsed=$((elapsed + tick))
  done
  return 1
}

_cmd_wait() {
  local agent="$1"; shift
  local timeout=300 until_re="" not_while_re=""
  while [ $# -gt 0 ]; do case "$1" in
    --timeout) timeout="$2"; shift 2 ;;
    # Positive-evidence gate: don't call a stable frame done until it matches.
    # For a 5d/5e GREEN that is the verdict line AND a full-suite result, e.g.
    #   --until-regex 'STATUS:.*(DONE|BLOCKED|NEEDS_CONTEXT)' --until-regex '[0-9]{3,4} passed'
    # (repeatable — every occurrence must match).
    --until-regex) until_re="${until_re:+$until_re
}$2"; shift 2 ;;
    # Known-busy marker: while it shows, a stable frame is not done.
    --not-while-regex) not_while_re="${not_while_re:+$not_while_re|}$2"; shift 2 ;;
    *) _unknown_opt wait "$1"; return $? ;;
  esac; done
  # Multiple --until-regex are ALL required; passed newline-joined, ANDed per
  # frame by _frame_satisfies. Multiple --not-while-regex are |-joined (any hit
  # means still busy).
  local sub target; sub="$(_detect_substrate)" || return 1
  target="$(_resolve_target "$agent")" || return 1
  case "$sub" in
    orca)
      # Orca's native `--for tui-idle` has been observed reporting satisfied
      # while an agent was still generating, so it is a fast first gate, not
      # proof: its "not idle" is authoritative, its "idle" is not. Confirm
      # with the same stability comparison cmux has always relied on.
      orca terminal wait --terminal "$target" --for tui-idle --timeout-ms "$(( timeout * 1000 ))" || return 1
      _wait_stable "$sub" "$target" "$timeout" "$until_re" "$not_while_re" ;;
    cmux)
      # No native idle in cmux at all — stability is the only signal.
      _wait_stable "$sub" "$target" "$timeout" "$until_re" "$not_while_re" ;;
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
    verify) _cmd_verify "$@" ;;
    launch) _cmd_launch "$@" ;;
    pin) _cmd_pin "$@" ;;
    pin-agents) _cmd_pin_agents "$@" ;;
    send)   _cmd_send "$@" ;;
    ask)    _cmd_ask "$@" ;;
    exec)   _cmd_exec "$@" ;;
    clear)  _cmd_clear "$@" ;;
    interrupt) _cmd_interrupt "$@" ;;
    read)   _cmd_read "$@" ;;
    wait)   _cmd_wait "$@" ;;
    alive)  _cmd_alive "$@" ;;
    notify) _cmd_notify "$@" ;;
    progress) _cmd_progress "$@" ;;
    run-ensure) _require_orca run-ensure && _run_ensure ;;
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
    worktree-list) _cmd_worktree_list "$@" ;;
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
