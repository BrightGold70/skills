# Report: tdd-gate-fail-opens

**Branch:** `feature/tdd-gate-fail-opens` · **Range:** `15681a53..35cd43bd` (Phase 5c baseline to HEAD)
**Match rate:** 100% (8/8 FRs, 44/44 ACs) · **6a-prime:** `READY_TO_MERGE` (cycle 7 of 7)

## Executive Summary
Both TDD gates (Claude `h-mad-tdd-gate.sh` and Codex `h-mad-codex-tdd-gate.py`) now resolve every
write target through one shared canonicaliser (`h_mad_target_identity.py`). An unresolvable target
is refused `judge-error` when governed, the Codex patch-header grammar is read exactly, the judge
reap is bounded, and the resume oracle reads the session id from the git dir. The feature closed
at 100% match after one iterate cycle and seven architectural-review cycles. The full suite has one
failure, a known pre-existing drift in the live-binary test. No failure belongs to this feature.

## Summary
Tasks 0-12 (with T10 split into 10a callee and 10b wiring) were built test-first through Codex,
each as a RED commit followed by a GREEN commit (`git log 15681a53..HEAD --oneline`). The key
decisions came from the operator on 2026-09-30:
- The Codex cell `M-18 M-14`/step3 joined the approved deny-to-allow set, which grew from six to
  seven keys.
- F2, the Claude root-open refuse, was kept, with design v1.4 narrowing it.
- The arm-2 component is the on-disk spelling (design v1.5).

Phase 6b then fixed six defects found by review and gap analysis. Two of them were regressions this
branch had introduced: the Codex M-6 `..` fail-open and the HemaSuite pin drift.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 2 (`ls docs/01-plan/features/tdd-gate-fail-opens.plan.audit.v*` → v1 p1 + agy, v2 p1; the v2 agy leg is `docs/03-analysis/tdd-gate-fail-opens.plan-audit-c2-agy-unscored.md`). Plan Version History v1.2 answers cycle 1 and v1.4 answers cycle 2, "the second and final gating round". |
| Design audit cycles | 2 (`ls docs/02-design/features/tdd-gate-fail-opens.design.audit.v*` → v1 p1/p2, v2 p1/p2). Design Version History: v1.1 answers v1, and v1.2 answers v2. |
| Impl-plan audit cycles | 2 (`ls docs/01-plan/features/tdd-gate-fail-opens.impl-plan.audit.v*` → v1 p1/p2, v2 p1/p2). Impl-plan Version History: v1.1 answers round 1. v1.2 answers round 2, where the agy p2 pass was hollow and was disregarded. |
| Iterate cycles (Phase 6b) | 1 (analysis v1 at `1d454948`: 75%, one gap. Analysis v2 at `f75ca887`: 100%. Sources: `docs/03-analysis/tdd-gate-fail-opens.analysis.v1.md` and `.v2.md`, §"Match Rate") |
| Final match rate | 100% (8/8 FRs, 44/44 ACs, from `grep -n "Match Rate" docs/03-analysis/tdd-gate-fail-opens.analysis.v2.md`) |
| 6a-prime architectural review | `READY_TO_MERGE` at cycle 7 (`docs/03-analysis/tdd-gate-fail-opens.archreview.v1..v7.md` → v1-v4 `WITH_FIXES`, v5 `READY_TO_MERGE`, v6 `WITH_FIXES`, v7 `READY_TO_MERGE`). The cap is 2 cycles. The operator authorised cycles 3-7, but analysis v2 item 9 notes that this authorisation is not separately recorded in the repo. |
| Tests | Full `h-mad/tests` suite: 4871 passed, 1 failed (source: the `594fe50b` commit message, `git log -1 --format=%B 594fe50b`). The failure is `test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches`, a pre-existing live-binary drift that this feature did not cause. The targeted set was 665/665 at `f75ca887` (analysis v2 §Test Results). |
| Phases with back-propagation | Phase 5 and Phase 6, from operator decisions on 2026-09-30. Spec v1.5 added the seventh approved key. Plan v1.5 and impl-plan v1.3 propagated it. Design v1.3 carried the same decision, v1.4 narrowed the F2 root-open rule, and v1.5 made the arm-2 component the on-disk spelling. Sources: each document's §Version History. |

Other evidence at HEAD:
- Mutation: `codex_gate_judge_wiring` ALL_CAUGHT 34/34 (`594fe50b`), `claude_gate_judge_wiring`
  43/43, `target_identity` 8/8 (`f75ca887`).
