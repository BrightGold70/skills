# Plan: audit-cycle-verb

## Executive Summary

Add one `hmad-dispatch audit-cycle` verb that composes the five existing audit scripts into a
single, two-pass, union-gated cycle emitting an `AUDITCYCLE:` verdict, without modifying any of the
scripts it composes.

## Overview

h-mad's audit cycle at Phases 3, 4 and 5b is assembled by hand from five separate calls plus the
token reads and fallbacks between them. The skill-candidate backlog records that shape being retyped
18, 10 and 20+ times in single sessions, and every hand-run is an opportunity to drop the step that
makes the cycle trustworthy. All five parts already exist as tested scripts; what is missing is the
wiring, and the wiring is where the discipline lives.

## Scope

In scope: a new verb in `h-mad/scripts/hmad-dispatch.sh` (reached as `hmad-dispatch audit-cycle`),
its collection and gating logic, its test suite, its mutation spec, and the SKILL.md sections that
document it — including the correction to the report-file transport guidance at §6.6.

User-visible behaviour: one command that runs a cycle and prints one verdict line, per-pass counts,
per-pass delivery channels, and a premise-check checklist. Exit 0 on every verdict; non-zero only
for operational errors.

**CLI signature.** Every context argument the composed scripts require is accepted by the verb and
forwarded; none is inferred:

```
hmad-dispatch audit-cycle --feature <name> --phase plan|design|impl-plan --cycle <N>
                          --project-root <path>
                          [--passes <K>]            # default 2
                          [--ack-file <path>]       # forwarded to every per-pass gate
                          [--report-grace <sec>]    # default 5; post-reap grace wait
                          [--timeout <sec>]         # per-pass exec watchdog
```

`--feature`, `--phase`, `--cycle` and `--project-root` are forwarded to
`h_mad_assemble_audit.py`; `h_mad_extract_report.py` receives `--feature`, `--phase`, `--cycle`
and `--after-marker` only — **it has no `--project-root` flag** (verified against `--help`), so
forwarding one would abort the fallback at the moment it is needed most. `--ack-file` is forwarded to **every**
per-pass `h_mad_audit_gate.py` invocation, so the `## Acknowledged-not-fixed` operator escape hatch
works identically through the verb and through a hand-run cycle — a capability the operator has
today and must not lose by adopting the verb.

## Goals

- Collapse the five-call hand-run cycle into one verb — FR-1, FR-2
- Make the second independent pass the default rather than an act of discipline — FR-3, FR-5
- Make the transport fallback automatic and its use measurable — FR-4
- Make a cycle that measured nothing distinguishable from a cycle that passed — FR-6
- Surface every must-fix citation for premise verification without pretending to adjudicate it — FR-7
- Keep the verdict readable by the same discipline as every other h-mad gate — FR-8
- Reconcile the documented transport preference with the measurement contradicting it — FR-9
- Cover the whole cycle offline, including the case that would break a naive union — FR-10

## Requirements

- FR-1: One verb, one cycle
- FR-2: Assembly is gated, and its size signal is relayed
- FR-3: Two independent passes, isolated per-pass channels
- FR-4: Report collection tries report-file, falls back to `--out`
- FR-5: Union gating by per-pass gate runs, never by concatenation
- FR-6: Cannot-judge is a distinct verdict carrying no counts
- FR-7: Premise-check checklist
- FR-8: Verdict line and signal discipline
- FR-9: Documentation, including the report-file correction
- FR-10: Tests

## Implementation Strategy

**Compose, do not modify.** This feature invokes `h_mad_assemble_audit.py`, `h_mad_report_wait.py`,
`h_mad_extract_report.py`, `h_mad_audit_gate.py` and the existing `exec` verb exactly as they are —
some from the shell verb and some from the Python helper, per the process-boundary table below,
which is the single statement of which process calls which. No script this feature calls is edited.
That keeps the blast radius to one new code path and lets every existing test stay meaningful.

**Follow the house verdict-token pattern.** Every h-mad gate prints `TOKEN: VERDICT fields…`, exits
0 on a verdict, reserves non-zero for operational error, and emits an `[H-MAD]` marker. This verb is
the thirteenth instance of that shape and deviates from it in no respect. The three invariants that
have cost time before are explicit acceptance criteria here: a cannot-judge carries **no** count
fields (AC-6.1), the CLI exits 0 on a verdict (AC-8.2), and the token is pinned bidirectionally
between implementation and SKILL.md by a docs test (AC-9.4).

