# audit gate — first field verification of the suite and leg-set gates (#91, #11/H3)

**Date:** 2026-09-07 · **Gates:** `h_mad_audit_gate.py` `--project-tests` (#91, `a90c365`) and
`--legs` / `--exit-check` leg-set refusal (#11/H3, `9a31357`+`6f2f227`)

## Why this exists

Both gates shipped with full offline coverage — 2936 tests, `ALL_CAUGHT` mutation batteries — and
**neither had ever run on real content.** That combination is the shape this repo has been burned by:
`pin-agents-tail-banner` had every offline gate green while the matcher matched **0 of 5** real
banners, and only the live run found it.

The measurement that prompted this: of the **25** `.gated.json` stamps in the repository, `suite` is
`null` in **25/25** and no stamp carries a `legs` key. That is not a defect — the newest stamp was
committed 12:51:54 and #91 landed 13:04:51, thirteen minutes later — but it means the fields had
never been exercised outside a fixture.

## Method

Real archived audit reports, run in a scratch directory so no committed stamp was written:

- reports: `doc-block-exec.plan.audit.v43.codex.md`, `…v44.codex.md` (both genuinely `PASS must=0 should=0`)
- gated document: `doc-block-exec.plan.md` (688 KB)
- suite: the real scoped project root `h-mad/tests` — not a stub, not `--suite-cmd`
- legs: `--legs codex --legs agy`

Predictions were recorded **before** the run, not after.

## Result — 5 of 5 predictions matched

```
######## CYCLE A — v43, legs=codex+agy, real suite ########
SUITE: PASS passed=2936 failed=0
GATE: PASS must=0 should=0 gated=1
GATE-CLASS: build=0 measurement=0 untagged=0 ack_refused=0
GATE-LEGS: agy+codex
[H-MAD] doc-block-exec gate PASS

######## CYCLE B — v44, SAME legs, real suite ########
SUITE: PASS passed=2936 failed=0
GATE: PASS must=0 should=0 gated=1
GATE-CLASS: build=0 measurement=0 untagged=0 ack_refused=0
GATE-LEGS: agy+codex
[H-MAD] doc-block-exec gate PASS

######## STAMPS ########
{
 "verdict": "PASS",
 "files": {
  "doc-block-exec.plan.md": "16fa8fbe813e24b19d1098b64fbb581389b8c866a1e792682522c921b2d04a80"
 },
 "suite": "PASS",
 "legs": [
  "agy",
  "codex"
 ]
}
{
 "verdict": "PASS",
 "files": {
  "doc-block-exec.plan.md": "16fa8fbe813e24b19d1098b64fbb581389b8c866a1e792682522c921b2d04a80"
 },
 "suite": "PASS",
 "legs": [
  "agy",
  "codex"
 ]
}

######## EXIT-CHECK A+B  (expect READY legs=agy+codex) ########
EXIT: READY cycles=A.json,B.json legs=agy+codex
rc=0

######## CONTROL: same stamps, B's leg set changed by one ########
control legs: ['agy', 'codex', 'doc-auditor']
EXIT: BLOCKED reason=legs_changed:agy+codex|agy+codex+doc-auditor
  the two cycles ran different reviewer legs, so the streak measures two different questions. Σmust tracked the leg count on #18 and the exit was reset four times by legs, never approached by the documents (#11/H3). Run two cycles under the new set — that IS the new baseline.
rc=0
######## DONE ########
```

## What the control bought

`READY` on its own proves nothing: all 25 archived stamps would have produced the same
comparison-never-ran silence. The control is stamp B with **exactly one field changed** — its leg
set gaining `doc-auditor` — and it flipped to `BLOCKED` naming both sets. The comparison is live,
not vacuous.

## Findings

1. **The suite did not flake.** `2936 passed` on two independent runs over one tree. This was the
   pre-registered outcome that would have falsified #91's *premise* rather than its code:
   `docs/skill-candidates.md:1277` records this repo producing 6, 3 and 0 failures across runs over a
   single working tree. One clean pair is a data point against that history, not a refutation of it.
2. **The emission order is four lines, not three.** Actual: `SUITE:` → `GATE:` → `GATE-CLASS:` →
   `GATE-LEGS:`. `SUITE:` printing FIRST is real and was undocumented; `SKILL.md`'s registry entry
   described a three-line sequence. Harmless — nothing anchors on it, and `GATE_RE` matches by line —
   but a documented order that omits a line is a claim that does not survive execution. Corrected in
   the same commit as this file.

## What this does NOT establish

The flags are proven to WORK. They are still three things an orchestrator must remember on every
cycle, documented in `SKILL.md` prose — which is precisely the "instruction an orchestrator can skip"
that `h_mad_audit_gate.py` names as the reason 91 cycles ran with a red suite. `h_mad_audit_cycle.py`
invokes the gate at `:627` and passes none of them, so a cycle driven through the driver still records
`suite: null` and no leg set, and its exit gate is refused for `suite_unmeasured`. This run removed
the *does-it-work* risk and left the *will-anyone-pass-it* risk untouched.