- Anchors: `ANCHORS_OK drifted=0`.
- Comparator: `COMPARE: PASS softened=7 approved=7`.
- Wire registry: `WIREREG: PASS registered=44 verified=44` (`106421f0`).

## What Went Well
- **The gap analysis rebuilt the spec's M-6 fixture itself and did not trust the probe.** That
  found v1 Gap 1 (`..` after a symlink collapsed lexically before the walk). The M-6 fixture was a
  Codex fail-open that this branch had introduced, because the baseline `15681a53` denied it. It
  was fixed in `8816590e`/`f75ca887` with mutation row TI8. A 20-spelling `..` sweep over three
  trees then found no new fail-open.
- **Revert probes and new mutation rows came with every 6b fix:** CX-CWD-RECHECK (F1, `7e6bee62`),
  CG-PARENT (pin drift, `e1dfed23`), CG-PRODNAME (hard-link name, `2a99ef81`), TI8 (M-6) and
  CX-ROOT-ONDISK (`594fe50b`). Each commit records its revert-probe failure count and its
  ALL_CAUGHT score.
- **Cross-repo acceptance was run live.** The HemaSuite pin-drift brief was confirmed against the
  symlinked hook (`test_h_mad_tdd_gate.py` 9 passed in HemaSuite), and the fix was not accepted on
  the skills suite alone. The report also established that the pin was right and the branch was
  wrong: skills main and `15681a53` both gave `test-missing`.
- **Two measurement defects were caught before they certified anything.**
  - T0's `fr8()` ran FR-8 as `python3` through the fixture PATH shim, which the Codex gate refuses
    as untrusted. As a result, all three FR-8 cells denied for that reason on both trees and
    measured nothing. It was fixed in `196f4d70` with a `/usr/bin:/bin` control.
  - The 5c wire pins were h-mad-relative and never matched pytest's repo-relative node ids. They
    were re-registered in `106421f0`.
- **Review findings were treated as claims.** archreview v4 #1 was rejected with a line citation:
  the check is present at `h-mad-codex-tdd-gate.py:260`.

## What To Improve Next Time
- **Build fixtures where the two candidate rules give different answers.** M-6 and the pin drift
  both survived green suites for the same reason: in the fixtures, both rules gave the same
  answer. The lexical `..` and the kernel `..` agreed wherever no symlink came before the `..`.
  `$CANON_PREFIX/$NAME` and `${CANON_TARGET%/*}/$NAME` agreed wherever no intermediate directory
  was missing. For every normalisation or path-join rule, add one fixture per rule pair in which
  the two rules produce different results. The Task 6 differential still lacks such a fixture
  (Carry Items).
- **Pin the single-source contract's field semantics before the first review cycle.** F3
  oscillated across four cycles:
  - v1 #3 and v2: the gate must not scan for the on-disk name itself, so the scan moved into the
    canonicaliser (`d06d82f6`).
  - v4 #3: the canonicaliser must not alter the spelled component, because design v1.2 said
    "spelled".
  - Design v1.5 then settled the field as the on-disk spelling.
  - v6: the Codex root fallback still passed the spelled root (`594fe50b`).

  The design should have defined what `component` holds on every arm-2 path, root included, before
  6a-prime began. Most of cycles 3-7 were spent converging on that one definition.
- **Record a cap override when it is granted, not afterwards.** Cycles 3-7 ran past the cap of
  two, and analysis v2 notes that the authorisation is not in the repo. Write an override line into
  the state or the archreview doc at each cycle that exceeds the cap.
- **Scope a gap-analysis measurement to a commit, not to the working tree.** Analysis v2 had to
  exclude uncommitted edits (the arm-2 fix for `_canonical_root`) that appeared during the
  measurement. Run the analysis on a `git archive` copy by default, as v2 did by hand.

## Carry Items
Operator items (analysis v2 §"Design-vs-spec items"; not defects, not counted in the rate):
- **D-1**: the F2 root-refuse before governance (`h-mad-tdd-gate.sh:243-246`) is kept by operator
  decision and narrowed in design v1.4. The spec's FR-3 text still lags it.
- **D-2**: Codex parity on a mode-000 root is not met, because `rglob` swallows `EACCES`.
- **D-3**: the design v1.5 conjunct residual. A mis-cased existing root makes
  `CANON_COMPONENT = CANON_ROOT` false.
- **D-4**: the spec's M-18 row, AC-3.3 and AC-6.1 still state the unfixed Codex M-14 cell as
  allow.
- **N-1 (candidate D-5)**: a `..` through a mode-0311 directory is now refused `judge-error` when
  governed. This includes an exempt test-file write that the kernel allows. It is fail-closed. The
  operator can accept and document it, or narrow `h_mad_target_identity.py:92` to a lexical parent
  for non-symlink directories.

