# Analysis: gate-blindness-hardening

## Executive Summary

All 23 spec acceptance criteria are met and verified by execution rather than by reading the
diff; the coupled suite is green at 1166 with no regressions, and the feature's own Phase 7 now
correctly blocks until its architectural review is recorded.

## Match Rate: 100%

23 of 23 ACs met. **The spec defines 23 ACs, not the 25 the plan's Success Criteria claims** —
see §"Findings" below; that is a plan defect, not an implementation gap.

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: unrecorded review blocks | 5 | 5 | ✅ Complete | `h_mad_phase7_preconditions.py` terminal `else`, `check()` |
| FR-2: a skip blocks | 3 | 3 | ✅ Complete | `h_mad_phase7_preconditions.py` `SKIPPED_NO_PANE` → `blockers` |
| FR-3: explicit operator override | 4 | 4 | ✅ Complete | `h_mad_state_schema.json` enum + `archreview_overridden` branch |
| FR-4: headless 6a-prime + auto-record | 4 | 4 | ✅ Complete | `SKILL.md` §6a-prime |
| FR-5: hostile stub corpus | 5 | 5 | ✅ Complete | `h-mad/tests/stubs/orca` `_hostile_comment` |
| FR-6: template mandate | 2 | 2 | ✅ Complete | `references/codex-implementer-prompt.md` |

## AC-by-AC verification

Every row below was **executed** during this analysis, not inferred from the diff. The gate ACs
were driven through `p7.check()` directly; the doc ACs by reading the shipped section; the stub
ACs by invoking the stub as a subprocess.

| AC | Result | How it was checked |
|---|---|---|
| AC-1.1 absent → `archreview_not_run` | ✅ | `check({last_completed_phase:6})` → not ready, code present |
| AC-1.2 `None` → blocked | ✅ | driven through `check()` directly, not via the writer (the enum excludes `null`) |
| AC-1.3 detail names field + remedy | ✅ | detail contains `archreview`, `6a-prime`, and `record` |
| AC-1.4 `READY_TO_MERGE` still ready | ✅ | ready, zero blockers |
| AC-1.5 exit discipline | ✅ | verdict → exit 0; unreadable state file → exit 2 |
| AC-2.1 `SKIPPED_NO_PANE` blocks | ✅ | not ready, code `archreview_skipped` |
| AC-2.2 detail names the headless remedy | ✅ | contains `exec agy` and `satisfies the gate` |
| AC-2.3 no other `SKIPPED_*` accepted | ✅ | `SKIPPED_FOO` blocks, no archreview warning emitted |
| AC-3.1 override → ready + warning | ✅ | ready, warning `archreview_overridden` |
| AC-3.2 enum accepts it, rejects a misspelling | ✅ | enum contains it; `--set archreview=SKIPPED_OVERRIDE` exits 2 |
| AC-3.3 warning requires carrying into the report | ✅ | contains `Phase 7 report` and `not READY_TO_MERGE` |
| AC-3.4 override is the ONLY missing→ready path | ✅ | swept all 8 values; ready set is exactly {`READY_TO_MERGE`, `SKIPPED_OPERATOR_OVERRIDE`} |
| AC-4.1 `exec agy` satisfies the gate | ✅ | §6a-prime states it and that no resolved pane is required |
| AC-4.2 no longer prescribes `SKIPPED_NO_PANE` | ✅ | string absent from the whole bullet |
| AC-4.3 instructs recording the ASSESSMENT | ✅ | exact instruction present |
| AC-4.4 reviewer-less route names the override | ✅ | `SKIPPED_OPERATOR_OVERRIDE` present |
| AC-5.1 knob unset ⇒ no regression | ✅ | 1166 passed, 0 failed (branch point was 1143) |
| AC-5.2 four corpora accepted | ✅ | each invoked, rc 0, parseable envelope |
| AC-5.3 `markdown` has literal `[` and `*` | ✅ | asserted on the emitted comment directly |
| AC-5.4 `markers` round-trips as data | ✅ | `jq -e` parses the envelope |
| AC-5.5 unrecognised name fails loudly | ✅ | rc 2, **empty stdout**, stderr names all four corpora |
| AC-6.1 template mandates hostile payloads | ✅ | mandate sentence present, names `HMAD_STUB_HOSTILE` |
| AC-6.2 template states the rationale | ✅ | rationale sentence present and distinct from the mandate |

## Findings

These are not unmet ACs. Each is classified per the Phase-6 rules.

1. **The plan's Success Criteria says "All 25 spec ACs"; the spec defines 23.** Classification:
   `design-vs-spec` (a document disagreement, not an implementation defect). No AC is missing —
   the count is simply wrong in the plan. Recommend correcting the plan; escalated rather than
   silently "fixed", since the operator may prefer to know the number was never reconciled.

2. **Three defects were found in this feature's own shipped work by dogfooding it**, all fixed in
   `733a5f8` and re-reviewed:
   - `h_mad_extract_verdict.py` prints its `[H-MAD]` marker to **stdout**, so §6a-prime's
     auto-record instruction led into a two-line `$(...)` capture that the writer refused. Caught
     live by the read-back guard the same task had introduced.
   - The §6a-prime doc tests sliced a magic 1600-character window. The bullet was already 1707
     characters with only 76 of margin on the nearest guard; the fix took it to 2006, which under
     the old slicing would have pushed three unrelated guards out of scope.
   - A ban on the substring `h_mad_state_validate.py` passed only because the sentence warning
     against it fell outside that window.

3. **Two defects were found in the generated RED tests before GREEN**, neither visible from
   running them (both showed the expected failure counts): an assertion that lowercased its
   haystack then searched for an upper-case literal, and a pair of mutually unsatisfiable
   assertions (one banning `resolved pane`, its sibling requiring `does not require a resolved
   pane`). Both would have made GREEN unreachable.

4. **Known limitation, deliberate and recorded**: the hostile stub path emits a reduced envelope
   carrying only `comment`, where the unset path also carries `branch` and `path`. No current test
   needs both; a future test selecting a corpus AND reading `.branch` would see null.

## Regression posture

- Branch point 1143 → **1166 passed, 0 failed** across both coupled suites (`h-mad/tests/` and
  `handoff/`, coupled through the `~/.claude/skills/h-mad` symlink).
- Every task revert-tested: reverting production with tests untouched reproduces that task's RED
  split **exactly**, and restoration was verified by executing the symbol rather than grepping.
- Every task mutation-verified `ALL_CAUGHT` with `refused=0`: 6 + 7 + 5 + 6 + 5 + 3 + 4 = 36
  mutations, zero survivors. One run correctly REFUSED an ambiguous anchor (`command -v agy`
  matches twice in `SKILL.md`); the anchor was made unique rather than the refusal ignored,
  because a refused mutation measures nothing.
- Backward compatibility executed, not asserted: `closed=9 absent=0` across already-closed
  records, so FR-1's blocker newly fires on none of them; no live record carries
  `SKIPPED_NO_PANE`; `archreview` remains absent from the schema's `required` array.

## Readiness

Ready for Phase 7. The feature's own Phase 7 gate correctly blocked on `archreview_not_run` until
6a-prime ran and recorded `READY_TO_MERGE` — the dogfood the plan named as its acceptance
evidence. 6a-prime was run twice: once over `88a31ff..765634d`, then again over
`88a31ff..733a5f8` after the fix changed the reviewed surface, so the recorded assessment
describes the code that will actually merge rather than a superseded diff.
