# Implementation Plan: exec-path-hardening

> Source: docs/02-design/features/exec-path-hardening.design.md (post-audit, v1.4, GATE PASS cycle 5)
> Branch target: feature/213-exec-path-hardening

## Executive Summary

Twelve tasks: four leaf units and the stub plumbing first, then the `_exec_run` unification,
then five `wiring` tasks that connect each surface into `_cmd_exec`, then the `--log` append
contract and docs.

## Task 1: exec-comment-compose

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_exec_stamp.py`
**Task shape**: `new-behaviour`

**Description**: Pure string function placing a complete h-mad stamp span into an existing
comment. Recognises a span by the fixed `h-mad: ` lead-in and fixed `⟦/h-mad⟧` terminator,
replaces it **wherever it occurs** (not only at the start), appends once when absent, and
emits the stamp alone when the current comment is empty. Locating by content rather than
prefix is what makes repeated heartbeats idempotent — a prefix rule appends to a human
comment, after which the string no longer starts with the stamp and every later heartbeat
appends again.

**Code structure**:
```bash
# $1 = current comment (may be empty, may contain newlines/tabs)
# $2 = complete stamp span, e.g. 'h-mad: codex skills · running · 4m⟦/h-mad⟧'
# stdout = composed comment. Always rc 0.
_exec_comment_compose() { :; }
```

**Acceptance Criteria**:
- [ ] AC-1.1: `_exec_comment_compose "" "$STAMP"` outputs exactly `$STAMP`.
- [ ] AC-1.2: With current `Fixing issue`, output is `Fixing issue · $STAMP` (appended once).
- [ ] AC-1.3: With current `handoff: slug · state · next: x`, the full handoff text is present
      byte-identically in the output and the stamp follows it.
- [ ] AC-1.4: Composing 5 times, feeding each output back in with a different `<state>`,
      yields exactly one `h-mad: ` occurrence and one `⟦/h-mad⟧` occurrence, and the final
      output length equals the length after the 1st compose (± the state-text delta only).
- [ ] AC-1.5: With current `pre h-mad: old⟦/h-mad⟧ post`, output is `pre $STAMP post` — bytes
      before and after the span preserved exactly.
- [ ] AC-1.6: A malformed half-span (`lead-in present, terminator absent`) is treated as NOT a
      span: the stamp is appended and the malformed text is preserved, with no truncation to
      an unbounded end offset.
- [ ] AC-1.7: A current comment containing `\n` and `\t` round-trips byte-identically into the
      output.

**Dependencies on other tasks**: None

---

## Task 2: orca-stub-stateful-comment

**Test stub (target file)**: `h-mad/tests/stubs/orca` — a test stub, not production code
**Test file**: `h-mad/tests/test_hmad_dispatch_exec_stamp.py`
**Task shape**: `new-behaviour`

**Description**: Give the existing `orca` stub an optional comment round-trip so a
multi-interval heartbeat test is not blind. `worktree set --comment <v>` persists `<v>` to the
path in `HMAD_STUB_ORCA_STATE`; `worktree ps` serves the persisted value back in its payload.
With the env var unset the stub behaves exactly as today, matching the existing
"consulted only when explicitly set" precedent used by `HMAD_STUB_ORCA_WT_PS_STDOUT` and
`HMAD_STUB_ORCA_TASKLIST_STDOUT`. There is deliberately **no default path**: a shared or
hardcoded temp file is how a mutation run once clobbered live session state while reporting
green (J18).

**Code structure**:
```bash
# In tests/stubs/orca, consulted only when HMAD_STUB_ORCA_STATE is set:
#   worktree set --comment <v>  -> persist <v> to $HMAD_STUB_ORCA_STATE
#   worktree ps                 -> emit payload whose matching entry carries that comment
```

**Acceptance Criteria**:
- [ ] AC-2.1: With `HMAD_STUB_ORCA_STATE` unset, every existing test in
      `test_hmad_dispatch.py` and `test_hmad_dispatch_exec.py` passes unchanged.
- [ ] AC-2.2: With it set, `worktree set --comment X` then `worktree ps` yields an entry whose
      `.comment` is `X`.
- [ ] AC-2.3: The round-trip preserves a value containing a newline and a tab byte-identically.
- [ ] AC-2.4: Two tests using different `HMAD_STUB_ORCA_STATE` paths do not observe each
      other's values.

**Dependencies on other tasks**: None

---

## Task 3: exec-wt-target

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_exec_stamp.py`
**Task shape**: `new-behaviour`

