## Summary
This is the round-2 GATING audit (codex-leg stand-in) of impl-plan v1.9 (`be702c08`, diff `7e1c48e3..be702c08`), checked against design v1.14 D21 (`8fd0f637`), spec v1.20 AC-3.9/AC-3.6, and the tree at HEAD. `h-mad/` has not changed since `d9f25dc2`.

How I checked it: I applied the Task 14a and 14b production edits and the stub edits verbatim to a `git archive HEAD h-mad` copy, re-anchored `verb-assemble-drop`, and ran the two existing modules: production (no `--pass-root`) is `86 passed` both before and after the edits. Every remaining anchor in 14a–14c matches as stated: each quoted old text gives exactly the count claimed under its stated unit, and `--check-anchors` on all 34 specs naming the three scripts reads ANCHORS_OK in the edited copy. I then wrote a 14-id probe module shaped like the planned 14a/14b tests and ran it in three states: RED (production at HEAD), GREEN (edits applied), and under nine PS mutants (PS2, PS4 ×2, PS5, PS6, PS7, PS9, PS14, PS15). Results:
- The GUARDs pass at RED.
- The RED ids fail on assertions, not on import or collection errors.
- Every mutant was killed, and PS6's `prompt_divergence` explanation reproduces.

All round-1 findings are closed except one Nit, which is partly open. Two new blocking build defects were found by execution, not by reading:
- The path-scope module is over the 40 s judge budget.
- The production GUARD's "no `*.here.txt`" check fails once any armed cycle has run earlier in the same session.

Evidence: 23 files opened, 52 greps run (plus 14 pytest invocations in the scratch copy).

Not run:
- The full `h-mad/tests` suite. The archive copy carries no real git history, so tests that `git show` real shas would fail spuriously.
- The mutation harness runs (AC-T14b.4 ALL_CAUGHT, AC-T14d.2).
- The 14c module, which does not exist yet: its RED was checked only at the CLI level. At HEAD, `assembler-read`/`assembler-check` print `QUARANTINE: REFUSED reason=internal:UsageError` rc 2, and `require --verb assembler` prints `REQUIRE: STOP reason=internal:UsageError` rc 2.

Scratch copies were deleted after the run (see the final message).

## Round-1 closure
- M1 (the empty-array guard `[ -n "${scope_arg[@]+x}" ]`): CLOSED. Edit 5 now reads `if [ "${#scope_arg[@]}" -gt 0 ]; then  # M:PATH-SCOPE-CHECK-ARMED` (plan line 2000). With all 14a/14b edits applied verbatim, `test_grok_audit_surface_wrapper.py` + `test_hmad_dispatch_audit_cycle.py` gave `86 passed`. `grep -c 'scope_arg\[@\]+x'` prints 0 and `grep -c 'M:PATH-SCOPE-'` prints 5, so AC-T14b.3 holds. My GUARD probe passes at RED and GREEN and fails under PS14 and PS5.
- M2 (the GUARD names `path_scope` before the parameter exists): CLOSED (lines 1797–1799, 1873, 1894–1896). The switch-off call without the keyword equals the `7e10f543` reference for `[plan]`/`[design]`/`[impl-plan]` at both RED and GREEN, and PS2 kills all three.
- S1 (`raising=False`): CLOSED (lines 1800–1802, 2269, 2296–2297, 2313–2316). The precedent is real: `test_grok_audit_surface_containment.py:1184`.
- S2 (move the fixtures out of the containment module): CLOSED. The new module is `test_grok_audit_surface_assembler_pin.py`, the containment module is unedited (AC-T14c.3), and the `command` list goes from 8 to 10 files. The four imported helpers exist: `containment_module` is a fixture at line 275/276, and `_containment_cli`/`_containment_main`/`_assert_containment_token` are at 309/316/323.
- S3 (row 2 is non-discriminating): CLOSED. `test_assembler_read_sha256_repository_reads_unreadable` was added. I re-ran the premise: `git init --object-format=sha256` followed by a commit gives `rev-parse` length 64 and `status --porcelain` 0 lines, on git 2.54.0.
- S4 (the pre-clause script dir and assertion order): CLOSED. In the probe, the three extra copies plus `dispatch_count == 0` first passes at GREEN, and fails on the dispatch count at RED and under PS4 (rc 4 at GREEN).
- S5 (anchor units; line 18 → 20): CLOSED. Re-run at HEAD:
  - `extra =` line: `-cF` 2, `-cxF` 1.
  - `"Audit prompt\\n"`: `-cF` 3, `-cxF` 2, and the second line of the pair `-cxF` 1.
  - `class UsageError` is at line 20.
  - All other 14a/14b/14c anchors read 1.
- Nits:
  - Four-needle zero: CLOSED. I re-ran the stated `grep -rnE … h-mad/ | wc -l` and got 0.
  - 14a replace rule: CLOSED (line 1919).
  - 14c insertion point: moot, because the module moved.
  - Routing plan-added contract to the design: PARTIAL (see Nit).

