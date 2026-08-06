# Report: gate-blindness-hardening

**Status:** SHIPPED · **Match rate:** 100% (23/23 ACs) · **Suite:** 1143 → 1166 passed, 0 failed
**Branch:** `feature/214-gate-blindness-hardening` · **6a-prime:** `READY_TO_MERGE` (run twice)

## Executive Summary

Closed the Phase-7 hole that let an unrecorded architectural review pass silently, made the
headless review the ordinary way to satisfy 6a-prime so blocking a skip is safe, and gave the
shared stubs an opt-in hostile-payload corpus. All 23 ACs met and verified by execution; the
feature's own Phase 7 blocked on its new gate until 6a-prime ran and recorded, which was the
acceptance evidence the plan asked for.

## What shipped

The Phase-7 gate's `archreview` ladder is now **total**: every value, including absence, produces
an explicit verdict. 6a-prime is satisfiable by any session with the `agy` CLI and records its own
result. The shared stub can emit hostile payloads on request, and the implementer template
mandates using them.

| Value | Before | After |
|---|---|---|
| `READY_TO_MERGE` | ready | ready |
| `WITH_FIXES`, `NO` | blocker `archreview_failed` | unchanged |
| `SKIPPED_NO_PANE` | **warning** — closed the feature | **blocker** `archreview_skipped`, detail names the headless remedy |
| `SKIPPED_OPERATOR_OVERRIDE` | did not exist | ready + warning `archreview_overridden` |
| absent, `null`, unknown | **silently ready** | **blocker** `archreview_not_run` |

## The measurement that matters

The same record, with `archreview` removed, run against both gates:

```
$ python3 <old gate @88a31ff> /tmp/noreview.json --feature gate-blindness-hardening
PHASE7: READY blockers=0            <-- the hole

$ python3 h-mad/scripts/h_mad_phase7_preconditions.py /tmp/noreview.json --feature …
PHASE7: BLOCKED blockers=1
  BLOCKER archreview_not_run: no architectural review recorded …
```

## Landing order — corrected mid-flight

Plan and design both mandated `FR-4 → FR-3 → FR-2 → FR-1`. The 5b audit caught that this is wrong
in one detail: FR-4 makes `SKILL.md` instruct writing `archreview=SKIPPED_OPERATOR_OVERRIDE`, but
FR-3 is what adds that value to the enum, so landing FR-4 first documents a value the writer
**refuses** — verified by running the writer, not by argument. Corrected to
**FR-3 → FR-4 → FR-2 → FR-1** and back-propagated into plan v1.2 and design v1.2. The property
those documents actually protect, *both means before both blockers*, is preserved: FR-3 arms no
blocker.

## Verification

- **Revert test per task.** Reverting production with tests untouched reproduced each task's RED
  split **exactly**; restoration verified by executing the symbol, never by grepping the source.
- **Mutation-verified per task**: 6 + 7 + 5 + 6 + 5 + 3 + 4 = **36 mutations, 0 survivors,
  0 refused** on the final runs. One run correctly REFUSED an ambiguous anchor (`command -v agy`
  matches twice in `SKILL.md`); the anchor was made unique rather than the refusal ignored,
  because a refused mutation measures nothing.
- **Backward compatibility executed, not asserted**: `closed=9 absent=0`, so FR-1's blocker newly
  fires on no already-closed record; no live record carries `SKIPPED_NO_PANE`; `archreview`
  remains absent from the schema's `required` array.
- **Exit discipline preserved** on the stricter path: verdicts exit 0, only an unreadable state
  file exits 2.

## Defects found in this feature's own work

Five, all caught before merge, none by the suite alone.

**Two in the generated RED tests, invisible from running them** — both showed the expected failure
counts, so the RED looked correct:
1. An assertion lowercased its haystack then searched for an upper-case literal — it could never
   match, even with the target sentence present verbatim.
2. Two assertions were **mutually unsatisfiable**: one banned the substring `resolved pane`, its
   sibling required `does not require a resolved pane`, which contains it. GREEN was unreachable.

**Three in shipped work, found by dogfooding the feature on itself** (fixed in `733a5f8`):
3. `h_mad_extract_verdict.py` prints its `[H-MAD]` marker to **stdout**, so §6a-prime's own
   auto-record instruction led into a two-line `$(...)` capture that the writer refused. **The
   read-back guard introduced by the same task caught it on its first live use** — and
   `--strict-only` returns `STATE: PASS` on a record with `archreview` dropped, so the validator-
   based check the 5b audit originally proposed would have passed this silently.
4. The §6a-prime doc tests sliced a magic 1600-character window. The bullet was already 1707
   characters with **76 characters of margin** on the nearest guard; the fix took it to 2006,
   which under the old slicing would have pushed three unrelated guards out of scope.
5. A ban on the substring `h_mad_state_validate.py` passed **only because** the sentence warning
   against it fell outside that window. A blanket ban forbids the warning as well as the mistake;
   replaced with a positive assertion of the warning.

## Audit cycles

`plan: 2 · design: 2 · impl_plan: 6 · iterate: 0`. The six 5b cycles resolved 9 must-fix, 1
should-fix and 1 nit. Two of those must-fix items were defects introduced while fixing earlier
ones — a vacuous verification (`--strict-only` on a non-required field) and a stub guard that
reproduced this feature's own motivating defect by calling its helper from inline command
substitution, where the `exit 2` dies in the subshell and the stub returns 0.

## Carry / follow-ups

1. **The plan's Success Criteria says "All 25 spec ACs"; the spec defines 23.** Document
   disagreement, not an implementation gap. Left for an operator decision rather than silently
   corrected.
2. **The hostile stub path emits a reduced envelope** carrying only `comment`, where the unset
   path also carries `branch` and `path`. Deliberate and adequate today; a future test selecting a
   corpus AND reading `.branch` would see null.
3. **Hostile payloads are opt-in, not default** — explicitly out of scope per the spec, since
   flipping the default would force unrelated triage across the suite. The strongest form of this
   guarantee remains unbuilt.
4. **No live e2e is mandated before Phase-7 closure.** Out of scope per the spec and unchanged;
   note that a live run is what found the defect that motivated this feature.

## Commits

```
88a31ff docs  Phase 5a-5b impl-plan, 6 audit cycles, order correction
e687f25 feat  Task 1 (FR-3) recorded operator override
1be959d feat  Task 2 (FR-4) headless 6a-prime, auto-recorded
ac2285d feat  Task 3 (FR-2) a recorded skip now blocks
519dc6d feat  Task 4 (FR-1) an unrecorded review blocks
721728c feat  Task 5 (FR-5) opt-in hostile stub corpus
765634d feat  Task 6 (FR-6) implementer template mandates hostile fixtures
733a5f8 fix   §6a-prime capture form + boundary-scoped doc slices
```

6a-prime was run twice — over `88a31ff..765634d`, then again over `88a31ff..733a5f8` after the fix
changed the reviewed surface — so the recorded assessment describes the code that merges rather
than a superseded diff.

## Version History

- v1.0: Phase 7 closure report. Match rate 100% (23/23), suite 1143 → 1166, 6a-prime
  `READY_TO_MERGE` recorded and read-back verified, Phase-7 gate `READY blockers=0` with the
  no-review control demonstrated blocking against the new gate and passing against the old.
