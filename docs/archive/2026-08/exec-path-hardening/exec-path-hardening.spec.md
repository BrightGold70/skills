# Spec: exec-path-hardening

## Executive Summary

`hmad-dispatch exec` gains mandatory, best-effort observability stamped from inside
`_cmd_exec` — a durable mobile-visible worktree comment at start, during, and at exit, plus
a desktop notification at exit — under a hard invariant that none of it may alter `rc`,
stdout, or dispatch timing; and the codex/agy `--log` truncation asymmetry is resolved into
one stated contract.

## Goal

An operator away from the desk can tell, from the Orca worktree card alone, whether a
headless `exec` dispatch is running, finished, or died — without opening a terminal, and
without the observability itself being able to break the dispatch it observes.

## Functional Requirements

### FR-1: Durable start/exit checkpoints on the worktree card

- **Description**: `_cmd_exec` stamps an Orca worktree comment when the subprocess is
  launched and again when it exits. The exit stamp carries the agent, `rc`, and the verdict
  token when one is present on stdout. Both are best-effort: any failure is silent and
  changes nothing about the dispatch. Under a non-Orca substrate the stamps are a no-op.
- **Acceptance Criteria**:
  - AC-1.1: With substrate `orca`, a successful `exec codex` produces at least two
    `worktree set --comment` invocations — one before the agent process starts, one after it
    exits — observable in a stubbed-orca invocation log.
  - AC-1.2: The exit comment text contains the agent token (`codex`/`agy`), the literal
    `rc=<n>` matching the process exit code, and the extracted verdict value when stdout
    carries a `STATUS:`/`VERDICT:` line.
  - AC-1.3: With substrate `cmux`, an `exec` dispatch issues **zero** `worktree set`
    invocations and its stdout, stderr verdict diagnostics, and `rc` are byte-identical to
    the same run with the feature absent.
  - AC-1.4: When the `orca` CLI exits non-zero for the comment call, `exec` still returns
    the agent's own `rc` and its stdout is unchanged.
  - AC-1.5: When the `orca` CLI hangs on the comment call, the dispatch is not blocked
    indefinitely — the comment call is bounded and abandoned.

### FR-2: Liveness heartbeat while the subprocess runs

- **Description**: While the agent subprocess is alive, `_cmd_exec` refreshes a **single
  rolling** worktree comment (overwrite, never an append trail) at a bounded interval, so a
  long run is distinguishable from a dead one on the card. The heartbeat rides the existing
  `kill -0` liveness poll in `_run_with_timeout` rather than adding a second poller.
  Interval is `HMAD_EXEC_HEARTBEAT_SEC`, default `120`; `0` disables it.
- **Acceptance Criteria**:
  - AC-2.1: A stubbed agent that stays alive across more than one interval produces more
    than one heartbeat comment, and each heartbeat call is an overwrite (`worktree set
    --comment`) — never an append of prior text.
  - AC-2.2: The heartbeat text distinguishes elapsed time (a monotonically non-decreasing
    elapsed value across successive stamps for one dispatch).
  - AC-2.3: `HMAD_EXEC_HEARTBEAT_SEC=0` produces zero heartbeat comments while start/exit
    checkpoints (FR-1) still fire.
  - AC-2.4: An `exec` invoked **without** `--timeout` (no `_run_with_timeout` wrapper) still
    emits heartbeats, or the spec's chosen mechanism is documented as timeout-path-only and
    the no-timeout case is explicitly asserted to emit start/exit only. One of the two must
    be pinned by a test; silence on this case is a failure.
  - AC-2.5: A failing heartbeat call does not terminate the dispatch, alter `rc`, or write
    to stdout.

### FR-3: Desktop notification at exit (not a mobile surface)

- **Description**: `_cmd_exec` fires `_cmd_notify` once when the dispatch exits, carrying
  agent, `rc`, and verdict. Under Orca this is `osascript display notification` — a **local
  macOS desktop** notification. It is explicitly *not* the mobile channel; FR-1/FR-2 are.
  Recorded here so a later reader does not mistake it for push.
