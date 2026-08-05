# Plan: exec-path-hardening

## Executive Summary

Add mandatory-but-best-effort observability inside `_cmd_exec` — start/heartbeat/exit
worktree checkpoints plus a desktop notification — under a hard non-interference invariant,
and resolve the codex/agy `--log` truncation asymmetry into one stated contract.

## Overview

`exec` became the documented default for one-shot 5d/5e and every audit dispatch because its
exit code is a hard completion signal. The cost was never priced: it is the only transport
with no pane, no task row, and no durable trace, so a 900-second Phase-5 dispatch is
indistinguishable from a dead one to an operator away from the desk. Every mechanism needed
already exists in the wrapper (`_cmd_worktree_comment`, `_cmd_notify`, the `kill -0` poll in
`_run_with_timeout`); none is wired to `exec`.

## Scope

`scripts/hmad-dispatch.sh` — `_cmd_exec` and its timeout/liveness path only. User-visible
behaviour: an Orca worktree card that reports a running `exec` dispatch and its outcome, a
desktop notification at exit, and one `HMAD_EXEC_HEARTBEAT_SEC` knob. No change to `exec`'s
stdout, `rc`, prompt delivery, or verdict semantics. No change to any other verb.

**Flags: one intentional carve-out.** No flag is added, removed, or renamed, and no flag's
parsing changes — but `--log`'s *behaviour on the codex backend* deliberately changes from
truncate to append, which is FR-5's whole point (see §Implementation Strategy). A caller that
points `--log` at a file with existing content keeps that content instead of losing it. Every
other flag (`--cd`, `--model`, `--out`, `--timeout`, `--sandbox`, `--effort`) is untouched.

## Goals

- Make a headless dispatch's liveness and outcome readable from the Orca card alone — FR-1, FR-2
- Signal completion at the desk without claiming it is a mobile channel — FR-3
- Guarantee observability can never alter the verdict channel or the exit code — FR-4
- Retire the `--log` code/comment contradiction on the recovery path — FR-5
- Stamp the worktree the work lands in, not the coordinator's — FR-6

## Requirements

- FR-1: durable start/exit checkpoints on the worktree card
- FR-2: liveness heartbeat while the subprocess runs
- FR-3: desktop notification at exit, explicitly not mobile
- FR-4: observability cannot corrupt the verdict channel or the exit code
- FR-5: one stated `--log` truncation contract across both backends
- FR-6: comment target resolution follows `--cd`

## Implementation Strategy

**One seam, not four.** All surfaces are stamped from inside `_cmd_exec` rather than at call
sites. This skill's recorded failure mode is a correct signal nothing was obliged to consume:
`PREFLIGHT:` had to be re-engineered because detection existed and no step read it, and
`size_status=` was moved onto the verdict line for the same reason. A `SKILL.md` instruction
would reproduce that defect one signal over.

**Route every dispatch through the background-and-poll shape.** Today `exec` runs the agent
in the foreground when `--timeout` is absent and only backgrounds it under
`_run_with_timeout`. A heartbeat riding the existing `kill -0` poll therefore has nowhere to
attach on the no-timeout path. Unifying on one shape — background, poll, reap, with the
deadline check skipped when no timeout was given — makes the heartbeat unconditional and
removes a second code path rather than adding one.

**Spec AC-2.4 requires this to be pinned by a test, not merely implemented.** The AC states
that silence on the no-timeout case is itself a failure, so the plan mandates the guard
explicitly: a dispatch invoked **without** `--timeout`, spanning N≥3 heartbeat intervals,
must emit heartbeat stamps at the same cadence as the `--timeout` case. Both paths are
asserted in the same test set so the unification cannot silently regress to
timeout-path-only — which is the shape the defect would take, since the `--timeout` tests
would stay green while headless dispatches with no deadline went dark again. This is the load-bearing decision and the
main risk surface, because that path already carries hard-won behaviour: stdin handed to the
child with `<&0`, the fresh process group from `set -m`, group-signalled TERM→grace→KILL, and
an absolute deadline off `SECONDS`. None of it may regress.

**One `worktree ps` call serves both needs.** Per A2/A3 the same payload carries
`worktreeId` (the `<repoId>::<path>` selector FR-6 needs) and the current `comment` the
composer needs, so resolution and composition share one runtime call rather than two.