**Layer placement, and the exact process boundary.** The verb belongs in `hmad-dispatch.sh` rather
than as a standalone Python script because everything it orchestrates is already reached through the
wrapper, and it inherits the wrapper's substrate detection, `--log` plumbing and `progress`
observability for free. The split between shell and Python is drawn as follows, and nothing
straddles it:

| Step | Invoked by | Rationale |
|---|---|---|
| `h_mad_assemble_audit.py` | **shell** (the verb) | Runs once per pass before any dispatch; the verb must read `ASSEMBLE:` to decide whether to dispatch at all |
| `exec agy` dispatch, backgrounding, reaping | **shell** (the verb) | Job control and `--log` plumbing are the wrapper's existing job |
| `h_mad_report_wait.py` | **Python helper** | Its timeout/empty outcome feeds directly into the fallback decision, which is collection logic |
| `h_mad_extract_report.py` | **Python helper** | The fallback half of the same decision |
| `h_mad_audit_gate.py` | **Python helper** | Per-pass invocation and token parsing |
| Premise-check extraction, verdict line assembly | **Python helper** | Text handling |

So the shell owns *assembly and dispatch*; the helper owns *collection, gating and reporting*, and
is called once per cycle with the per-pass paths. Keeping shell to orchestration and Python to text
handling is the split the rest of the skill already uses.

**Every `AUDITCYCLE:` line is emitted by the helper — including the ones the shell decides.** The
shell intercepts two conditions before any dispatch exists (`ASSEMBLE: HALT` → AC-2.2, and a failed
byte-identity assertion), and it would be natural to `echo` the verdict there. It must not: two
emitters means two format definitions, and the token is the machine-readable contract. Instead the
shell invokes the helper in a **no-pass mode** (`--halt-reason <r>`) that emits the `AUDITCYCLE:
UNVERIFIED reason=<r>` line and the `[H-MAD]` marker without collecting or gating anything. The
boundary therefore holds literally: nothing straddles it, and there is exactly one place where a
verdict line is formatted.

**The gate's own verdicts are read as three, not two.** Verified 2026-08-20: a report with no
`## Must-fix`/`## Should-fix` headers — a narration-only report, and an empty file — yields
`GATE: INVALID must=0 should=0` at exit 2. Two things follow. The verb needs no pre-parse to satisfy
AC-5.6, so "compose, do not modify" holds. And `INVALID` **carries counts it did not measure**, so a
helper reading `must=`/`should=` rather than the verdict word would score a header-less report as
clean — the same cannot-judge-reads-as-pass shape this feature's own AC-6.1 forbids. The helper keys
on the verdict word for all three, and its exit-2 does not mean "operational error" here; only an
absent `GATE:` token does.

**Assembly runs once per pass, not once per cycle.** The report-file path is substituted into the
prompt body at assembly time, so per-pass report-file isolation and a single shared prompt file are
mutually exclusive. Executed rather than assumed (2026-08-20) — two prompts assembled for the same
feature/phase/cycle differing only in `--report-file`:

```
$ diff /tmp/audit_audit-cycle-verb_plan_cycle1_p1.txt /tmp/audit_audit-cycle-verb_plan_cycle1_p2.txt
742c742
< /tmp/audit_audit-cycle-verb_plan_cycle1_p1.report.md
---
> /tmp/audit_audit-cycle-verb_plan_cycle1_p2.report.md
```

Both assembled at 47037 B with the same sentinel `AUDIT-audit-cycle-verb-plan-v1`. The verb
therefore calls `h_mad_assemble_audit.py` once per pass, asserts `ASSEMBLE: PASS` on each, and
asserts the prompts differ **only** at the report-path line — which preserves the guarantee that
mattered (one preflight, one size check, one sentinel per cycle) without pretending one file can
carry two report destinations.

A **failed** identity assertion means the inputs changed between two assemblies of the same cycle —
someone edited the plan, spec or invariants mid-cycle — so the two passes would be auditing
different documents and their union would be meaningless. That is a **cannot-judge verdict**, not an
operational error: every script ran correctly and detected a real condition, and the cycle simply
measured nothing. It is the same shape as `assemble_halt`. The shell invokes the helper's no-pass
mode with `reason=prompt_divergence`; the helper prints `AUDITCYCLE: UNVERIFIED
reason=prompt_divergence` with no count fields and exits **0**, and the operator re-runs the cycle
rather than scoring it.