## Must-fix
- **The path-scope module, as specified, runs past the 40 s judge budget, so AC-T14d.5 fails.** The two real-cycle ids (WIRE-PIN 2, and `test_calibration_cycle_records_its_here`, which uses "the setup of the test above") each run the real `h_mad_audit_cycle.py` with the default `--report-grace 5`.
  - Measurements in the edited archive copy, at load average about 11.8:
    - One real-cycle run, 3 passes: `18.93s call` and `ELAPSED 18.92`.
    - A 13-id approximation of the module (4 of 14a's ids plus the 14b shapes, with the real cycle run twice) under the judge's `-x -q --no-header`: `13 passed, 1 deselected in 40.87s` (`real 41.70`). The real module has 20 ids.
    - The stub-driven ids take 0.17–0.60 s, so the plan's 0.63 s basis is right only for those.
  - Effect: once WIRE-PIN 2 is green, every later judge run of this module during 14b's GREEN (for example the write of edit 5, while `records_its_here` is still red) executes about 38 s of real cycles before reaching the red. The result is DENY `timeout` (`h_mad_tdd_judge.py:29` `JUDGE_BUDGET_S = 40.0`). The plan moved 14c out of the containment module for exactly this reason.
  - Fix, any of these (they can be combined):
    - (a) Pass `--report-grace 0` in both real-cycle tests. Measured: `ELAPSED 6.91`, and the test still passes.
    - (b) Run the real calibration cycle once in a module-scoped fixture, with `tmp_path_factory` stem/XDG dirs, and have WIRE-PIN 2 and `records_its_here` each assert on its result. PS12 and PS15 still each have their own target. Unverified.
    - (c) Move the two real-cycle ids into a third module under 40 s. That needs a design D21/Test Plan edit and a `command` list change.
  - Also replace the 1.5 s-per-id estimate with a measured per-id figure for the real-cycle ids.
  - instance of: a module time budget derived from the fastest member of a mixed population. The rule: budget the slowest member. The residual is load variance, so AC-T14d.5 should keep a margin rather than sit at 40 s.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `so 20 ids at up to about 1.5 s each is about`
- **The production GUARD `test_audit_cycle_without_pass_roots_does_not_pass_the_switch` fails at GREEN whenever any armed cycle ran earlier in the session.** Its new output half asserts that the stem dir holds no `*.here.txt`.
  - Why: unless a test overrides it, the stem dir is the session-wide `HMAD_AUDIT_STEM_DIR` that `conftest.py:163` sets once per session (`# M:CONFTEST-STEM-DIR`). The tests that reuse `_pass_root_case` set no stem dir of their own: WIRE-PIN 1 (listed before the GUARD), the three halt ids and the control. At GREEN each of them writes `${stem}.here.txt` into that shared dir. So do the existing `test_pass_roots_give_each_pass_its_own_cd` and `test_pass_root_report_path_lies_in_its_own_root`.
  - Measured in the edited copy: the GUARD probe passed when run first and failed when re-run after the WIRE-PIN 1 probe in the same session, with `AssertionError: [PosixPath('…/audit-stems/audit_cycle-red_plan_cycle7_run20261022T072703Z-19143.here.txt')]`. At RED it passes either way, so the defect first appears at GREEN, in the full suite and in the judge's `-x` runs. The mutation harness runs the GUARD alone and would not see it.
  - Fix, either:
    - (a) Give the GUARD its own `HMAD_AUDIT_STEM_DIR` under `tmp_path`, as WIRE-PIN 2 already does.
    - (b) Assert the absence of this cycle's own record only: `Path(str(out)[:-len("_p1.txt")] + ".here.txt")`, where `out` is the `--out` of the first recorded `assemble_calls.jsonl` row. The derivation is unverified.
  - Either keeps PS14 (`REQUIRE: STOP`/no `AUDITCYCLE:`) and PS5 (argv) killed. Write the same rule for every 14b test that asserts on the stem dir's contents: `records_its_here` already relies on WIRE-PIN 2's `tmp_path` stem dir, so state that explicitly too.
  - instance of: an absence assertion over a shared, session-scoped directory. The rule: an absence assertion reads a directory the test owns. The residual is none once every absence check is scoped this way.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `` the stem dir holds no `*.here.txt` ``

## Should-fix
- **WIRE-PIN 2's "three dispatches" reads 6, not 3, through the suite's `dispatch_count` helper once the real assembler runs.** `dispatch_count` (`test_hmad_dispatch_audit_cycle.py:290`) counts capture lines that start with `agy `. The real prompt inlines `h-mad/invariants.base.md:330` (`agy reads this verbatim as the **base** portion of the Axis B rubric, before the project layer.`), and the stub logs the prompt into the capture. I measured `assert 6 == 3` in the probe; counting lines that start with `agy --dangerously` gave 3 and the test passed.
  - The pre-clause test's `dispatch_count == 0` is unaffected: 0 at GREEN, non-zero under the mutant.
  - Fix: name the count in WIRE-PIN 2's text. Options:
    - capture lines starting `agy --dangerously-skip-permissions`;
    - the number of `--pass` specs in the cycle's collection call;
    - `init` events, as `test_pass_roots_give_each_pass_its_own_cd` does.
  - instance of: a stub-era helper reused against real production output.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `holds the clause line exactly once, three dispatches, and no`

## Nit
- AC-T14b.1 says the full suite passes "`test_grok_audit_surface_wrapper.py` and `test_hmad_dispatch_audit_cycle.py` included, unchanged". The second file is edited in this Task (stub edits, and `STUB_PATH_SCOPE_CLAUSE` from 14a). Say "their existing ids unchanged in outcome".
- Round-1 Nit (route plan-added contract to design D21) is partly open. Design v1.14 now carries the two usage branches, `here_unrecorded`/`here_mismatch` and `--stems`. It still names none of these (a `grep` over the design returns 0 for each):
  - `# M:ASSEMBLER-READ-SHA`, `-READ-DIRTY`, `-READ-ENV` or `-LAST-RESORT`;
  - "raises on load" for `clause_unavailable`;
  - the "40 lowercase hex" rule.

  Separately, 14c's mutation-row prose counts row 24 (`LAST-RESORT`) among the 16 rows "D21 requires". The design's rule (line 863) names reason guards, usage branches and `REQUIRE-OK-ASSEMBLER` only, so the split is arguably 15 design-required and 12 plan-added. The total of 27 is unaffected.