**The `--log` contract is decided: codex appends, matching agy.** FR-5 requires one stated
contract, so this plan states it rather than deferring. codex's `> "$log"` becomes `>> "$log"`.
Three reasons, in order: (a) the `:1898` comment justifies appending the boundary on both
backends *by reasoning from surviving caller content* — append is what makes the code match
its own stated rationale, and truncation would mean correcting the comment to admit the
recovery channel is destroyed on the backend that needs it most; (b) agy already appends and
its caller-log recovery is a shipped, tested behaviour (AC-5.3), so append unifies the
backends instead of documenting a split; (c) boundary recovery slices after the **last**
occurrence, so accumulated prior-dispatch content in the log cannot produce a stale verdict —
the mechanism that makes append safe is already in place and already tested. The cost is an
ever-growing file when a caller reuses one `--log` path across cycles, which is the caller's
choice and is visible to them.

**Append becomes a rule applied by two surfaces, so it needs a cross-surface equivalence
test.** The base invariant requires one authoritative implementation *or* a test asserting
byte-equivalence across surfaces. One implementation is not available here: codex appends by
redirecting a **live process stream** (`>> "$log"` on the agent invocation) while agy appends
a **captured response file** (`cat "$resp_file" >> "$log"`). These cannot collapse into a
shared helper without re-plumbing how each backend produces output — a change well outside
this feature and into the shipped recovery path. The equivalence test is therefore the
mandated route: a single parameterised assertion that, for **both** backends, pre-existing
`--log` content is preserved verbatim and the run's own transcript is appended after it. That
test is what stops the two independent implementations from silently diverging, and it fails
if either backend regresses to truncation.

**Compose the comment; never blind-overwrite — and the rule is asymmetric.**
`worktree-comment` only ever overwrites, and the `handoff` skill stamps the same single field
with `handoff: <slug> · <status> · next: …`. `handoff`'s documented rule treats
`handoff:` / `handover:` / `taken over:` / `h-mad` as skill stamps that may be replaced
outright, and anything else as human-written and preserved by appending.

**Adopting that rule symmetrically would reproduce the exact clobber it is supposed to
prevent**: a heartbeat firing every 120 s would replace the `handoff:` checkpoint observed in
A4, which is a resume artifact the operator depends on and cannot reconstruct. So `exec`
adopts a strictly narrower rule:

**The rule is positional-independent, not prefix-based.** A `startswith`-style rule is broken
for precisely the case it exists to serve: with a human comment `Fixing issue`, heartbeat 1
appends to give `Fixing issue · h-mad: 2m`; heartbeat 2 sees a string that does *not* start
with `h-mad`, takes the preserve branch, and appends again — unbounded growth, once per
interval, on the field we promised to protect. So the operation is **replace-our-segment
wherever it appears, else append**:

| Existing comment | Heartbeat / checkpoint behaviour |
|---|---|
| empty | write the h-mad stamp |
| contains an `h-mad` segment **anywhere** | replace that segment in place, preserving everything around it — this is what makes the stamp *rolling* |
| `handoff:` / `handover:` / `taken over:` / human text, no `h-mad` segment | **preserve**; append our stamp after it, once |

Only our own segment is ever replaced, and it is located by content rather than position.
Everything else is preserved. This is narrower than `handoff`'s rule on purpose and does not
change `handoff`'s behaviour — `handoff` WRITE remains free to replace an `h-mad` stamp,
because it is an operator-initiated low-frequency action, whereas the heartbeat is automatic
and high-frequency. Frequency is the asymmetry that justifies the different rule.

The stamp therefore needs a delimited, greppable form (a fixed `h-mad:` lead-in and a segment
terminator) so it can be located and replaced mid-string without disturbing neighbours.

**Idempotency is an acceptance property, not a comment.** N heartbeats against any starting
comment must leave exactly one `h-mad` segment and a comment length that does not grow with N.
The test must run **at least three** intervals: the two-interval case passes under the broken
prefix rule above for a comment that starts empty, so it cannot discriminate.

**A failed read aborts the stamp — it never degrades to a write.** The read exists solely to
avoid clobbering. Treating an unreadable comment as empty and writing anyway would reintroduce
the exact A4 data loss the read was added to prevent, and would do it precisely when the
runtime is already misbehaving. Skipping a stamp costs one missing heartbeat; guessing costs
the operator's checkpoint. This applies to start, heartbeat, and exit stamps alike.