Non-zero is reserved for "a script could not run at all" — an unreadable input, a bad argument —
which is both the base invariant's rule and the reason it exists: a non-zero exit registers as a
`PostToolUseFailure` and leaks into coexisting plugins, so a detected condition must never claim
one.

**There are two assemblies, so there are two `ASSEMBLE:` tokens** — one per pass — and each is
parsed separately, line-scoped, from that pass's own captured stdout: `sed -n 's/^ASSEMBLE: //p'`,
taking the last match. Line-scoping matters for the same reason it does at 6a-prime: a bare capture
breaks the moment a future version adds anything to stdout.

The three outcomes are combined as follows, and no pass dispatches until every pass has assembled:

| Across the passes | Cycle behaviour |
|---|---|
| all `PASS` | dispatch every pass |
| **any** `HALT` | dispatch **nothing** — helper no-pass mode, `reason=assemble_halt:p<i>` naming the first halting pass. Dispatching only the passes that assembled would gate a `--passes 2` cycle on one pass while printing `passes=2` |
| any exit non-zero, or exit 0 with **no** `ASSEMBLE:` token | operational error (AC-2.4/AC-2.5): non-zero exit, no `AUDITCYCLE:` line, nothing dispatched. The absent-token case is called out because it is the one where silence would otherwise read as consent — identical treatment to an absent `GATE:` token |

`size_status=` is likewise per-pass. The helper receives the **worst** value across the passes
(`unverified` if any pass reported it), because the field exists to make an unverified size visible
and a per-pass average would hide exactly the case it is for.

**Deliberately untouched**: the hand-run step list in SKILL.md §"Audit prompt assembly" (retained as
the debugging path), Phase 5b's separate `WIREPIN:` gate, and the revision loop, which stays with
the orchestrator because advancing a cycle is authoring judgment.

## Architecture Considerations

**Per-pass isolation is a correctness constraint, not tidiness — and the reason is not the one
that reads as obvious.** Probed rather than assumed (2026-08-20), two concurrent `exec agy`
dispatches staggered 2s apart onto one shared `--out`:

```
=== rc: a=0 b=0 ===
=== shared --out content ===
ALPHA
=== b.stdout ===
hmad-dispatch: exec: REFUSING to overwrite --out /tmp/probe_out/shared.out — its content
changed while this dispatch ran (another dispatch wrote there; J29). Existing file
preserved; this dispatch's answer is on stdout and in the transcript.
BETA
```

So `exec` is **not** last-writer-wins: the overwrite guard fires, the **first** writer's content
survives, and the second dispatch reports only on stdout and in its transcript. Both exit 0.

This makes a shared path *more* dangerous than a clobber, not less. Pass 2's `--out` holds **pass
1's report** — a well-formed, plausible audit report, not an empty file — so a collector reading
`--out` cannot distinguish it from a correct delivery, and the cycle would gate twice on one pass's
findings while reporting `passes=2`. Distinct `--out`, `--log` and report-file paths per pass are
therefore load-bearing for the union's meaning, not merely for tidiness.

**Union by per-pass gating, not by concatenation.** This is the load-bearing architectural decision.
It was first derived by reading `h_mad_audit_gate.classify` — it accumulates content across repeated
section headers, so a concatenated file superficially behaves like a union, but
`_count_section_findings` returns the bullet count whenever any bullet is present and applies its
prose/numbered/blockquote fail-safe only when there are none. Reading is not evidence, so it was
then **executed** (2026-08-20): a prose-only-finding report and a single-bullet report, gated alone
and concatenated.

```
=== gate prose.md alone ===              GATE: FAIL must=1 should=0
=== gate bullets.md alone ===            GATE: FAIL must=1 should=0
=== gate CONCATENATION ===               GATE: FAIL must=1 should=0
```

The concatenation reports **must=1** where the two findings total 2: the prose finding is silently
dropped. That is an under-count, in the one direction a gate must never fail. Gating each pass on
its own file has no such interaction and totals 2, and the aggregate verdict (PASS iff all passes
PASS) is identical to what a correct union would give.

