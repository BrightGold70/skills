# Phase 7 Report — doc-block-exec

**Feature:** `doc-block-exec`
**Branch:** `feature/doc-block-exec`
**Baseline (5c):** `0885152` · **Closure:** `4ecc4c4`
**Started:** 2026-09-02 · **Closed:** 2026-09-07
**Gate:** `PHASE7: READY blockers=0`

## Executive Summary

`doc-block-exec` shipped and closed: five tasks, a full 5e gate set on each of the last two, and a
real consumer migrated off its own hand-rolled extraction and execution onto the new helper. At
closure the full h-mad suite is `2792 passed / 0 failed`, the Phase-6a gap analysis reads
**100.00% (49/49)**, and Phase 6a-prime returned `READY_TO_MERGE` with no Critical and no Important
findings. `PHASE7: READY blockers=0`.

Two substantive defects were found and fixed *during closure* rather than after it — a duplicated
key-validity policy the architectural review caught, and the plan not recording that decision once
the code had made it. Four tooling defects in the H-MAD apparatus itself were surfaced by this
feature's own gates and are filed rather than fixed here (#152–#155). One residual is carried
forward (#142).

The section on what the 5e gates established is the load-bearing part of this report: every green
below was checked against a mutation or a revert, because a passing suite cannot certify itself.

## What shipped

`h-mad/scripts/h_mad_doc_block_exec.py` — a helper that locates and executes exactly one
explicitly tagged ` ```bash hmad:exec ` block from one UTF-8 document and heading. It carries a
fence-aware Markdown scanner, heading-scoped selection, an info-string grammar, literal
substitution, a bounded strict-shell execution path with stream artifacts, and a CLI whose every
outcome is a `DOCBLOCK: <VERDICT>` line at exit 0 — exit 2 reserved for environmental failure.

Task 5 then **migrated a real consumer onto it**. `h-mad/tests/test_h_mad_collect_report_docs.py`
previously hand-rolled its own extraction (a `re.findall` over the Second-surface section) and its
own execution (an inline `subprocess.run` with no timeout). It now calls `dbe.extract`/`dbe.select`
and `dbe.substitute`/`dbe.run_block`, and the gate fence in `h-mad/SKILL.md` was retagged so
exactly one tagged fence exists in the tree.

## Verification at closure

| gate | result |
|---|---|
| Full h-mad suite | `2792 passed`, 0 failed |
| Phase 6a gap analysis | **100.00% (49/49)** ACs satisfied |
| Phase 6a-prime | `ASSESSMENT: READY_TO_MERGE`, no Critical, no Important |
| Phase 5f wire registry | `WIREREG: PASS registered=14 verified=14 broken=0` |
| Mutations, feature spec | `ALL_CAUGHT mutations=91 caught=91 survived=0` |
| Mutations, wire spec | `ALL_CAUGHT mutations=8 caught=8 survived=0` |
| Anchor sweep, whole dir | `ANCHORS_OK specs=42 mutations=526 ok=526 drifted=0` |
| impl-plan precheck | `issues=11` — the FR-4 grammar's deliberate PLACEHOLDER specimens |

Cycle counts: plan 91, design 100, impl-plan 51, iterate 0.

## What the 5e gates actually established

Not "the tests pass" — that a green suite cannot self-certify is the whole reason 5e exists.

**Revert tests.** Reverting production only reproduced each task's RED split exactly: Task 4
`62 failed, 98 passed`; Task 5 `4 failed, 18 passed` and `1 failed, 161 passed`. Every revert was
blob-asserted in both directions before the run, and every restoration was verified by **executing
the symbol** rather than reading the source — `_gate_block()` returning a real `Block` with
`info=' hmad:exec'` and 317 chars containing `h_mad_audit_gate.py` is what proves the wire, where a
diff proves nothing.

**Wiring.** Task 5 is shape `wiring`, so the load-bearing property was each WIRE-PIN's failure
*reason*, not its count. Both pins failed on an empty call record —
`_gate_block must call dbe.extract exactly once`, `assert 0 == 1` — never on a missing symbol. A pin
that REDs on `ImportError` goes green the moment the callee exists, wired or not; a first 5d
dispatch correctly **refused** for exactly this reason, and RED step 0 (`9873ace`) exists because of
that refusal. The four `wire-revert-*` rows mechanize the per-callee wire-scoped revert and
`wire-unconditional` covers the opposite direction.

## Open items carried out of this feature

- **#142 — D2 residual.** Nothing detects a parked `.json.pending` mutation spec that is never
  moved back. The parking convention itself is sound and was exercised here.
- **#152, #153, #154, #155 — four tooling defects**, all found by this feature's own closure and
  all in the same family: an output contract a prompt never spells, or a gate reading the wrong
  instrument. See the Learnings section.

## Learnings

**A gate's zero is only a measurement if the instrument can read that input.** `EVIDENCE: NONE
tools=0` fired on a codex review that demonstrably read the tree — every cited line verified — because
the gate parses agy's NDJSON and codex logs are `codex-text` (#154). Separately, `PHASE7:
match_rate_unreadable` fired on an analysis stating its rate correctly, because the parser accepts
`match rate:` but not the `match_rate=` its own template emits (#155). Both fail closed, which is
right; both cost a cycle to diagnose, because the blocker text describes a real hazard that was not
this one.

**Briefing a reviewer with the answer removes its reason to read.** The same 740 KB prompt returned
`tools=12` with no appendix and `tools=0` once it was handed the confirmed conclusion and told not to
re-litigate — and the blind run still wrote 2154 fluent bytes (#153). Brief with the question and the
paths, never the answer.

**One review pass would have shipped this feature with a defect.** 6a-prime round 1 found the code
duplicated the key-validity policy; round 2, on the fixed tree, found the code correct and the *plan*
stale; round 3 cleared it. Each round found something the previous could not have.

**An unlanded mutation reports as a kill.** Verifying the 6b fix, the first API-side mutation did not
match its target, and the pin "passed" against an unmutated tree. Redone with a landing assertion,
both call sites red the pin. Without that assertion the fix would have been recorded as verified on a
no-op.

**A reading belongs to the tree it was taken at.** A gap analysis dispatched concurrently with the
6b fix measured a tree being rewritten underneath it and reported `13 failed`, which marked a
satisfied AC as failed and would have published `97.96%`. Three readings at three instants isolated
the torn one. The two dispatches looked independent and shared a file.

## Version History

- v1.0 (2026-09-07, closure `4ecc4c4`): Phase 7 report written at feature closure.
  `PHASE7: READY blockers=0`; full suite `2792 passed / 0 failed`; gap analysis 100.00% (49/49);
  6a-prime `READY_TO_MERGE`. Every figure here was re-derived by the orchestrator at the closure
  commit rather than carried from the dispatch reports that first produced them.