**Description**: Resolve the stamp target and read its current comment from **one**
`orca worktree ps --limit 200 --json` call. Emits two lines — selector, then the comment
base64-encoded — or nothing with rc 1. Base64 because a comment is free text that may contain
newlines and tabs; a tab-joined single line consumed with `read -r` would keep only the first
line and the composer would write that truncation back, a partial-clobber bug invisible to
single-line tests. The `orca` call is bounded and `</dev/null`-guarded exactly like the write.

**Code structure**:
```bash
# $1 = cd_dir. stdout: line1 = selector, line2 = base64(current comment). rc 1 = abandon.
# Extraction MUST be `(.comment // "") | @base64` — bare `.comment | @base64` does not fail
# on null, it emits base64 of the literal string "null" (probe A7).
# Reads .result.worktrees[] / .result.truncated (NOT the unwrapped shape `worktree-ps` prints).
_exec_wt_target() { :; }
```

**Acceptance Criteria**:
- [ ] AC-3.1: `--cd` equal to a listed `.path` returns that entry's `worktreeId` and its
      comment.
- [ ] AC-3.2: `--cd` inside a **subdirectory** of a listed worktree returns the enclosing
      worktree's `worktreeId`.
- [ ] AC-3.3: With worktrees `/x/repo` and `/x/repo-other` both listed, `--cd /x/repo-other`
      returns `repo-other`'s selector — never `repo`'s. (Boundary match: equal, or `.path + "/"`
      is a prefix of `cd_dir`.)
- [ ] AC-3.4: `--cd` matching no entry, with an `.isActive == true` entry present, returns the
      active entry's selector and comment.
- [ ] AC-3.5: A payload with no usable entry returns rc 1 and prints nothing.
- [ ] AC-3.6: A `truncated: true` payload that still contains the matching entry resolves
      normally (rc 0).
- [ ] AC-3.7: An entry whose `.comment` is `null`, and one where the key is absent, both yield
      a decoded comment of exactly the empty string — never the 4 bytes `null`.
- [ ] AC-3.8: A comment containing `\n` and `\t` decodes byte-identically.
- [ ] AC-3.9: An `orca` invocation that never exits is abandoned within the stamp timeout and
      returns rc 1 rather than hanging.
- [ ] AC-3.10: The read call does not consume the caller's stdin. Asserted **two ways, neither
      via argv** — a shell redirection changes file descriptors and never appears in a
      command's argv, so an argv-capture assertion here would be untestable and would pass with
      the guard removed. (a) A sentinel is placed on the caller's stdin as a single inherited
      descriptor (not re-opened) and is still fully readable after `_exec_wt_target` returns;
      (b) the stub records what it observes on its own fd 0, which must be empty/EOF.

**Mutation anchors** (each must be `ALL_CAUGHT`):

| # | Mutation (exact find → replace) | Test that must fail |
|---|---|---|
| M-7 | drop the `</dev/null` redirect on the `orca worktree ps` read call | AC-3.10 (both limbs) |
| M-8 | `(.comment // "")` → `.comment` in the jq extraction | AC-3.7 (decoded comment must be empty, never `null`) |
| M-9 | boundary test `"$p/"` → `"$p"` (bare string prefix) | AC-3.3 (`/x/repo` vs `/x/repo-other`) |

**Dependencies on other tasks**: Task 2 (stub payloads)

---

## Task 4: exec-stamp-emitter

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_exec_stamp.py`
**Task shape**: `new-behaviour`

**Description**: The sole comment writer. Builds the complete span — `_exec_stamp` owns the
whole format, the composer never assembles fields — gates on substrate, composes against a
supplied current comment, and issues one bounded, stdin-null `orca worktree set`. Returns 0
unconditionally on every path, writes nothing to stdout, and emits no stderr: a silent stamp
failure must not be mistaken for a dispatch diagnostic. Does **not** call
`_cmd_worktree_comment`, whose `_require_orca` prints and whose `_orca_json` echoes a whole
error envelope to stderr on `ok:false` — correct for an operator verb, wrong here.

**Code structure**:
```bash
# _exec_stamp <kind> <agent> <label> <cd_dir> [rc] [verdict]
#   kind = start|beat|exit
# The emitter resolves its own target+comment (via _exec_wt_target, wired in Task 6) and
# formats its own state text. Callers pass only facts they already hold; they never supply a
# selector, a current comment, or preformatted state — that would push the resolver call and
# the span format out to every call site and break the single-owner rule the design sets.
# Span is always:
#   h-mad: <agent> <label> · <state>⟦/h-mad⟧
# state: start='running · 0m'  beat='running · <n>m'  exit='rc=<n> · <verdict|no-verdict>'
_exec_stamp() { :; }   # always returns 0
```

Until Task 6 wires the resolver, `_exec_stamp` is exercised with `_exec_wt_target` stubbed at
the shell-function level, so Task 4's ACs test the emitter's own behaviour without presupposing
the wire.

**Acceptance Criteria**:
- [ ] AC-4.1: An `exit` stamp's composed text contains all three of: the agent token
      (`codex`/`agy`), the literal `rc=<n>`, and the verdict value.
- [ ] AC-4.2: `start` and `beat` spans also contain the agent token and the label — not the
      state alone.
- [ ] AC-4.3: Under substrate `cmux`, zero `orca` invocations are recorded.
- [ ] AC-4.4: With the `orca` stub exiting non-zero, `_exec_stamp` still returns 0 and prints
      nothing on stdout or stderr.
- [ ] AC-4.5: With the `orca` stub hanging, `_exec_stamp` returns 0 within the stamp timeout.
- [ ] AC-4.6: `_exec_stamp` writes zero bytes to stdout on every path.
- [ ] AC-4.7: The `worktree set` call is recorded with `--comment` carrying the composed value.
- [ ] AC-4.8: The **write** call does not consume the caller's stdin: a sentinel on an inherited
      stdin descriptor is fully readable after `_exec_stamp` returns, and the stub records
      EOF on its own fd 0. (Write-scoped twin of AC-3.10; asserted without argv, per the same
      reason.)

**Mutation anchors** (each must be `ALL_CAUGHT`):

| # | Mutation (exact find → replace) | Test that must fail |
|---|---|---|
| M-4 | substrate gate `[ "$sub" = orca ]` → `[ 1 -eq 1 ]` (stamp under any substrate) | AC-4.3 (cmux → zero `orca` calls) |
| M-5 | trailing `return 0` → `return "$rc"` (propagate the orca failure) | AC-4.4 |
| M-6 | drop the `</dev/null` redirect on the `worktree set` **write** call | AC-4.8 (below) — NOT Task 3's AC-3.10, which is scoped to the read call and would not fail on a write-call mutation |

**Dependencies on other tasks**: Task 1, Task 2

---

## Task 5: exec-run-unification

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_exec.py`
**Task shape**: `refactor`

**Description**: Rename `_run_with_timeout` to `_exec_run` and make the deadline optional so a
dispatch without `--timeout` still backgrounds, polls and reaps — giving the heartbeat one
attachment point for both cases. The heartbeat is **opt-in** via `--heartbeat`: `_exec_run`
owns the heartbeat hook and `_exec_stamp` calls `_exec_run`, so an implied heartbeat would
recurse `_exec_stamp → _exec_run → _exec_stamp` unbounded for any `HMAD_EXEC_HEARTBEAT_SEC`
shorter than the stamp timeout. Both existing call sites collapse to one per backend. Only two
callers exist today, both inside `_cmd_exec`, so no other verb is affected.

**Code structure**:
```bash
# _exec_run [--heartbeat <agent> <label> <cd_dir> <interval_secs>] <secs|""> <cmd...>
#   ("" for <secs> = no deadline)
# The heartbeat context is passed EXPLICITLY, never read from the environment inside this
# function: `_cmd_exec` is the sole reader of HMAD_EXEC_HEARTBEAT_SEC (as the design states)
# and forwards it as <interval_secs>. A zero-argument flag could not call
# `_exec_stamp beat <agent> <label> <cd_dir>` at all, and reading the env var here would both
# contradict the design and make recursion-safety a property of configuration.
# Preserved verbatim as regression guards: `<&0` stdin handoff; `set -m` fresh pgroup with the
# prior -m state restored; group TERM -> 2s polled grace -> KILL; absolute deadline off
# SECONDS; return 124 on timeout.
_exec_run() { :; }
```

**Acceptance Criteria**:
- [ ] AC-5.1: All 45 existing tests in `test_hmad_dispatch_exec.py` pass unchanged.
- [ ] AC-5.2: A dispatch **without** `--timeout` returns the agent's own exit code for success
      and for a crash.
- [ ] AC-5.3: A dispatch **with** `--timeout` still returns 124 when the agent outlives it.
- [ ] AC-5.4: `codex exec -` receives its complete piped prompt on both paths (the `<&0` guard).
- [ ] AC-5.5: A timed-out agent's grandchildren are killed (existing pgroup guard).
- [ ] AC-5.6: `_exec_run` accepts and consumes a leading `--heartbeat <agent> <label> <cd_dir>
      <interval>` without passing any of those five tokens to the child: the recorded agent
      argv is identical with and without the flag group. (The
      *behavioural* no-heartbeat assertion belongs to Task 9 — at this task the beat call does
      not exist yet, so "records zero stamps" would pass vacuously and certify nothing.)
- [ ] AC-5.7: A nested `_exec_run` inside a `--heartbeat` frame, captured via command
      substitution, returns its output intact and does not stall the outer reap.
- [ ] AC-5.8: `_exec_run` never reads `HMAD_EXEC_HEARTBEAT_SEC`: with the env var set to `1`
      but no `--heartbeat` group passed, zero beat stamps are recorded (a grep of the function
      body for the variable name is NOT sufficient — the assertion is behavioural).

**Dependencies on other tasks**: None

---

## Task 6: wire-stamp-to-resolver

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_exec_stamp.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/hmad-dispatch.sh:_exec_stamp` → `_exec_wt_target`
**WIRE-PIN**: `test_stamp_targets_the_cd_worktree_not_active`

**Description**: `_exec_stamp` calls `_exec_wt_target` to obtain its selector and current
comment, and abandons the stamp — issuing zero `worktree set` calls — when the resolver
returns rc 1. Both callee and caller already exist after Tasks 3 and 4; this task is the call.

**Acceptance Criteria**:
- [ ] AC-6.1: With `--cd` inside a listed worktree that is not the active one, the recorded
      `worktree set` targets that worktree's selector, not `active`.
- [ ] AC-6.2: When the resolver returns rc 1, **zero** `worktree set` calls are recorded and
      the pre-existing comment is byte-identical afterwards.
- [ ] AC-6.3: The `WIRE-PIN` test fails when only the `_exec_wt_target` call is removed
      (callee intact), and its failure is an assertion about the recorded target — not an
      `ImportError`/`AttributeError`/`NameError`.

**Dependencies on other tasks**: Task 3, Task 4

---

## Task 7: wire-exec-start-stamp

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_exec_stamp.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/hmad-dispatch.sh:_cmd_exec` → `_exec_stamp start`
**WIRE-PIN**: `test_start_stamp_is_written_before_the_agent_runs`

**Description**: `_cmd_exec` emits the start checkpoint before launching the agent, guarded
`|| true` so a non-zero cannot propagate under `set -e`.

**Acceptance Criteria**:
- [ ] AC-7.1: A successful `exec codex` under substrate `orca` records at least one
      `worktree set` **before** the first `codex` invocation in the capture file.
- [ ] AC-7.2: Under substrate `cmux` the same run records zero `worktree set` calls.
- [ ] AC-7.3: The `WIRE-PIN` fails when only the `_exec_stamp start` call is removed, asserting
      the absence of a pre-agent comment invocation.

**Dependencies on other tasks**: Task 4, Task 6

---

## Task 8: wire-exec-exit-stamp

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_exec_stamp.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/hmad-dispatch.sh:_cmd_exec` → `_exec_stamp exit`
**WIRE-PIN**: `test_exit_stamp_carries_agent_rc_and_verdict`

**Description**: `_cmd_exec` emits the exit checkpoint after the agent exits and after the
verdict is captured, carrying agent, `rc`, and verdict. Emitted on the `rc 3`
empty-final-message path too, where the verdict is `no-verdict` unless one was recovered.

**Acceptance Criteria**:
- [ ] AC-8.1: A clean run records a `worktree set` whose `--comment` contains the agent token,
      `rc=0`, and the verdict token.
- [ ] AC-8.2: A crashing agent records `rc=<its code>`.
- [ ] AC-8.3: The `rc 3` empty-final-message path also records an exit stamp.
- [ ] AC-8.4: The `WIRE-PIN` fails when only the `_exec_stamp exit` call is removed, asserting
      that no comment carries all three elements.

**Dependencies on other tasks**: Task 4, Task 6

---

## Task 9: wire-heartbeat

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_exec_stamp.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/hmad-dispatch.sh:_exec_run` → `_exec_stamp beat`
**WIRE-PIN**: `test_heartbeat_stamps_across_three_intervals`

**Description**: Inside `_exec_run`'s poll loop, when the `--heartbeat` group was passed and
`SECONDS - last_beat >= <interval_secs>` (the **parameter**, not the env var — `_cmd_exec`
remains the sole reader of `HMAD_EXEC_HEARTBEAT_SEC` and forwards it), emit
`_exec_stamp beat <agent> <label> <cd_dir>`. Interval `0` disables.
The interval is a wall-clock floor checked inside the existing 0.25 s poll, never a per-tick
action. `_cmd_exec` passes `--heartbeat` for the agent dispatch only.

**Acceptance Criteria**:
- [ ] AC-9.1: With `HMAD_EXEC_HEARTBEAT_SEC=1` and an agent alive ≥3 s, more than one beat
      stamp is recorded.
- [ ] AC-9.2: Successive beat stamps carry a monotonically non-decreasing elapsed value.
- [ ] AC-9.3: With `HMAD_EXEC_HEARTBEAT_SEC=0`, zero beat stamps are recorded while start and
      exit stamps still are.
- [ ] AC-9.4: A dispatch **without** `--timeout` spanning ≥3 intervals records beats at the
      same cadence as one with `--timeout`.
- [ ] AC-9.5: Against a stateful stub seeded with `handoff: keep-me`, after ≥3 beats the
      comment contains `handoff: keep-me` byte-identically and exactly one `h-mad: ` span.
- [ ] AC-9.6: With `HMAD_EXEC_HEARTBEAT_SEC` shorter than the stamp timeout, the dispatch
      terminates normally — no unbounded recursion.
- [ ] AC-9.7: A sentinel on the dispatch's stdin, **inherited** (not re-opened), is fully
      readable by the agent after heartbeats have fired.
- [ ] AC-9.8: The `WIRE-PIN` fails when only the beat call is removed, recording zero beats
      while start/exit remain.
- [ ] AC-9.9: (moved from Task 5, where it would have passed vacuously) `_exec_run` invoked
      **without** `--heartbeat` records zero beat stamps even with `HMAD_EXEC_HEARTBEAT_SEC=1`
      and a child outliving several intervals — now a real assertion, because the beat call
      exists at this task.

**Mutation anchors** (`h_mad_mutation_harness.py` spec; each must be `ALL_CAUGHT`):

| # | Mutation (exact find → replace) | Test that must fail |
|---|---|---|
| M-1 | heartbeat interval guard `[ "$hb" -gt 0 ]` → `[ 1 -eq 1 ]` (fire unconditionally) | AC-9.3 (interval `0` → zero beats) |
| M-2 | `--heartbeat` opt-in test → always-true (heartbeat implied) | AC-9.9 |
| M-4b | interval sourced from `$HMAD_EXEC_HEARTBEAT_SEC` instead of the passed parameter | AC-5.8 |
| M-3 | elapsed-floor comparison `>=` → `>= 0` (beat every tick) | AC-9.1's stamp-count bound |

**Dependencies on other tasks**: Task 4, Task 5, Task 6

---

## Task 10: wire-exit-notify

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_exec_stamp.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/hmad-dispatch.sh:_cmd_exec` → `_cmd_notify`
**WIRE-PIN**: `test_exit_notify_fires_once_with_rc`

**Description**: `_cmd_exec` fires exactly one `_cmd_notify` after the agent exits, with `rc`
and verdict in the body. This is a local desktop notification, not a mobile channel.

**Acceptance Criteria**:
- [ ] AC-10.1: Exactly one notify invocation per dispatch, recorded after the agent exits.
- [ ] AC-10.2: The body contains `rc=<n>` matching the agent's exit code **and** the verdict
      token, matching the stated behaviour.
- [ ] AC-10.3: A notify stubbed to exit non-zero leaves `rc` and stdout unchanged.
- [ ] AC-10.4: The `WIRE-PIN` fails when only the `_cmd_notify` call is removed, asserting zero
      notify invocations for a completed dispatch.

**Dependencies on other tasks**: Task 5

---

## Task 11: log-append-contract

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_exec.py`
**Task shape**: `refactor`

**Description**: Change the codex transcript redirect from `> "$log"` to `>> "$log"` so a
caller-supplied `--log` keeps pre-existing content, matching agy. After Task 5's unification
there is exactly one codex invocation, hence one redirect. A shared implementation across the
two backends is infeasible (live process redirect vs captured-file concat), so the base
invariant's alternative — a cross-surface byte-equivalence test — is what pins it. Also update
the `:1898` comment, whose stated rationale already assumes surviving caller content.

**Acceptance Criteria**:
- [ ] AC-11.1: `exec codex --log <f>` where `<f>` already holds `PRIOR` leaves `PRIOR` present
      byte-identically and appends the run's transcript after it.
- [ ] AC-11.2: The identical assertion holds for `exec agy --log <f>` (one parameterised test
      over both backends).
- [ ] AC-11.3: `test_agy_empty_response_recovers_verdict_from_caller_log` passes unchanged.
- [ ] AC-11.4: With no `--log`, the auto-`mktemp` path is unchanged and the temp file is still
      removed on the clean path.
- [ ] AC-11.5: The `:1898` comment states the append contract the code implements.

**Dependencies on other tasks**: Task 5

---

## Task 12: docs-heartbeat-and-log-contract

**Production file**: `h-mad/SKILL.md`
**Test file**: `h-mad/tests/test_hmad_dispatch_exec_stamp.py`
**Task shape**: `refactor`

**Description**: Document `HMAD_EXEC_HEARTBEAT_SEC` in §"Exit-code dispatch for 5d/5e" and the
`--log` append contract in §"A missing report on the `exec` path", so `SKILL.md`, the `:1898`
comment, and the code all state the same contract (AC-5.4 of the spec).

**Acceptance Criteria**:
- [ ] AC-12.1: A doc test asserts `SKILL.md` mentions `HMAD_EXEC_HEARTBEAT_SEC` together with
      its default of 120 and the `0`-disables behaviour.
- [ ] AC-12.2: A doc test asserts `SKILL.md` describes `--log` as appending, with no surviving
      text claiming codex truncates it.
- [ ] AC-12.3: `SKILL.md` frontmatter `name` and `description` are unchanged.

**Dependencies on other tasks**: Task 11

---

## Version History

- v1.0: Initial implementation plan draft.
- v1.1: 5b audit cycle 1 — 2 must-fix, 1 should-fix. Task 4's signature took `selector`,
  `current comment` and preformatted `state text` as arguments, which contradicted Task 6
  (where `_exec_stamp` calls the resolver itself) and pushed both the resolver call and the
  span format out to every call site, breaking the single-owner rule the design sets; the
  emitter now takes only `<kind> <agent> <label> <cd_dir> [rc] [verdict]` and is exercised
  against a stubbed resolver until Task 6 wires it. AC-5.6 asserted "zero stamp calls without
  `--heartbeat`" at a task where the beat call does not yet exist, so it would have passed
  vacuously and certified nothing — it is now a flag-consumption assertion at Task 5, with the
  behavioural version moved to Task 9 as AC-9.9. Added explicit unconditional-fire mutation
  anchors (M-1..M-6) to Tasks 4 and 9, which the design mandated and v1.0 omitted.
- v1.2: 5b audit cycle 2 — 4 must-fix, 2 should-fix, 1 nit. `_exec_run`'s zero-argument
  `--heartbeat` could not have called `_exec_stamp beat <agent> <label> <cd_dir>`; the flag now
  carries that context plus the interval. The interval is passed as a **parameter** rather than
  read inside `_exec_run`, which resolves a direct contradiction with the design's "read only
  by `_cmd_exec`" and keeps recursion-safety a property of the call rather than of
  configuration (new AC-5.8 + mutation M-4b). M-6 mutated the write call but was tied to Task
  3's read-call AC, which it could never fail — retargeted to a new write-scoped AC-4.8.
  AC-3.10 asserted the guard via recorded argv, which is untestable because a shell
  redirection changes descriptors and never appears in argv — restated as a two-limb
  behavioural assertion (inherited-descriptor sentinel + stub-observed fd 0), and given its own
  mutation anchor M-7, plus M-8/M-9 for the jq-null and path-boundary guards. AC-10.2 now
  asserts the verdict as well as `rc`. Task 2's stub relabelled as a test stub.