- **Acceptance Criteria**:
  - AC-3.1: Exactly one notify invocation per `exec` dispatch, fired after the agent exits.
  - AC-3.2: The notify body contains `rc=<n>` matching the agent's exit code.
  - AC-3.3: A failing notify call leaves `rc` and stdout unchanged (`_cmd_notify` already
    returns 0 unconditionally; this AC pins that it stays that way).

### FR-4: Observability cannot corrupt the verdict channel or the exit code

- **Description**: The load-bearing invariant. `exec`'s stdout is the verdict carrier and
  its `rc` is the operational signal; every surface added by FR-1–FR-3 writes to stderr or
  nowhere, and no surface's failure may propagate into `rc`.
- **Acceptance Criteria**:
  - AC-4.1: For a clean `exec codex` and a clean `exec agy`, stdout is byte-identical with
    all surfaces enabled and with all surfaces disabled.
  - AC-4.2: For the `rc 3` empty-final-message path, stdout (including a recovered verdict)
    and the `EMPTY final message` / `tree delta:` stderr diagnostics are byte-identical with
    and without the surfaces.
  - AC-4.3: With every surface stubbed to fail non-zero, `exec` returns the agent's own exit
    code for at least: success (0), agent crash (non-zero), watchdog timeout (124), and
    empty-final-message (3).
  - AC-4.4: Mutation-verified — each guard above is mutated to its permissive value via
    `h_mad_mutation_harness.py` and a test fails for every mutation. Message-content
    assertions where the message is the load-bearing part, per J22/J23.

### FR-5: One stated `--log` truncation contract across both backends

- **Description**: Today codex redirects `> "$log"` (truncates a caller-supplied log before
  the run) while agy appends `>> "$log"`. The comment at `scripts/hmad-dispatch.sh:1898`
  justifies appending the boundary on both backends by reasoning that "a caller can point
  `--log` at a file that already holds echoed content" — which is false for codex, on the
  channel the recovery protocol names as the one observed to outlive the others. Resolve to
  a single contract: either make codex append, or state truncation as the contract and
  correct the comment plus `SKILL.md`. Not both.
- **Acceptance Criteria**:
  - AC-5.1: A test asserts the chosen contract for **codex** against pre-existing
    `--log` content: preserved (append) or documented-and-asserted as discarded.
  - AC-5.2: The equivalent agy assertion exists and the two agree, or the divergence is
    stated in `SKILL.md` with its reason.
  - AC-5.3: `test_agy_empty_response_recovers_verdict_from_caller_log` still passes
    unchanged — the agy recovery path from caller-log content is a shipped behaviour and is
    a regression guard here, not something this feature may renegotiate.
  - AC-5.4: The `scripts/hmad-dispatch.sh:1898` comment and the `SKILL.md` recovery section
    state the same contract the code implements.

### FR-6: Comment target resolution

- **Description**: The stamped comment targets the worktree the work lands in — the one
  containing `--cd` — not unconditionally the coordinator's active worktree. They diverge
  whenever `exec --cd` points at a sibling checkout, which is the Phase-5 fanout shape.
  Falls back to `active` when the `--cd` path cannot be mapped to a worktree.
- **Acceptance Criteria**:
  - AC-6.1: With `--cd` inside a worktree that `worktree ps` lists, the comment call targets
    that worktree's selector, not `active`.
  - AC-6.2: With `--cd` at a path no listed worktree contains, the comment call targets
    `active` and the dispatch proceeds normally.
  - AC-6.3: An unreadable or `truncated` `worktree ps` **never fails the dispatch**. It falls
    back to `active` only when `active`'s own current comment was read in the same payload;
    when no target's comment is readable, the stamp is abandoned and zero `worktree set` calls
    are issued. *(Amended v1.2 — v1.0 said "falls back to `active`" unconditionally, which was
    written before the no-clobber requirement existed. Targeting `active` without having read
    its comment would overwrite an unread checkpoint, i.e. cause the exact data loss the read
    exists to prevent, on a worktree that is not even the one the work ran in.)*

## Non-Functional Requirements

