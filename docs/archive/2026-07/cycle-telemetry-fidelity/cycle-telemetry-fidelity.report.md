# Report: cycle-telemetry-fidelity

## Executive Summary

Both H-MAD cycle counters now derive from the versioned artifacts each cycle writes instead of
from state fields nothing ever incremented, so the two drift warnings in `h_mad_telemetry.py` can
fire for the first time since they were written.

## Summary

`audit_cycles` and `iterate_cycles` were seeded to zero at `h_mad_state_write.py:53-54` and
incremented nowhere, so every telemetry row ever recorded claimed the run consumed no cycles.
Rather than reintroduce a counter that an orchestrator step must remember to advance — the exact
dependency that failed — the counts are now derived from the `.audit.v<N>.md` and `.analysis.v<N>.md`
files on disk, which backfills every historical feature for free. The one gap in that evidence was
Phase 6b overwriting its analysis in place, so the protocol now emits one artifact per iterate
cycle. Shipped with the first tests `h_mad_telemetry.py` has ever had.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 1 |
| Design audit cycles | 2 |
| Impl-plan audit cycles | 2 |
| Iterate cycles (Phase 6b) | 0 |
| Final match rate | 100% |
| 6a-prime architectural review | `READY_TO_MERGE` |
| Tests | 498 passing / 0 failing (baseline 454, net +44) |
| Phases with back-propagation | None |

Baseline commit (5c): `7ae2d78`. Phase 5 closure commit (5g): `4a7995b`.

## What Went Well

- **The design audit caught a defect that would have shipped as a platform-dependent bug.** The
  design said "case sensitivity follows the glob" for AC-7.4. The default macOS filesystem is
  case-**insensitive**, so `Path.glob` matches `Feat` when asked for `feat` on this machine and
  would not on Linux ext4 — the requirement would have passed or failed by machine. It is now
  enforced in code via a `str.startswith` re-check, with a test that fails a glob-only
  implementation specifically here.
- **Deriving instead of counting made the fix retroactive.** Three archived features report their
  true counts with no migration, and the append-only log is never rewritten.
- **Codex reported `BLOCKED` rather than making the suite green.** Two Task-2 tests created
  artifacts under `<tmp>/docs` but invoked `summary` without `--docs-root`, so the audited
  resolution rule correctly looked elsewhere. It diagnosed this precisely instead of modifying the
  tests — and those two had passed RED only because `--docs-root` did not exist yet, a RED that
  proved nothing.
- **Verification against live data, not fixtures, closed the loop.** The feature derives its own
  audit history (`plan 1, design 2, impl_plan 2`) correctly, and the Task 4 protocol change
  produced an `analysis.v1.md` that the Task 1 module then discovered — proving the integration
  rather than asserting it.

## What To Improve Next Time

- **"Every new test must FAIL" is wrong for a refactor task.** Task 3 preserved behaviour, so only
  one test could legitimately be RED — "the duplicate is gone". The instruction forced Codex to
  bolt `assert "AUDIT_VERSION_RE" not in source` onto two regression guards to manufacture
  failures. Dispatches for refactor tasks should say so explicitly and name which tests are guards.
- **Review verdicts were wrong twice while their reasoning was right.** Across three coverage
  reviews agy produced 12 findings: 9 genuine, 2 whose stated premise was false but whose
  underlying point was real, 1 pedantic. Taking verdicts at face value would have been wrong twice;
  discarding findings with false premises would have lost two real defects. Verify each claim
  against the source.
- **Shell-measured diff sizes understate the payload.** Sizing the 6a-prime prompt with
  `git diff | wc -c` reported 21 KB because the shell `git` is rewritten through rtk; the assembled
  prompt was 67.6 KB, past the reviewer cliff. Measure with `subprocess.run` when sizing a prompt.
- **A defect caught in an audit can reappear one layer down.** The emptiness-vs-zero distinction
  was fixed in the design after the design audit, then re-entered at the test level in Task 2 and
  had to be caught again by the coverage review.

## Carry Items

- **Same-version collision between a live root and the archive is unspecified.** If both
  `docs/01-plan/features/f.plan.audit.v2.md` and `docs/archive/*/f/f.plan.audit.v2.md` existed, the
  archive wins by dict overwrite. Cannot arise from the documented workflow (archiving moves files),
  so recorded as undefined rather than wrong.
- **`cmd_summary` scans each audit root twice** — `audit_maps` and `audit_cycles` both call
  `audit_artifacts`. Correct and within the NFR; not optimised.
- **The `> 3` drift thresholds have never been exercised** because the counters were dead. They can
  fire now; whether 3 is the right number is a question this feature makes answerable but does not
  answer.
- **Nine skill defects filed to `docs/skill-monitoring.md`, none fixed here** — J1 (`launch` pins a
  handle the pane never has, reproduced 2×), J2 (pin file is cwd-relative), J3 (tail reads of a TUI
  are stale), J4 (F8 re-opened — the remedy message shipped, the dependency gap did not close), J5
  (`--claim` needs `--create`), J7 (F13 residual: the pin **file** leaks into the dispatch tests, so
  the Phase-5-mandated `pin-agents` guarantees 17 failures at 5f), J8 (`elapsed_min` ≈ 56 years),
  J9 (flaky `test_alive_cmux_true`). J6 was investigated and **disproven**, recorded as such so the
  correlation is not re-filed as causation.
- **Wave 1 of `docs/01-plan/h-mad-remediation-sequence.md` is complete; Waves 2–5 are not.** Wave 2
  (`PREFLIGHT:` token + mandated reads) is the next item, and J7 should be folded into it since both
  concern preflight correctness.

## Version History
- v1.0: Initial report draft.