**The gate's internals are now a dependency, so pin them.** The verb's correctness rests on
`classify`'s behaviour continuing to hold. AC-10.3 pins exactly the case that distinguishes the two
designs, so a future change to the gate breaks a test rather than the verb silently.

**Cannot-judge must be structurally unmistakable.** `must=0 should=0` and "no report arrived" are
the same bytes to a consumer that reads counts. Omitting the count fields from `UNVERIFIED` is what
makes the two unmistakable, and it is why AC-6.1 is stated as an absence rather than a value.

**Concurrency, and the reap/collect ordering.** The two passes are dispatched in the background and
reaped, matching the skill's own guidance to background an `exec` and read its result rather than
poll on a timer. The ordering between reaping and collection is load-bearing, because `report_wait`
polls a *path* and knows nothing about a *process* — either order, done naively, can hang for the
full timeout:

- **Collect before reaping** → if a dispatch crashes or exits early without writing the report,
  `report_wait` keeps polling a file that will never arrive, for its whole timeout.
- **Reap, then collect with the full timeout** → if the agent delivered via `--out` instead of the
  report slot, the process is already dead and `report_wait` again burns its whole timeout on a file
  that cannot appear.

So the verb does neither. **Reap first, then decide from the file, with a short grace period rather
than the full wait:**

1. `wait` each backgrounded dispatch and record its rc.
2. For each pass, test the report path directly. Non-empty → `delivered=report-file`, no wait at
   all. This is the normal case and costs nothing.
3. Empty or absent → `report_wait` with a **grace** timeout (`--report-grace`, default 5s), not the
   600s figure. Once the process has exited, the only file that can still land is one already being
   flushed; a longer wait cannot change the outcome.
4. Still nothing → `h_mad_extract_report.py` on that pass's `--out` (`delivered=out`), then
   `delivered=none` if that is empty too.

`--report-timeout` is **not offered at all** — the reap-first flow is the only collection path, so
the flag would reach no logic, and a CLI control that silently does nothing invites tuning a
timeout that cannot apply. The collection bound is the dispatch's own `--timeout` plus the grace.

**Every collection channel is cleared before dispatch, and every removal is verified by re-reading.**
Both scored channels carry the same hazard, and guarding only one leaves the hole open on the other:

- `<report-path>` and `<report-path>.done` — the primary channel.
- `<out-path>` — the **fallback** channel, and the one easier to forget. Every path here is
  deterministic in feature/phase/cycle/pass, so re-running a cycle reuses it. If the re-run's
  dispatch dies before writing anything, `exec`'s overwrite guard never fires (the file is unchanged
  since the dispatch started, which is exactly the case it permits overwriting), the stale file
  survives, and `h_mad_extract_report.py` extracts the **previous run's** report — a well-formed,
  correctly-sentinelled report for the same feature/phase/cycle, indistinguishable from this run's.

A removal is a state mutation, and an `rm` that silently removed nothing leaves a previous cycle's
report to be scored as this one's — the same class of failure as an unlanded mutation anchor
reporting a guard as enforced. The verb therefore asserts the post-state of every one of them
(`[ ! -e "$path" ]`) and treats a surviving file as an operational error, not a verdict.

`--log` is deliberately **not** cleared: it appends by design on both backends, it is never scored,
and its history across re-runs is useful for exactly the crash diagnosis this guard is about.

**This feature's deliverable is almost entirely connections, so connection enforcement governs its
tests.** The verb writes very little logic of its own; what it ships is five call sites —
`h_mad_assemble_audit.py`, `exec agy`, `h_mad_report_wait.py`, `h_mad_extract_report.py` and
`h_mad_audit_gate.py`. A test that exercises any of those scripts directly is not evidence the verb
reaches it, and presence of a call site in the diff reads as correct whether or not it fires. Each
of the five therefore ships a test that **fails when that connection alone is removed and the callee
is left intact**, mutated in both directions where a direction exists:

**Every mutation below is applied to the CALLER, leaving the callee intact** — that is what the
invariant requires, and it is the half that is easy to get wrong. Mutating the callee's *output* (a
stubbed `ASSEMBLE: PASS`, a forced `GATE: PASS`) tests the caller's branch but leaves the callee
modified, so it is not a connection mutation and is not evidence the connection is enforced.