**Target selection and clobber avoidance are the same decision, because they are the same
read.** Per A3 one `worktree ps` payload yields both `worktreeId` and `comment`, so the
fallback ladder is driven by what that payload contains — not by two independently-chosen
policies. Resolving to a target whose comment we have *not* read is never safe:

| `worktree ps` outcome | Target | Write? |
|---|---|---|
| entry matching `--cd` found (even in a `truncated` listing) | that entry's `worktreeId` | yes — selector and comment both known |
| no match for `--cd`, but the `active` entry is present with its comment | `active` | yes — AC-6.3's fallback, and we hold `active`'s comment |
| listing unreadable / times out / no usable entry at all | none | **no** — abandon the stamp, zero `worktree set` calls |

The dispatch never fails in any row; only the stamp is skipped. This resolves the v1.3–v1.4
contradiction between the deliverables table ("`active` fallback on no-match/`truncated`") and
the abort rule: `truncated` is not itself disqualifying — a truncated listing that still
contains a usable entry is fine, and what disqualifies is having no entry whose comment we
read. Spec AC-6.3 is amended to match (spec v1.2).

**Best-effort means structurally incapable of interfering,** not merely "we call it in a way
that usually works": every surface call is bounded, its output redirected off stdout, its
exit code discarded, and its failure invisible to `rc`.

**Deliberately untouched:** prompt assembly and the boundary append, `--out` handling,
verdict recovery, `tree delta`, sandbox/model/effort flags, and every other verb.

## Verified assumptions (live probe evidence)

Every load-bearing assumption below was executed against the real runtime and its output is
cited here, per the Axis B assumption-verification invariant. Nothing in this plan rests on
an inferred interface.

**A1 — `_cmd_worktree_comment` already carries `_require_orca`,** so the cmux no-op is
inherited rather than re-implemented. Observed:

```
$ grep -n "_require_orca" scripts/hmad-dispatch.sh
scripts/hmad-dispatch.sh:1300:  _require_orca worktree-comment || return $?
```

**A2 — `worktree ps` exposes a path→selector mapping.** Each entry carries `worktreeId` in
the exact `<repoId>::<path>` selector form, so the reverse mapping FR-6 needs is a direct
field read, not an inference. Observed (one entry, trimmed):

```
WORKTREE[0] KEYS: [workspaceKind, worktreeId, repoId, hostId, ..., comment, ..., agents]
  worktreeId = "73485f82-3088-4bfc-a750-83e20becedb0::/Users/kimhawk/orca/HemaSuite"
  path       = "/Users/kimhawk/orca/HemaSuite"
```

**A3 — the current comment ships in that same payload.** `worktree ps` returns a `comment`
field per entry, so read-then-compose (below) costs no extra runtime call: the resolver
already fetches what the composer needs.

**A4 — the clobber hazard is observed, not hypothetical.** At probe time a live worktree
held an actual `handoff` checkpoint in that field:

```
  comment = "handoff: section-persistence-integrity · phases 1-4 clean, 5b unresolved (8 cycles), no code y…"
```

A blind heartbeat overwrite destroys exactly this. That is why composition is a requirement
and not a nicety.

**A5 — entry order is NOT stable between calls.** Two `worktree ps` calls seconds apart
returned the skills worktree at index 0 and then HemaSuite at index 0. Any resolver must
match on `path`, never on position. The top level also carries `truncated`, which is the
real condition behind AC-6.3's fallback.

**A6 — the test harness already records `orca` invocations; this is not new plumbing.**
`tests/stubs/orca` line 2 appends every invocation's argv to `$HMAD_STUB_CAPTURE`, already
answers `worktree set`, and already lets a test drive `worktree ps` output via
`HMAD_STUB_ORCA_WT_PS_STDOUT`. Observed:

```
$ grep -n "worktree\|CAPTURE" tests/stubs/orca
2:printf 'orca %s\n' "$*" >> "${HMAD_STUB_CAPTURE:-/dev/null}"
17:if [ "${1:-}" = "worktree" ] && [ "${2:-}" = "set" ]; then
29:if [ "${1:-}" = "worktree" ] && [ "${2:-}" = "ps" ] && [ -n "${HMAD_STUB_ORCA_WT_PS_STDOUT:-}" ]; then
```

