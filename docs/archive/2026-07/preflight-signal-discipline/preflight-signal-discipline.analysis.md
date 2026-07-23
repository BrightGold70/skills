# Gap Analysis: preflight-signal-discipline

**Feature**: preflight-signal-discipline (Wave 2 of `docs/01-plan/h-mad-remediation-sequence.md`)
**Base**: `aa1f01a` → **Head**: `fcea6ab` on `feature/191-preflight-signal-discipline`
**Suite**: 530 passed

## Match Rate

**Match rate: 100% (26/26 acceptance criteria satisfied)**

25 of 26 are pinned by an automated test that cites the AC in its docstring. The 26th (AC-6.2) is
satisfied by measurement, deliberately and by design — see below.

## Per-FR verification

| FR | ACs | Evidence |
|---|---|---|
| FR-1 `PREFLIGHT:` token | 1.1–1.6 | 6 tests in `test_hmad_dispatch.py`; live-verified all four verdict shapes against real Orca |
| FR-2 verdict never changes exit code | 2.1–2.4 | exit-0 asserted for PASS *and* FAIL; AC-2.4 asserts the prohibition comment + literal `PostToolUseFailure` within 15 lines of the single emission site |
| FR-3 `UNRESOLVED` is informational | 3.1–3.3 | 3 tests; AC-3.3 strengthened from a vacuous loop-guard to require the FAIL line exist before asserting what it lacks |
| FR-4 Phase-5 mandated read | 4.1–4.4 | 4 doc-contract tests in `test_h_mad_preflight_docs.py` |
| FR-5 `ASSEMBLE:` mandated read | 5.1–5.2 | 2 doc-contract tests |
| FR-6 pin file cannot leak (J7) | 6.1–6.5 | 4 tests + AC-6.2 by measurement |
| FR-7 automation precheck + docs | 7.1–7.2 | 3 doc-contract tests, incl. the readiness clause added after 6a-prime |

## AC-6.2 — satisfied by measurement, not by unit test

> "The suite result is byte-identical in pass/fail counts whether that pin file is present or absent."

A test *inside* the suite cannot honestly assert a property *of* that suite; it would be asserting
its own context. This was flagged as measurement-verified in the spec, the design's Test Plan, and
the impl-plan, rather than papered over with a test that looks like coverage and is not.

Measured at `fcea6ab`:

| condition | result |
|---|---|
| `.h-mad/orca-pins.env` absent | `530 passed` |
| `.h-mad/orca-pins.env` present | `530 passed` |
| baseline before the fix (module only) | **17 failed / 136 passed** |

Identical. The defect is closed against the exact condition that produced it.

*(Method note: an initial comparison reported a false failure because it compared the whole pytest
summary line including elapsed time — `11.75s` vs `11.57s`. The counts were identical throughout.
Recorded because a measurement harness that produces false negatives is worth remembering.)*

## Findings from the review chain

| Gate | Result |
|---|---|
| plan audit v1 | `GATE: PASS must=0 should=0` |
| design audit v1 | `GATE: FAIL must=1` — module-scope `tempfile.mkdtemp()` leaks a directory per collection |
| design audit v2 | `GATE: PASS`, 1 nit taken (PID-scope the path) |
| impl-plan audit v1 | `GATE: PASS must=0 should=0` |
| 5d coverage review | 2 must-fix — weak AC-6.1 assertion; `Path` vs `str` contract mismatch |
| 6a-prime cycle 1 | `ASSESSMENT: WITH_FIXES` — 3 findings |
| 6a-prime cycle 2 | `ASSESSMENT: READY_TO_MERGE`, findings None |

Two review findings were accepted in substance but **rejected in prescribed direction**, both
recorded in the docs they changed:

1. The 5d reviewer proposed casting `_NO_PIN_FILE` to `Path` inside the tests because the impl-plan
   said `os.path.join`. That inverts TDD — it treats the plan as authoritative over the test. The
   implementation contract was changed instead.
2. 6a-prime cycle 1 held that `hmad-dispatch send` is mechanically unguarded, so consumers who skip
   the protocol read "remain vulnerable to the exact same hazard". Verified false: `send` already
   refuses a stale handle (`terminal_handle_stale`, rc=1, nothing sent — shipped `912b93a`). The
   correction was put to the reviewer, which accepted it in cycle 2.

## Carry items

- **The mandated reads are protocol, not machinery.** FR-4/FR-5 oblige an orchestrator to assert
  `PREFLIGHT: PASS` / `ASSEMBLE: PASS`; nothing enforces it mechanically. Stated Out-of-Scope in the
  spec and confirmed as a real residue by 6a-prime cycle 1. Wave 3's dogfood run is the exercise.
- **The CONFLICT case is not mechanically guarded.** `send` refuses a *stale* handle, but two agents
  resolving to one **live** handle is undetectable at that boundary — only the protocol read catches
  it. Narrower than the original hazard, still open.
- **Report-contract gap.** The Task-2 GREEN dispatch returned `DONE_WITH_CONCERNS` while stating no
  concern anywhere in its report. A verdict that declares doubt without naming it is unactionable.
  Worth a monitoring entry.

## Live validation worth recording

During this feature's own 6a-prime re-review, agy's pane restarted and its handle rotated. The
mandated read — added two commits earlier — fired:

```
agy -> term_bc8bc0c4… STALE (no such terminal — re-pin or relaunch)
PREFLIGHT: FAIL stale=agy
```

and `hmad-dispatch send` refused. The dispatch was stopped, agy re-identified by content, re-pinned,
re-asserted to `PREFLIGHT: PASS`, and re-dispatched. This is the same handle-rotation class that lost
a Task-2 RED dispatch on HemaSuite and put this wave on the board — caught here by the feature under
review, on its author, without the doc test being the thing that noticed.

## Version History
- v1.0: Phase 6a gap analysis.