**Operator decisions, 2026-09-30 (post-merge):**
- **D-1, D-4 — amend the spec.** FR-3 is to state the design v1.4 root-refuse narrowing. The M-18
  row, AC-3.3 and AC-6.1 are to state the unfixed Codex M-14 cell as deny `judge-error`.
  Documentation only.
- **D-2 — fix parity.** The Codex gate refuses `judge-error` when the selected root cannot be
  entered (`X_OK` false), before `_any_phase5_status` runs. Add a mode-000 pin on both gates.
- **D-3 — drop the conjunct.** The Claude root-refuse fires on arm 2 whenever the root is not `-d`
  or not `-x`, without the `CANON_COMPONENT = CANON_ROOT` test. A root that cannot be entered is
  necessarily the failing component. Add a mis-cased mode-000 pin.
- **N-1 — narrow.** At `h_mad_target_identity.py:92`, an existing non-symlink directory takes the
  lexical parent (`os.path.dirname`) and does not open it. Add a control cell for the 0311 exempt
  row. The symlink branch (`:90`) is unchanged.
- D-2, D-3 and N-1 are code changes, owed as a follow-up TDD change on `main`.
- **Closed** in `962c47fb` (branch `fix/tdd-gate-residuals`): D-2, D-3, N-1 fixed; D-1/D-4 spec
  v1.6 and design v1.6 amended. Pins `test_mode_000_project_dir_refuses`,
  `test_codex_mode_000_root_refuses_whatever_the_phase`,
  `test_dotdot_through_unreadable_directory_is_lexical`; mutations TI9, CX-ROOT-ENTER, CG-ROOT-CONJ,
  CG-ROOT-000 ALL_CAUGHT. Full suite 5221 passed / 1 known failure; HemaSuite gate tests 9/9.
- **Review follow-up:** a fresh-context review found `.`-then-`..` spellings
  (`tests/./../src/prod.py`) resolving under `tests/`, so the Claude gate allowed a governed
  production write. One shape was new with N-1; two were already on `main`. The canonicaliser now
  skips `.` components (mutation TI10).

Carried residuals (analysis v2 §"Carried findings and residuals"):
- `session_id_from_git_dir` (`h_mad_resume_decision.py:59-64`) catches only `OSError`, so a
  non-UTF-8 id file escapes as `UnicodeDecodeError`. It fails closed with rc 1 but does not print
  the `cannot_judge` token.
- Two load-sensitive timing flakes: `test_run_bounded_plain_timeout_is_not_reap_failure` and
  `test_timeout_kind`.
- Three mutation specs that predate this feature (`codex_gate_judge_wiring`,
  `claude_gate_judge_wiring`, `tdd_judge_scoring`) still use the absolute
  `/opt/anaconda3/bin/python` as `command[0]`.
- `reading-fixed.txt` has no `MANUAL:` R-4/R-5 lines (0 fixed against 80 unfixed). The comparator
  keys only `REPRO` lines.
- Low-severity impl-plan 5d items:
  - The T0 absent-line control was never run.
  - T4 `marker[:-1]` has 0 mutation rows.
  - No committed mutation row restores the pre-walk `normpath`. TI8 mutates the symlink branch
    instead.
  - There is no committed record of the T7 re-check of the adapters' other gate sentences.
- Census row counts exist only at `f61bb908`. The five rows added since then are scored only in
  commit messages.

Task 6 differential blind spot: the fixture root has no prefix that the name map can map, so every
judged cell is `no-test-resolved` whichever path the gate judged. The differential therefore cannot
tell which path was judged, and it hides N-1's class and the second Gap-1 instance
(`tests/l/new/../../prod.py`). AC-1.8's absent-leaf and absent-parent cells and the hard-link
mixed-names cell are still absent from it.

Skill candidates filed on main in `198f2908` (`docs/skill-candidates.md`, "HemaSuite #10 handover
triage"):
- **(a)** An agy report that says `Evidence: 0 files opened` is scored zero-evidence even when its
  transcript shows real reads. Status: open, parked.
- **(c)** The Phase 5d/5e assembler never asks for a mutation spec. Status: open, parked.

## Version History
- v1.0: Initial report draft (2026-09-30) at HEAD `35cd43bd` against spec v1.5, plan v1.5, design
  v1.5, impl-plan v1.3 and analysis v2. Match 100%, 6a-prime `READY_TO_MERGE` at cycle 7, full
  suite 4871 passed and 1 failed (pre-existing live-binary drift).