What is missing is that the **exec** tests stub `codex`/`agy` but not `orca`, so
invocation-count assertions (AC-1.1, AC-1.3, AC-2.1, AC-2.3, AC-3.1, AC-6.1) need only wiring,
not new machinery.

**But capture alone is not sufficient, and assuming it was would have shipped a blind test.**
`HMAD_STUB_ORCA_WT_PS_STDOUT` is a *static* fixture: every `worktree ps` in a run returns the
same bytes. A multi-interval heartbeat test driven that way reads the original comment on
every tick, appends once each time against an unchanging base, and reports a stable result —
so it would pass even under the broken prefix rule, hiding the unbounded-growth defect that
rule causes. The stub must therefore round-trip state: `worktree set --comment` persists the
value and `worktree ps` serves the persisted value back, so the read-modify-write loop is
genuinely exercised. The static fixture is kept for read-*shape* and read-*failure* cases,
where no round trip is wanted.

## Architecture Considerations

- **Shared mutable field.** The worktree comment is one string shared by `h-mad`, `handoff`
  WRITE, TAKEOVER, and humans. Adding a high-frequency writer to a field with an existing
  low-frequency writer and a preservation convention is the principal integration risk —
  and A4 shows the field occupied by a real checkpoint right now.
- **Coupled suites.** `~/.claude/skills/h-mad` is a symlink into this repo and `handoff`
  ships from it too. Touching comment semantics can fail the handoff suite; both run before
  merge.
- **Orca-only by inheritance.** `_cmd_worktree_comment` already carries `_require_orca`, so
  the cmux no-op is inherited, not re-implemented — but `_require_orca` returning non-zero
  must not surface as a dispatch failure.
- **No new dependency.** Everything is existing wrapper functions plus bash builtins.
- **`--cd` → selector is a reverse mapping.** `_worktree_path` maps selector→path; FR-6 needs
  path→selector off `worktree ps`, and must degrade to `active` on any ambiguity.

## Deliverables

| Deliverable | Target file(s) | Satisfies |
|---|---|---|
| Unified background-and-poll execution path in `_cmd_exec` | `h-mad/scripts/hmad-dispatch.sh` (`_cmd_exec`, `_run_with_timeout`) | FR-2 |
| Checkpoint emitter (start / heartbeat / exit) with asymmetric composition | `h-mad/scripts/hmad-dispatch.sh` (new helper beside `_cmd_worktree_comment`) | FR-1, FR-2 |
| `--cd` → worktree-selector resolver (matches `path`, returns `worktreeId` + that entry's `comment`; falls back to `active` only when `active`'s comment came back in the same payload; otherwise abandons the stamp) | `h-mad/scripts/hmad-dispatch.sh` (new helper beside `_worktree_path`) | FR-6 |
| Exit notification call | `h-mad/scripts/hmad-dispatch.sh` (`_cmd_exec` → `_cmd_notify`) | FR-3 |
| `HMAD_EXEC_HEARTBEAT_SEC` env knob (default 120, `0` disables) | `h-mad/scripts/hmad-dispatch.sh`; documented in `h-mad/SKILL.md` §"Exit-code dispatch for 5d/5e" | FR-2 |
| codex `--log` append contract in code | `h-mad/scripts/hmad-dispatch.sh` (`_cmd_exec` codex branch, both timeout and no-timeout redirects) | FR-5 |
| codex `--log` append contract in prose (the `:1898` comment + recovery section) | `h-mad/scripts/hmad-dispatch.sh`, `h-mad/SKILL.md` §"A missing report on the `exec` path" | FR-5 |
| Non-interference + checkpoint/heartbeat/notify/resolver test set | `h-mad/tests/test_hmad_dispatch_exec.py` | FR-1–FR-4, FR-6 |
| Mutation spec for every new guard | `h-mad/tests/` (JSON spec consumed by `h_mad_mutation_harness.py`) | FR-4 |
| Orca-CLI invocation capture in the exec tests (**partly exists — see A6**) | `h-mad/tests/test_hmad_dispatch_exec.py` — add `"orca"` to the `_bindir` list (today the exec tests stub only `codex`/`agy`) and set `HMAD_STUB_CAPTURE` | FR-1, FR-2, FR-6 |
| **Stateful** comment round-trip in the orca stub, **per-test isolated** | `h-mad/tests/stubs/orca` — `worktree set --comment` persists to a path given by a per-invocation env var (e.g. `HMAD_STUB_ORCA_STATE`) that the harness points at the test's own `tmp_path`; `worktree ps` serves it back. **No default, no shared or hardcoded temp path** — unset means stateless, exactly as today. Static `HMAD_STUB_ORCA_WT_PS_STDOUT` retained for read-shape/failure fixtures | FR-1, FR-2 |
| Cross-surface `--log` append equivalence test (codex and agy) | `h-mad/tests/test_hmad_dispatch_exec.py` | FR-5 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Unifying on background-and-poll regresses stdin delivery, the pgroup kill, or the absolute deadline | Silent dispatch failure; the `<&0` bug already shipped once | Treat the existing timeout tests as regression guards; RED any change against them before refactoring; keep `_run_with_timeout`'s contract intact rather than inlining it |
| Heartbeat clobbers a `handoff` checkpoint on the shared comment field | Operator loses resume context — a data-loss bug, not cosmetic | Read-then-compose with segment-located replacement; pin with a test that a foreign comment survives N≥3 heartbeats on a stateful stub |
| A failed read degrades to a blind write | Same data loss, arriving exactly when the runtime is already unhealthy | Read failure / `truncated` / no-match abandons the stamp; asserted as zero `worktree set` calls |
| A static test fixture makes the composition test blind to unbounded growth | A shipped defect with a green suite — the "test discrimination" failure class | Stateful comment round-trip in the stub; the idempotency test runs N≥3 intervals because N=2 cannot discriminate |
| A surface call writes to stdout and corrupts the verdict | Wrong gate input — the exact J23 failure class | Redirect every surface call; AC-4.1/4.2 assert byte-identical stdout with surfaces on and off |
| A surface call hangs and stalls the dispatch | Phase 5 wedges with no diagnostic | Bound every surface call; abandon on expiry |
| A guard ships whose message is load-bearing and a returncode-only test passes it | False confidence — happened twice (J22, J23) | Mutation-verify with content assertions, not exit codes |
| Heartbeat interval interacts badly with a 0.25 s poll | Comment spam, orca call storm | Interval is a wall-clock floor checked inside the poll, not a per-tick action; assert stamp count over a multi-interval run |
| Scope drifts into shipped exec work | Wasted cycles re-auditing settled defects | Spec's Out-of-Scope list is binding; an audit finding against it is a scope violation |