| Connection | Remove the connection (callee intact) → must fail | Force the caller past its own guard → must fail |
|---|---|---|
| verb → `h_mad_assemble_audit.py` | drop the assemble invocation, dispatch the prompt file as found → the "dispatch refused on `ASSEMBLE: HALT`" test fails | delete the caller's token check so it dispatches whatever assemble said → the AC-2.2 `UNVERIFIED` test fails |
| verb → `exec agy` (per pass) | drop the second pass's dispatch, keep its paths allocated → the "`passes=2` yields two distinct dispatches" test fails | remove the caller's `--passes` guard so it always dispatches 2 → the `--passes 1` single-dispatch test fails |
| helper → `h_mad_report_wait.py` | drop the wait call and go straight to the fallback → the **delayed-delivery** test fails (see below) | remove the caller's file-present check so it always waits → the "file already present ⇒ `report_wait` is never invoked" test fails |
| helper → `h_mad_extract_report.py` | drop the fallback call on an empty slot → the `delivered=out` test fails | remove the caller's slot check so it always extracts → the `delivered=report-file` test fails |
| helper → `h_mad_audit_gate.py` | drop the per-pass gate call for pass 2 → the "FAIL in either pass fails the cycle" test fails | remove the `delivered=` guard so a `delivered=none` pass is gated anyway → the `no_report:p<i>` `UNVERIFIED` test fails, because the pass reports counts instead of a cannot-judge |
| **verb → `h_mad_audit_cycle.py`** (the shell→helper process boundary) | drop the helper invocation after reaping → the "a completed cycle emits an `AUDITCYCLE:` line" test fails | remove the shell's `ASSEMBLE:`-token guard so the helper is invoked in full collect-and-gate mode even on a halt → the `assemble_halt` `UNVERIFIED` test fails |

**The `report_wait` connection needs a delayed-delivery test, and the obvious test cannot catch
it.** Under the reap-first flow the wait is *bypassed* whenever the report file is already present —
which is how a successful delivery is normally mocked, by creating the file before the helper looks.
On that fixture, deleting the `report_wait` call changes nothing and the mutation survives while
reporting the connection as enforced. The fixture must therefore deliver the report **after** the
wait begins (file created ~1s into the grace window), which is the only shape in which the call site
is on the executed path at all. This is the fixture-hides-the-mutation failure in miniature: the
test was not wrong about the outcome, it was wrong about which code it ran.

The last row is the one it is easiest to leave out, because the helper is *this feature's own* code
rather than a pre-existing script — but it is the load-bearing boundary: it carries every verdict
line, in both the normal and the no-pass path. A whole-module test passes while the shell silently
fails to invoke it, and the cycle then has no verdict formatter at all.

These are connection mutations, distinct from the gating-logic mutation spec: the latter proves the
gate's own guards bite, the former proves the verb actually reaches the gate. A whole-module revert
establishes neither, because it removes both sides at once. Each mutation must be verified to have
**landed** before its run is trusted — an anchor matching nothing leaves the suite green and reports
the connection as enforced.

**The shell's own guards need discrimination coverage too, and they are the easiest to forget** —
they were each added in response to an audit finding, which makes them feel already-justified. A
guard that has never been observed failing is not known to bite. Both go in the gating mutation spec
with their own tests:

| Shell guard | Mutate to its permissive value | A test must then fail |
|---|---|---|
| `[ ! -e "$path" ]` after clearing each channel | delete the assertion, keeping the `rm` | the "stale report survives ⇒ operational error, nothing scored" test, whose fixture makes the path unremovable (read-only parent dir) |
| per-pass prompt byte-identity assertion | delete the assertion, keeping the two assemblies | the "prompts diverge ⇒ `UNVERIFIED reason=prompt_divergence`" test, whose fixture edits the plan between the two assemblies |

Both fixtures have to *create the condition* rather than assert on a happy path — a permissive
mutation is invisible against inputs that never trip the guard, which is the same reachability trap
as the `report_wait` fixture above.

## Deliverables