- **Performance**: Each stamp costs **2 bounded `orca` calls** — one `worktree ps` (which
  resolves the selector and returns the current comment in the same payload) and one
  `worktree set`. Start + exit is therefore 4 calls; each `HMAD_EXEC_HEARTBEAT_SEC` interval
  (default 120 s) adds 2. Worst case at the default interval against a 900 s dispatch is
  roughly 18 bounded calls, all off the critical path and negligible against the dispatch.
  The read is not cacheable: the comment is a shared mutable field and a `handoff` write from
  another session can land between our read and our next write, so caching would reintroduce
  the clobber the composition rule exists to prevent. No new polling process.
  *(Amended v1.1 — v1.0 said "≤ 2 bounded calls" for start + exit, which read-then-compose
  cannot meet; the constraint was incompatible with the no-clobber requirement.)*
- **Security**: N/A — no new external dependency, no credentials, no network. Comment text
  is wrapper-authored; agent output is not interpolated into it beyond the validated verdict
  token, so an agent cannot inject arbitrary text into a worktree comment.
- **Compatibility**: cmux is unaffected (FR-1 AC-1.3). All 45 existing
  `test_hmad_dispatch_exec.py` tests must pass unchanged. `~/.claude/skills/h-mad` is a
  symlink into this repo, so both coupled suites run before merge.

## Out-of-Scope

- Re-opening any shipped exec defect: rc-3 empty-message handling, the
  `===HMAD-DISPATCH-BOUNDARY===` anti-laundering slice and its per-backend fail-closed
  behaviour, `--cd`-scoped `tree delta`, `_run_with_timeout` pgroup kill, and the agy
  report-file/F-10 mitigation. These are the explicit non-scope; an audit finding against
  them is a scope violation, not a defect.
- Orca task/dispatch **provenance** for exec-run work — structurally impossible
  (`worker_done` must originate from the dispatched terminal; `sender_not_assignee`
  measured) and forbidden by the Orca guide.
- Replacing `exec` with orchestration, or adding an orchestration fallback.
- Backfilling `docs/skill-monitoring.md` with J19–J23 (unfiled since 2026-07-23). Real gap,
  separate feature: it is registry hygiene, shares no code with this one, and folding it in
  would make this feature's gates score doc edits.
- Push-to-mobile notification. No such channel exists in `hmad-dispatch` today; the
  worktree comment is the mobile surface.

## Assumptions

- `_cmd_worktree_comment` remains Orca-only via `_require_orca`, so the cmux no-op is
  inherited rather than re-implemented.
- ~~`worktree set --comment` is an overwrite, so a rolling heartbeat needs no
  read-modify-write.~~ **Falsified in Phase 3.** It is an overwrite, and that is exactly why a
  read is mandatory: the field is shared with `handoff` WRITE/TAKEOVER and with humans, and a
  live worktree was observed holding a `handoff:` resume checkpoint at probe time. A rolling
  heartbeat must read-then-compose, replacing only its own prior `h-mad` stamp and preserving
  everything else.
- The existing exec test harness (`_bindir` stubs, `HMAD_STUB_*` env) can stub the `orca`
  CLI and count invocations. If it cannot, adding that stub is in scope as plumbing.
- Elapsed time is measured off bash's `SECONDS`, consistent with `_run_with_timeout`.

## Version History

- v1.0: Initial specification draft.
- v1.1: Back-propagated from plan audit cycle 2. Performance NFR amended — the v1.0 bound of
  "≤ 2 bounded `orca` calls" for start + exit was incompatible with the no-clobber composition
  requirement, which needs a read before every write. Restated as 2 calls per stamp with the
  reason the read cannot be cached. Also corrected the v1.0 assumption that overwrite
  semantics meant no read-modify-write was needed: overwriting is precisely why the read is
  required.
- v1.2: Back-propagated from plan audit cycle 5. AC-6.3 amended — v1.0's unconditional "falls
  back to `active`" predated the no-clobber requirement and would have written to `active`
  without having read its comment, causing the very data loss the read prevents, on a worktree
  the work did not even run in. Root cause: v1.0 conflated two reads — *which worktree to
  target* (selector resolution) and *what the field currently holds* (clobber avoidance). Per
  A3 one `worktree ps` payload answers both, so they succeed or fail together, and a
  resolution fallback cannot be chosen independently of whether a comment was read. The
  dispatch-never-fails guarantee is unchanged.