## Performance reconciliation — the spec's NFR is breached, deliberately

The spec's NFR states start + exit cost "≤ 2 bounded `orca` calls". Read-then-compose cannot
meet that, and the plan claims the breach rather than hiding it.

Actual cost per stamp is **1 `worktree ps` (resolve selector + read current comment, per A3 a
single call) + 1 `worktree set` (write)** = 2 calls. Start + exit is therefore **4 calls**, and
each heartbeat adds 2 more.

The read is not removable by caching. The comment is a shared mutable field (A4) and a
`handoff` WRITE from another session can land between our read and our next write, so a cached
comment would reintroduce the clobber that A4 exists to prevent — trading a correctness
property for one runtime call. The NFR as written is incompatible with the A4 constraint, and
A4 wins: destroying an operator's resume checkpoint is a data-loss defect, while 2 extra
bounded calls per stamp are unmeasurable against a 600–900 s dispatch.

**This requires a spec amendment**, carried back to `exec-path-hardening.spec.md` §Non-Functional
Requirements: the bound becomes 2 bounded `orca` calls *per stamp*, with start + exit = 4 and
each heartbeat interval adding 2. The default 120 s interval against a 900 s dispatch bounds a
worst case at roughly 18 calls per dispatch, all bounded and all off the critical path.

## Connection enforcement (this feature is wiring-shaped)

Every deliverable here is a **connection**, not new behaviour: `_cmd_worktree_comment`,
`_cmd_notify` and the poll loop all already exist and already work. What ships is the fact
that `_cmd_exec` *calls* them. A whole-module revert removes callee and call site together,
so its RED split returns identically whether or not the wire exists — it is structurally
incapable of establishing the one decision this feature makes.

Therefore each call site below is mandated as a `wiring`-shaped task carrying an explicit
`WIRE` / `WIRE-PIN`, and Phase 5 must run the **wire-scoped revert** for each: revert the
call site only, leaving the callee and the tests intact, and confirm the named `WIRE-PIN`
test fails. Module suite still green after a wire-scoped revert → the connection is
unenforced and the task halts.