| Deliverable | Path | Type | Satisfies |
|---|---|---|---|
| `audit-cycle` verb | `h-mad/scripts/hmad-dispatch.sh` (edit) | CLI verb | FR-1, FR-2, FR-3, FR-8 |
| Collection + gating helper | `h-mad/scripts/h_mad_audit_cycle.py` (new) | module | FR-4, FR-5, FR-6, FR-7 |
| Per-pass audit report files | `docs/01-plan/features/<feature>.<phase>.audit.v<N>.p<i>.md` (and `docs/02-design/features/…` for design) | artifact | FR-4 |
| `AUDITCYCLE:` verdict line + `[H-MAD]` marker | `h-mad/scripts/h_mad_audit_cycle.py` | CLI contract | FR-8 |
| SKILL.md §"Audit prompt assembly" revision | `h-mad/SKILL.md` (edit) | docs | FR-9 |
| SKILL.md §6.6 report-file correction | `h-mad/SKILL.md` (edit) | docs | FR-9 |
| Verb registry entry for `AUDITCYCLE:` | `h-mad/SKILL.md` §"Helper scripts" (edit) | docs | FR-9 |
| Helper test suite — collection, gating, verdict, premise list | `h-mad/tests/test_h_mad_audit_cycle.py` (new) | tests | FR-4, FR-5, FR-6, FR-7 |
| Verb-level shell test — **stubbed `exec agy` dispatch**, assembly gating, no-pass halt mode | `h-mad/tests/test_hmad_dispatch_audit_cycle.py` (new) | tests | FR-1, FR-2, FR-3 |
| Bidirectional docs test for the token | `h-mad/tests/test_h_mad_audit_cycle_docs.py` (new) | tests | FR-9 |
| Mutation spec for the gating logic | `h-mad/tests/specs/audit_cycle_gating.mutation.json` (new) | tests | FR-10 |
| Connection mutation spec — one entry per composed call site | `h-mad/tests/specs/audit_cycle_connections.mutation.json` (new) | tests | FR-10 |
| `--ack-file` / `--passes` / context-argument forwarding | `h-mad/scripts/hmad-dispatch.sh` + `h_mad_audit_cycle.py` | CLI contract | FR-3, FR-5 |

Exact paths are stated here rather than deferred to the impl-plan because two of them are *edits to
existing files* — `hmad-dispatch.sh` and `SKILL.md` — and naming them now is what makes the
feature-branch prerequisite (§"Convention Prerequisites") concrete rather than advisory.

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Two concurrent passes share an output path | **Not a clobber** — probed: the overwrite guard fires and the first writer survives, so pass 2's `--out` holds pass 1's *report*. The cycle gates twice on one pass's findings while printing `passes=2` | Pass-indexed `--out`/`--log`/report-file (AC-3.2, AC-3.3). The refusal is a backstop that makes the failure quiet, not a substitute for isolation |
| A naive union implementation under-counts a prose finding | A real must-fix ships as a PASS | AC-5.1 forbids concatenation; AC-10.3 pins the distinguishing case as a test |
| A pass delivering nothing is scored as zero findings | A cycle that measured nothing reads as clean | `UNVERIFIED` with no count fields (AC-6.1); `delivered=none` routes there (AC-4.6) |
| Aggregate counts double-count a finding both passes reported | `must=` is a poor cross-cycle progress signal | Safe direction — can never turn FAIL into PASS; per-pass counts printed alongside (AC-5.3) and the inflation stated (AC-5.4) |
| The premise checklist is emitted and never read | The rec-13 discipline stays theoretical | It is part of the verdict output, not a side file (AC-7.5) |
| SKILL.md keeps prescribing the hand-run steps after the verb exists | The verb is built and nobody uses it | FR-9 is part of this feature, not a follow-up |
| Editing the live skill while another run is in flight | A run reads a half-finished `hmad-dispatch.sh` | Build on a feature branch; the skills symlink makes the working tree the live skill |
| The skills symlink couples two repos' suites | A sibling repo's tests fail on a change here | Run both coupled suites before merge |
| An echoed prompt's own sentinel pair is scored as the report | A false verdict from the template's own text | `--after-marker` mandatory on every fallback extraction (AC-4.3) |

## Convention Prerequisites

- Feature branch off `main` before any edit to `h-mad/scripts/hmad-dispatch.sh` — the skills symlink
  means the working tree is the live skill.
