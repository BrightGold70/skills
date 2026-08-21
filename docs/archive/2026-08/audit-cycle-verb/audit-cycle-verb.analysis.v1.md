# Analysis: audit-cycle-verb

## Executive Summary

All 57 acceptance criteria across 10 functional requirements are met by the shipped code; the
scoped suite is 1577/0 and `WIREREG: PASS verified=6/6`. The two open items on this feature are a
**test-depth** gap (real concurrency is exercised only on its happy path) and a **document** gap
(J39: `plan.md` restates several ACs more narrowly than `spec.md`) — neither is an unmet AC, and
both are recorded below rather than folded into the rate.

## Match Rate: 100%

`(FRs where all ACs are met) / (total FRs) x 100` = 10/10 = **100%**. AC-level: **57/57**.

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: One verb, one cycle | 4 | 4 | ✅ Complete | `hmad-dispatch.sh:2584` (`--phase` rejected before clearing, AC-1.4); `test_verb_phase_rejected_before_clearing` |
| FR-2: Assembly gated, size signal relayed | 5 | 5 | ✅ Complete | `size_status` threaded 7x through `hmad-dispatch.sh`; `test_verb_assemble_halt_no_dispatch` |
| FR-3: Two independent passes | 6 | 6 | ✅ Complete | `local passes="2"` (AC-3.1, fixed as J38 this cycle); `test_verb_two_distinct_dispatches`, `test_verb_invalid_passes` |
| FR-4: Report collection + fallback | 8 | 8 | ✅ Complete | `.done` required in the fast path `h_mad_audit_cycle.py:63` (AC-4.1); `reports:` line `:387` (AC-4.4); omitted on UNVERIFIED, pinned at `test_h_mad_audit_cycle.py:755` (AC-4.4b) |
| FR-5: Union gating, never concatenation | 7 | 7 | ✅ Complete | per-pass `gate()` invocation; double-count note emitted `:389` (AC-5.4); `GATE: INVALID` routing `:314` (AC-5.6) |
| FR-6: Cannot-judge carries no counts | 5 | 5 | ✅ Complete | all four `reason=` values present — `assemble_halt`, `prompt_divergence`, `no_report`, `no_gate_sections` (AC-6.3) |
| FR-7: Premise-check checklist | 5 | 5 | ✅ Complete | `(no citation)` marker `:339` (AC-7.3) |
| FR-8: Verdict line + signal discipline | 4 | 4 | ✅ Complete | `[H-MAD]` marker `:363`/`:391`; `auditcycle_lines()` pins single-line output (AC-8.4) |
| FR-9: Documentation | 5 | 5 | ✅ Complete | SKILL.md §6.6 carries the **measured** 17-of-18 figure (AC-9.2, corrected as J36); `test_docs_token_pinned` is bidirectional (AC-9.4) |
| FR-10: Tests | 8 | 8 | ✅ Complete | 18 mutations across two specs, 8 of them shell-level (AC-10.5b); mutation re-run below |

## Method, and why the obvious shortcut was not used

The impl-plan's AC checkboxes are **not** a usable coverage map: only 31 of 57 ACs carry one and
only 10 name a test. Every test they do name exists in the collected suite (0 missing of 1348
collected), so the map is accurate where present and simply incomplete. Coverage was therefore
measured against the code, not against AC labels — a bare AC-label scan has previously reported 14
uncovered ACs on another feature, all of them false.

## Gaps

### Gap 1: CLOSED — the carried "real concurrency is untested" claim was overstated

This feature carried a standing gap: *"real concurrency untested by every lane"*, naming four
shapes. Probed directly this cycle, and the claim does not survive checking.

**First, the suite does fork.** `_bindir()` symlinks a real `agy` stub onto an isolated PATH, so the
verb's dispatch loop forks real subprocesses and `wait` reaps real pids. The `fcntl` lock in the
stub governs its *recording*, not the forking — the two were conflated when the gap was filed.

**Two of the four shapes have direct tests**, both green:

| shape | covered by |
|---|---|
| empty `pids` array at `--passes 1` | `test_verb_passes_one` |
| `set -e` / non-zero rc from a backgrounded pass | `test_verb_nonzero_exec_rc_is_forwarded_but_not_fatal` — forces `HMAD_STUB_AGY_RC=17` and asserts the rc is forwarded verbatim in the `--pass` payload while the cycle still returns PASS (AC-3.5) |

**The other two are not defects**, established by a throwaway probe driving the exact
dispatch/reap construct (`( … ) & pids[i]=$!` then `if wait "${pids[i]}"`) under `set -euo pipefail`:

```text
passes=1, array never empty      -> rc=[0]        no unbound-array error
child already dead before reap   -> rc=[0 0]      bash retains status until waited
non-zero exit in the subshell    -> rc=[7 7]      propagates; parent survives
child killed by a signal         -> rc=[143 143]  128+15 captured correctly
two passes on the shared stderr  -> 6/6 lines     none lost
```

A pass dying before its reap is indistinguishable at the verb from an ordinary non-zero exit, which
is already tested; and the shared fd carries only stderr diagnostics, which are never scored. The
probe was deleted after reading, per §"Confirming a suspected defect before fixing it".

- **Classification**: not a gap. No AC is unmet and none was ever at risk.
- **Lesson**: the claim had been carried across sessions as established fact and re-stated in three
  handoffs without once being probed. A carried repro is not evidence.

### Gap 2: J39 — `plan.md` is narrower than `spec.md` — `design-vs-spec`, escalated not fixed

Plan re-audit cycles 13 and 14 reported the plan omitting the `reports:` line (AC-4.4/4.4b), the
active rejection of `--passes N<1` (AC-3.1), the printed double-count warning (AC-5.4) and the
`(no citation)` marker (AC-7.3). **Each of these is present in the code** — verified at the line
references in the FR table above. So the shortfall is in the document, not the implementation, and
per §Phase 6 step 4.5 it is a reconciliation decision for the operator rather than an
implementation defect. It does not reduce the match rate, because the implementation genuinely
does satisfy what the spec asks.

## Test Results

```
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q
1577 passed in 229.74s (0:03:49)

h_mad_wire_registry.py verify --base 41efe98 --rootdir <repo> --testpath h-mad/tests
WIREREG: PASS registered=6 verified=6 broken=0 missing=0 ambiguous=0

h_mad_mutation_harness.py audit_cycle_gating.mutation.json
MUTATION: ALL_CAUGHT mutations=6 caught=6 survived=0 refused=0
h_mad_mutation_harness.py audit_cycle_connections.mutation.json
MUTATION: ALL_CAUGHT mutations=12 caught=12 survived=0 refused=0
```

Both mutation specs were re-run **after** this cycle's two code changes (the AC-3.1 `--passes`
default, and the `gate()` exit-code guard), because the prior `ALL_CAUGHT` predated both and was
therefore stale evidence for AC-10.5. `refused=0` is the load-bearing half of that token: the
harness refuses any anchor it cannot match exactly once, so a spec whose anchors had drifted would
report `REFUSED` rather than quietly mutating nothing and reporting the guards as enforced.

## Verdict

Match rate: **100%** (threshold: 90%). Tests: 1577/1577 passing.
→ **Advance to Phase 7.** Gap 1 is test depth beyond any AC; Gap 2 is a document reconciliation
owned by the operator. Neither is an unmet acceptance criterion, so 6b has nothing mechanical to
close — and running it over Gap 2 would encode one reading of a two-document disagreement.

## Version History
- v1.0: Initial gap analysis. Measured against code rather than AC labels; both open items
  classified as non-AC (test depth, and document reconciliation) with the code evidence cited.