| Wire | Call site | `WIRE-PIN` must assert |
|---|---|---|
| W1 | `_cmd_exec` → start checkpoint | With the start call removed, a test fails on the *absence of the pre-run comment invocation* — not on the comment function being missing |
| W2 | `_cmd_exec` poll → heartbeat checkpoint | With the heartbeat call removed, a run spanning N≥3 intervals produces **zero** heartbeat stamps — total comment writes fall to the 2 start/exit stamps, not "one fewer" |
| W3 | `_cmd_exec` → exit checkpoint | With the exit call removed, no comment carrying **all three** AC-1.2 elements — the agent token (`codex`/`agy`), the literal `rc=<n>`, and the extracted verdict — is emitted. A stamp carrying any subset still fails |
| W4 | `_cmd_exec` → `_cmd_notify` | With the notify call removed, zero notify invocations are recorded for a completed dispatch |
| W5 | checkpoint emitter → `--cd` selector resolver | With the resolver call removed, the comment targets `active` even when `--cd` is inside a listed worktree |

Each `WIRE-PIN` test's RED must be an assertion about the **caller's** observable behaviour
— the call was not made, the value did not propagate. A RED that is an `ImportError` /
`AttributeError` / `NameError` proves only that the callee is absent and goes green the
moment it exists, wired or not; that is a wrong-reason RED and halts.

Mutation in the other direction is also required: force each connection to fire
unconditionally and confirm the corresponding negative test fails — e.g. heartbeat firing
with `HMAD_EXEC_HEARTBEAT_SEC=0`, or a comment being stamped under substrate `cmux`.

## Convention Prerequisites

- Branch `feature/NNN-exec-path-hardening` off `main` at 5c.
- Codex authors Phase 5 under the TDD gate; RED before GREEN per module.
- Every guard mutation-verified via `h_mad_mutation_harness.py`; `SURVIVED`/`REFUSED` halts.
- Every call site in the table above declared `wiring` shape with `WIRE`/`WIRE-PIN` filled,
  so the 5b wire-pin gate can see it; an unpinned wiring task halts at 5b.
- Both coupled suites (h-mad + handoff) green before merge.
- GREEN established by the revert test with `git add -N` before `git stash push`, and
  restoration verified by executing the symbol — **plus** the wire-scoped revert above for
  each of W1–W5.

## Success Criteria

- All 24 ACs across FR-1–FR-6 pass automated tests.
- All 45 existing `test_hmad_dispatch_exec.py` tests pass unchanged.
- Both coupled suites green.
- Every new guard mutation-verified `ALL_CAUGHT`.
- Each of W1–W5 fails its `WIRE-PIN` test under a wire-scoped revert (call site removed,
  callee intact), with a caller-behaviour RED reason — never a missing-symbol error.
- A pre-existing foreign comment on the target worktree survives a full dispatch including
  at least three heartbeats, against a **stateful** stub that round-trips the comment.
- After N≥3 heartbeats from any starting comment, exactly one `h-mad` segment is present and
  the comment length does not grow with N.
- A `worktree ps` read yielding no entry whose comment was read produces **zero**
  `worktree set` calls, and the pre-existing comment is byte-identical afterwards — while a
  `truncated` listing that still contains the target entry stamps normally.
- A dispatch invoked **without** `--timeout` emits heartbeats at the same cadence as one with
  it (spec AC-2.4; silence on this case is a failure).
- Both backends preserve pre-existing `--log` content verbatim, asserted by one
  cross-surface equivalence test that fails if either regresses to truncation.
- The stub's comment state file is per-test and never shared; with its env var unset the stub
  behaves exactly as it does today.
- A live `exec` dispatch under Orca leaves a readable card trail: running → outcome.

## Out-of-Scope (confirmed from spec)

- Re-opening shipped exec defects: rc-3 empty-message, the `===HMAD-DISPATCH-BOUNDARY===`
  slice and its per-backend fail-closed behaviour, `--cd`-scoped `tree delta`,
  `_run_with_timeout`'s pgroup kill, the agy report-file/F-10 mitigation.
- Orca task/dispatch provenance for exec-run work (structurally impossible).
- Replacing `exec` with orchestration, or an orchestration fallback.
- Backfilling `docs/skill-monitoring.md` with J19–J23.
- Push-to-mobile notification (no such channel exists in `hmad-dispatch`).

## Next Steps