- `agy` on PATH. `exec` is pane-independent, so the repo's current `PREFLIGHT: FAIL
  unresolved=codex,agy` does not block dispatch or live-fire.
- Phase 5 implementation dispatched to Codex via `exec codex`, per the transport decision recorded
  at Phase 1.
- Stdlib-only Python and POSIX shell. No new external dependency.
- Both coupled suites green before merge.

## Success Criteria

- **Every** AC in the spec passes an automated test — the count is derived, never restated here:
  `grep -c '^\s*- AC-' docs/01-plan/features/audit-cycle-verb.spec.md`. A literal count in this
  document went stale twice during the plan-audit cycles (49→50→52), each time becoming a
  self-contradiction a reviewer had to spend a must-fix on; a derived count cannot.
- `AUDITCYCLE:` verdict emitted with exit 0 on PASS, FAIL and UNVERIFIED alike; non-zero reserved
  for operational error
- Every mutation in the gating mutation spec is caught
- Every connection mutation is caught — each of the five composed call sites has a test that fails
  when that connection alone is removed with its callee intact
- `--ack-file` reaches every per-pass gate, asserted by a test in which the sidecar clears a finding
  the gate would otherwise count
- Every pre-dispatch file removal is asserted to have landed by re-reading the path, and a surviving
  file is an operational error rather than a verdict
- No collection path can hang for a full `report_wait` timeout after its dispatch has been reaped
- One live cycle run end-to-end against real `agy`, producing a real verdict on a real audit
- SKILL.md §6.6 records the 8-of-8 report-file measurement
- The five candidate rows this closes (recurrences 18, 13, 10, 10, 9) are stamped with this feature
  as their landing location

## Out-of-Scope (confirmed from spec)

- Looping until `GATE: PASS` — advancing a cycle requires revising the audited document, which is
  authoring judgment; the orchestrator keeps the loop
- Automated premise adjudication — the verb does not open cited files; hard-failing an unresolvable
  citation is deferred until the checklist's output shape has settled in use
- Phase 5b's `WIREPIN:` gate — a separate check on the same document, still called separately
- Union deduplication — aggregate counts may double-count; safe in the gating direction and visible
  via per-pass counts
- Replacing the hand-run step list in SKILL.md — retained as the debugging path for when the verb
  itself is suspect
- Any change to `h_mad_assemble_audit.py`, `h_mad_audit_gate.py`, `h_mad_extract_report.py`, or
  `h_mad_report_wait.py` — the verb composes them as they are

## Next Steps

Operator approves plan v1.0, then the Phase 3 audit cycle runs: assemble the audit prompt, dispatch
agy, gate on must-fix and should-fix, revise and re-audit until both are zero.

## Version History

- v1.0: Initial plan draft.
- v1.1: Cycle-1 audit revisions. Both passes' must-fixes applied (they overlapped on nothing):
  connection mutation coverage for the five composed call sites; the `exec` shared-`--out`
  assumption **probed and corrected** — it is first-writer-wins with an explicit refusal, not
  last-writer-wins, which makes a shared path yield a plausible wrong report rather than an empty
  one; `--ack-file` forwarding and the full CLI signature stated; the shell/Python process boundary
  drawn as a table. Also records that assembly runs once per **pass**, not once per cycle, because
  the report-file path is substituted into the prompt body.
- v1.2: Cycle-2 audit revisions, again zero overlap between the two passes. The connection-mutation
  table was mutating the **callee**, which the invariant explicitly forbids — every row now mutates
  the caller and leaves the callee intact. The "compose, do not modify" paragraph still said the
  verb shells out to all four scripts, contradicting the process-boundary table added in v1.1 (the
  fix-in-one-place-stale-in-the-duplicate class); it now defers to the table as the single
  statement. Exact file paths added for every new and edited deliverable. The exit-code/token
  contradiction it also found is fixed in the spec at v1.2.
- v1.3: Cycle-3 audit revisions (4 must-fix per pass, one overlapping). Specifies the reap/collect
  ordering — reap first, test the report path directly, then a 5s **grace** wait rather than the
  600s timeout, because once a dispatch has exited no longer wait can change the outcome; either
  naive order could hang for the full timeout. Pre-dispatch file removals are now asserted by
  re-reading the path, since an `rm` that removed nothing leaves a previous cycle's report to be
  scored as this one's. Two assumptions previously argued from source are now **executed and
  cited**: the assemble-per-pass `diff`, and the concatenation under-count, which measured
  `must=1` against a true total of 2 — confirming the decision rather than overturning it. AC total
  corrected 49 → 50.
- v1.4: Cycle-4 revisions. Both passes independently flagged that the v1.3 reap-first design
  contradicted spec AC-4.1's 600s wait; the spec is reconciled at its v1.3 rather than the plan
  reverted, since the narrowing is the correct behaviour. `--report-grace` added to the CLI
  signature, which had described the flag in prose without listing it in the contract.
- v1.5: Cycle-5 revisions (3 must-fix + 2 should-fix, disjoint across passes). Resolves two
  boundary contradictions the cycle-4 fixes introduced: the stubbed-dispatch test was assigned to
  the helper suite though the helper never dispatches, and "verdict line assembly is the helper's,
  nothing straddles it" was contradicted by the shell emitting `UNVERIFIED` on `ASSEMBLE: HALT` —
  now routed through a helper no-pass mode so there is exactly one verdict formatter. Probing the
  gate for AC-5.6 found it **already** returns `GATE: INVALID` for a header-less report, and that
  the token **carries `must=0 should=0` it never measured** — so the helper must key on the verdict
  word, and this spec's own AC-5.5 ("non-zero gate exit is an operational error") would have
  misrouted it. Also defines the identity-assertion error path and how `size_status=` is relayed.
- v1.6: Cycle-6 revision — **both passes returned the same single finding**, the first full
  agreement in six cycles. v1.5 called prompt divergence "an operational error, not a verdict" and
  then had it exit 0 emitting `UNVERIFIED`, which AC-8.2 makes mutually exclusive. Resolved toward
  the cannot-judge verdict: every script ran and detected a real condition, so nothing failed to
  execute, and non-zero stays reserved for "could not run" — which also keeps a verdict from
  registering as a `PostToolUseFailure` in coexisting plugins. `prompt_divergence` added to the
  spec's AC-6.3 reason list.
- v1.7: Cycle-7 revisions — two disjoint must-fixes, both substantive rather than drift. Adds the
  **sixth** connection, verb → `h_mad_audit_cycle.py`: the shell→helper boundary was omitted from
  the mutation table because the helper is this feature's own code, yet it carries every verdict
  line in both the normal and no-pass paths. And clears `<out-path>` before dispatch alongside the
  report paths — the fallback channel had the same stale-data hazard the primary channel was already
  guarded against, and `exec`'s overwrite guard does not fire for a dispatch that dies before
  writing, so a re-run would extract the previous run's correctly-sentinelled report.
- v1.8: Cycle-8 revisions. **Pass 2 gated clean while pass 1 found three real defects** — the
  single-pass gate would have shipped all three. All three were one class in the connection-mutation
  table: the "force it to fire" column held mutations that were actually removals (the gate row gave
  the same removal twice) or unrelated changes (the shell→helper row swapped the formatter rather
  than forcing the call). Every force cell now genuinely forces its call site past a guard. Also
  records that the `report_wait` connection is **unreachable under the normal fixture** — reap-first
  bypasses the wait when the file is already present, which is how a success is mocked — so it needs
  a delayed-delivery fixture or its mutation survives while reporting the connection enforced.
- v1.9: Cycle-9 revisions — **roles reversed from cycle 8**: p1 gated clean and p2 found both
  defects, so neither pass is the reliable one. Both were unpropagated consequences of the v1.1
  assemble-per-pass change: the parsing description still spoke of a single `ASSEMBLE:` token, and
  the absent-token case was specified for `GATE:` but not for `ASSEMBLE:`. Adds the three-outcome
  combination table (all PASS / any HALT / operational error), fixes assembly to complete for every
  pass before any dispatch, and defines `size_status=` aggregation as worst-across-passes.
- v1.10: Cycle-10 revision — the two shell guards added by earlier cycles (`[ ! -e "$path" ]` and
  the prompt byte-identity assertion) had no discrimination coverage. A guard added in response to a
  finding feels already-justified, which is exactly why it escapes the mutation spec; both now carry
  a permissive mutation and a condition-creating fixture.
- v1.11: Two corrections from the design audit. A finding said the design dropped `--project-root`
  from the `h_mad_extract_report.py` call — its facts were right (the docs disagreed) and its
  direction was backwards: **that script has no such flag**, so the plan was wrong and forwarding it
  would abort the fallback exactly when it is needed. Also drops `--report-timeout`, which the
  design gives no logic to reach.