Operator approves v1.0 → Phase 3 audit cycle via agy (`exec agy`, report-file transport) →
gate until must-fix = 0 and should-fix = 0 → Phase 4 design.

## Version History

- v1.0: Initial plan draft.
- v1.1: Audit cycle 1 must-fix. Added §"Verified assumptions (live probe evidence)" (A1–A5)
  citing executed output for the `_require_orca` and `worktree ps` claims — the probe also
  produced three findings the plan did not have: `worktreeId` is already the `<repoId>::<path>`
  selector, `comment` ships in the same payload (so resolve+compose share one call), and entry
  order is unstable between calls, so the resolver must match on `path` rather than index. Added
  §"Connection enforcement" declaring W1–W5 as `wiring`-shaped call sites with mandated
  wire-scoped reverts, caller-behaviour RED reasons, and unconditional-fire mutations.
- v1.2: Audit cycle 2 must-fix + nit. FR-5's contract is now **decided in the plan** (codex
  appends, matching agy) instead of deferred. The composition rule was symmetric with
  `handoff`'s and so would have replaced the very `handoff:` checkpoint A4 observed — replaced
  with an explicit asymmetric table where only our own `h-mad` stamp is ever replaced,
  justified by write frequency, plus an idempotency requirement so repeated heartbeats replace
  in place rather than growing the string. Added §"Performance reconciliation" claiming the
  spec's NFR breach explicitly (2 calls per stamp, read not cacheable because the field is
  shared and mutable) and back-propagated the amendment into the spec. W3's `WIRE-PIN` now
  asserts the verdict token as well as `rc`.
- v1.3: Audit cycle 3 must-fix + should-fix + nit. Scope's "no flag changes" claim now carves
  out the intentional codex `--log` truncate→append behaviour change it contradicted. W3's
  `WIRE-PIN` asserts all three AC-1.2 elements (agent token, `rc`, verdict), not two.
  Deliverables table now names exact target files instead of generic types. Probing the stub
  inventory to write those paths produced A6: `tests/stubs/orca` already records every argv to
  `$HMAD_STUB_CAPTURE`, already answers `worktree set`, and already accepts injected
  `worktree ps` output — so the "build an invocation-counting stub" deliverable shrinks to
  wiring the existing stub into `test_hmad_dispatch_exec.py`.
- v1.4: Audit cycle 4 must-fix + nit — all three findings landed on content v1.2/v1.3 had
  just introduced. (1) The composition rule was prefix-based (`starts with h-mad`), which
  breaks on the preserve case it exists for: appending to a human comment yields a string that
  no longer starts with our stamp, so every later heartbeat appends again — unbounded growth
  on the protected field. Replaced with segment-located replacement, a delimited stamp form,
  and idempotency stated as an acceptance property over N≥3 intervals (N=2 cannot
  discriminate). (2) The static `HMAD_STUB_ORCA_WT_PS_STDOUT` fixture would have hidden that
  defect by returning the same base comment every tick, so a stateful comment round-trip in
  `tests/stubs/orca` is now a deliverable. (3) Read failure now explicitly abandons the stamp
  rather than degrading to a blind write. W2's `WIRE-PIN` corrected from "one fewer" to zero
  heartbeat stamps.
- v1.5: Audit cycle 5 must-fix + should-fix. (1) Spec AC-2.4 demands the no-timeout heartbeat
  case be *pinned by a test*, and v1.4 implemented the behaviour while staying silent on the
  guard — now mandated explicitly, with both paths asserted together so unification cannot
  regress to timeout-path-only. (2) v1.4 contradicted itself on `truncated`: the deliverables
  promised an `active` fallback while the abort rule discarded the stamp. Resolved by
  recognising that target selection and clobber avoidance are the *same read* (A3), so the
  fallback ladder is driven by what the payload contains — a truncated listing holding the
  target entry stamps normally, and only "no entry whose comment we read" abandons. Spec
  AC-6.3 amended to match (spec v1.2), since its unconditional `active` fallback predated the
  no-clobber requirement and would have overwritten an unread comment on the wrong worktree.
  (3) `--log` append is now applied by two surfaces; a single implementation is infeasible
  (live process redirect vs captured-file concat), so a cross-surface byte-equivalence test is
  mandated instead. (4) The stub's comment state is scoped per-test via an env var with no
  default, per the J18 state-clobber lesson.
