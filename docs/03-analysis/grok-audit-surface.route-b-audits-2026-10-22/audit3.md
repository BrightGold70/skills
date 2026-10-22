## Summary
This is the round-3 GATING audit (codex-leg stand-in) of the round-2 remediation: spec v1.21 (`d78cca8d..061bde85`), design v1.15 (`8fd0f637..741f35f4`) and impl-plan v1.10 (`be702c08..1accd5a9`), at HEAD `1accd5a9`. `git diff --stat 8fd0f637 HEAD -- h-mad` prints nothing.

Closure: every round-2 must and should is closed in the text. Of the round-2 nits, one is still partly open and one item of the other is open (see Nit).

The remediation introduced one blocking defect. The plan's new `test_calibration_cycle_records_its_here[assemble_halt]` asserts on the last stdout line, and that assertion fails at GREEN. I found this by running it, not by reading.

How I checked:
- I read all three diffs in full, both round-2 reports, D21 (design lines 555–610), Tasks 14a–14d and the Task 15/16 deltas of the impl-plan, `_cmd_audit_cycle` lines 3559–3800, `install_audit_cycle_stubs`, `_pass_root_case`/`_run_pass_roots`, and `conftest.py`'s stem-dir hook.
- In a `git archive HEAD h-mad` copy under the scratchpad, I applied the 14a edits 1–5, the 14b edits 1–6 (the `here.txt` block placed right after `stem=`), the stub edits, `STUB_PATH_SCOPE_CLAUSE` and the `verb-assemble-drop` re-anchor, all verbatim. I also copied in `docs/03-analysis/probes`, because 9 `grok_audit_surface.json` rows target the probe.
- Results:
  - `test_grok_audit_surface_wrapper.py` + `test_hmad_dispatch_audit_cycle.py`: `86 passed`.
  - `--check-anchors`: `ANCHORS_OK` on 34/34 specs (files) naming the edited scripts.
  - Every 14a/14b anchor gives its stated count under its stated unit (table under Round-2 closure).
  - A real calibration cycle (real assembler and real `h_mad_audit_cycle.py`, 3 passes, stub agy) took `6.94s` at `--report-grace 0`, against `18.96s` at the default. The load average was about 11.
- I wrote a 9-id probe module shaped on the planned 14b tests, and ran two mutants by hand (PS15, and an unrowed always-true here guard).
- The copy was deleted afterwards. The real tree is unchanged (`git status --short` shows only the three pre-existing untracked paths).

Not run:
- the full `h-mad/tests` suite (the archive has no history);
- the mutation harness runs (ALL_CAUGHT);
- the 14a ids;
- the 14c module, which does not exist.

Evidence: 19 files opened, 58 greps run (plus 11 pytest invocations, 34 `--check-anchors` runs and 2 hand mutants).

## Round-2 closure
Spec/design audit (`audit2-spec-design.md`):
- **Must 1, `here` written after the `ASSEMBLE: HALT` exit** — CLOSED, and EXECUTED.
  - Design 568: "The write sits in its own `if [ "${#scope_arg[@]}" -gt 0 ]; then … fi` block, immediately after `stem=` is computed and **before the assembly loop**". The class rule is stated.
  - Spec 192: "It writes this record before assembly, so a cycle that halts at assembly has it too".
  - Plan edit 5 matches both.
  - In the edited copy, a stub `HMAD_ASSEMBLE_HALT_P2=1` cycle printed `AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2 …`, and its own stem dir held exactly one `*.here.txt` whose line is `here=<HMAD_AUDIT_CYCLE_SCRIPT_DIR>`. `$here` is that variable verbatim (`hmad-dispatch.sh:3567`).
  - The design's claim that no earlier exit yields an `AUDITCYCLE:` line holds. Lines 3559–3720 hold only `return 2` and `_need`/`_need_val` returns. The only exit between the write and assembly is the `.hmad-report` `mkdir … || return 1`.
- **Must 2, AC-6.1/AC-6.2 not in the design** — CLOSED.
  - D14 at design 427–428 carries "measured with the calibration-only path-scope clause (AC-3.9)".
  - The D15 Residuals at 445–447 carry the AC-3.9 residual.
  - The Test Plan at 803–804 pins both.
  - Plan Task 16 holds the residual verbatim: after whitespace collapse, the design sentence is a substring of the plan (`True`).
- **Should, AC-6.2 smoke-failure scope** — CLOSED (spec 289: "On PASS, MISS and INCONCLUSIVE it also pins the AC-3.9 phrase … the doc test does not assert one on that branch").
- **Should, AC-3.6 stale on `$here`** — CLOSED. Spec 192 glosses `here_changed`, `here_not_self`, `here_unrecorded`, `here_mismatch` and `dirty:unknown`, and each agrees with D21 line 577.
- **Should, D8 order omits the smoke-failure gate** — CLOSED (design 224: "On `SMOKE: FAIL`, before any doc is published, come the end reading, `assembler-check --stages resmoke` and `require --verb assembler`"). Plan Task 15 step 6 matches.
- **Nits:**
  - `assembler=unpinned` — CLOSED. Spec 194 and the Delivery row (spec 492) say so. The remaining occurrences are changelog lines, design 908 (a historical cell) and plan 2718 (an absence check).
  - Unrecognised-switch signal — CLOSED (spec 209). I executed the pre-clause case at GREEN: rc 4, `dispatch_count` 0, no `AUDITCYCLE:` line.
  - Symlink vs copy for the pre-clause dir — moot. The plan copies `h_mad_audit_cycle.py` and its three sibling imports into one dir, which I verified works at GREEN. Those three siblings import no further `h_mad_*` module.

Impl-plan audit (`audit2-implplan.md`):
- **Must, 40 s budget** — CLOSED.
  - Both real-cycle ids and the pre-clause id pass `--report-grace 0`.
  - AC-T14d.5 is at most 30 s.
  - Re-measured: 6.94 s per real cycle. Six probe ids including one real cycle ran in `8.77s` under `-x`, which is consistent with the plan's ~25 s estimate for 21 ids.
- **Must, GUARD on the shared stem dir** — CLOSED. Plan 2085–2089 says "Every test here sets its own `HMAD_AUDIT_STEM_DIR`", and design rule (iii) says the same. In the probe, the GUARD with its own stem dir passed after WIRE-PIN 1 and the halt ids in the same session.
- **Should, `dispatch_count` reads 6** — CLOSED in substance. I re-measured `dispatch_count` = 6 and init events `[1, 1, 1]`. The source the plan names for the logs is not observable, though (Should-fix 2).
- **Nits:**
  - AC-T14b.1 wording — CLOSED.
  - Row-24 split — CLOSED. Re-counted: 15 design-required rows (6–12, 14, 15, 17, 19, 20, 22, 25, 26) plus 12 plan-added = 27.
  - Routing the plan-added contract to the design — still partly open (Nit 2).

Three-way consistency (spec v1.21 ↔ design v1.15 ↔ plan v1.10):
- **`here.txt` placement and `here_unrecorded`/`here_mismatch`** — consistent in all three (spec 192, design 568 and 577, plan 1976–1981 and edit 5).
- **The AC-3.9 phrase only on PASS/MISS/INCONCLUSIVE** — consistent:
  - spec 289;
  - design 427–428 and 804 ("Smoke failure: the AC-3.9 phrase is not asserted");
  - plan Task 16 ("neither requires nor forbids it there").
- **`SMOKE: FAIL` assembler gate** — consistent (spec 192, design 224 and 580, plan step 6).
- **Counts**, re-derived:
  - The 14b ids enumerate to 11 (8 functions). 14a + 14b = 21 path-scope ids.
  - The 14c list enumerates to 25 functions and 33 ids (read 6/7, check 18/21, require 1/5).
  - Rows: PS rows 6 + 9, plus 27, = 42. The spec today has 378 rows (`len(mutations)`), so 420 rows, and 422/424 at AC-T16.3.
  - Specs naming the three scripts: 34 files.
  - AC-T14b.3 in the edited copy: 5 / 1 / 0 matching lines. 14a markers: 2.
- **Anchors at HEAD**, each matching its stated unit:
  - assembler lines 218, 453, 485, 611, 628 and 463: `-cF` 1 each;
  - dispatch 3559 (`-cxF` 1), and 3566, 3646, 3739, 3775 (`-cF` 1);
  - dispatch 3720: `-cxF` 1;
  - test file lines 19 and 197: `-cxF` 1;
  - line 197: `-cF` 2 (197 and 362);
  - `"Audit prompt\\n"`: `-cF` 3 / `-cxF` 2;
  - line 212: `-cxF` 1;
  - `class UsageError`: line 20.
- **The four rows that find line 3720** (`stem-ignores-the-dir`, `d2-audit-cycle-log-path-reused`, `verb-reuses-one-stem-per-cycle`, `verb-stem-drops-the-pid`): each is single-line, as edit 5 claims.

## Must-fix
- **`test_calibration_cycle_records_its_here[assemble_halt]` asserts that the last stdout line begins `AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2`. That is false at GREEN, so the id can never pass, AC-T14b.1 ("The 11 ids pass") is unreachable, and PS15's kill of it would be vacuous.**
  - Why: the stub `h_mad_audit_cycle.py` prints the `AUDITCYCLE:` line and then `[H-MAD] {feature} audit-cycle UNVERIFIED` (`test_hmad_dispatch_audit_cycle.py`, the stub's `--halt-reason` branch). The wrapper's `exit $?` adds nothing after it.
  - Executed in the edited copy:
    - stdout was `['AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2 passes=3 size_status=verified', '[H-MAD] cycle-red audit-cycle UNVERIFIED']`;
    - the last-line assertion failed with `AssertionError: [H-MAD] cycle-red audit-cycle UNVERIFIED`;
    - the `*.here.txt` half of the same test passed.
  - The real collection also ends with an `[H-MAD]` line. I observed `[H-MAD] gas-d1 audit-cycle UNVERIFIED` last on the real cycle.
  - Repair, either one:
    - (a) `auditcycle_lines(r.stdout) == ["AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2 passes=3 size_status=verified"]`. That is the exact line measured with 3 passes, and the form `test_verb_assemble_halt_no_dispatch` uses.
    - (b) "stdout holds exactly one `AUDITCYCLE:` line, and it begins `AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2`".
  - With either repair the id passes at GREEN. Under PS15 (the `printf` replaced by `:`) it fails on `assert len(here) == 1`, which I executed.
  - instance of: a "last stdout line" assertion over output that `h_mad_audit_cycle.py` (stub or real) produces. Its last line is always the `[H-MAD]` marker.
    - The rule: "last stdout line" is valid only for a token the wrapper itself prints last before `return`, such as `REQUIRE: STOP …`. An `AUDITCYCLE:` line is asserted through `auditcycle_lines`.
    - Swept with `grep -n 'last stdout line'` over the plan, Tasks 14–15: plan 1989, 2118 and 2522 are `REQUIRE: STOP` and correct. I executed 2118's shape for `[p2]`/`[p1]`/`[all]` and the last line equalled the token. Only 2112 is a member.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `its own stem dir: the last stdout line begins `AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2` (the`

## Should-fix
- **The fix introduced an unmarked, unrowed guard.**
  - v1.15 moves the `here` write out of the `# M:PATH-SCOPE-CHECK-ARMED` block. In v1.9, PS14 mutated that block's condition together with the write. The write now sits under its own `if [ "${#scope_arg[@]}" -gt 0 ]; then`, which carries no marker, and no PS row mutates it.
  - Hand mutant in the edited copy: that condition replaced by `true`. Production cycles (no `--pass-root`) then write a `*.here.txt`, against spec/design "With the switch off, nothing is written". The probe GUARD (`test_audit_cycle_without_pass_roots_does_not_pass_the_switch`'s shape, own stem dir) FAILED, so the mutant is killable. Nothing in the mutation spec runs it, though, so the GUARD's here-half has no evidence that it can fail on this guard.
  - The opposite mutant (`false`) is equivalent to PS15 and is covered.
  - Repair, either one:
    - (a) Mark the line `# M:PATH-SCOPE-HERE-ARMED` and add a row PS16 `path-scope-here-always` (condition → `true`, target the GUARD). In the plan this moves: AC-T14b.3 to 6, 14b's rows to 10, rows 42→43, 420→421, AC-T16.3 to 423/425, and AC-T14d.4. The design PS list and line 89 move too.
    - (b) State in D21 and the plan that this guard is deliberately unrowed, with the reason. I have no reason to offer that holds.
  - instance of: guards that a v1.15 move split from the marker that used to cover them. The other moved element (the clause check) kept its marker, so this is the only member.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › `The write sits in its own `if [ "${#scope_arg[@]}" -gt 0 ]; then … fi` block, immediately after `stem=` is computed`

- **WIRE-PIN 2's dispatch count names a source that does not exist under the real collection script.**
  - The plan says to read "each `--pass` spec's log in the collection call, read as `test_pass_roots_give_each_pass_its_own_cd` reads it". That test reads the argv from the stub's `cycle_calls.jsonl` (`case["cycle"]`). WIRE-PIN 2 runs the real `h_mad_audit_cycle.py`, which records no argv. Its stdout carries no log paths either (I printed it).
  - Measured in the edited copy: the test's own stem dir holds `<stem>_p1.log`, `_p2.log` and `_p3.log`, with init-event counts `[1, 1, 1]` and `dispatch_count` = 6.
  - Repair, either one:
    - (a) Read `sorted(stem_dir.glob("*_p[0-9].log"))` in the test's own stem dir, require 3 files, and count `event == "init"` rows in each. Measured; this agrees with design 586, "taken from the pass logs".
    - (b) Wrap with `traced_bindir` to capture the collection argv. Unverified.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `one `init` event** (each `--pass` spec's log in the collection call, read as`

- **AC-T14d.5 says "The slowest members are reported with `--durations=3`", but Task 14d's command block runs both modules as `-x -q -p no:cacheprovider` with no `--durations`.** The gate's own commands cannot produce the figure the AC asks to be reported. Fix: append `--durations=3` to the two module commands.
  class: measurement
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `are reported with `--durations=3`; the two real-cycle ids are expected near 6.9 s each`

## Nit
- Design header (line 7) and changelog: v1.15 "takes spec v1.20 (`d78cca8d`) and the v1.21 texts in flight". Spec v1.21 was committed at `061bde85`, before `741f35f4` (`git log` order: `1accd5a9`, `741f35f4`, `061bde85`). Cite `061bde85`.
- Round-2 nit, partly open. Over the design, `grep -c` gives 0 matching lines for each of these plan-added contract items:
  - `ASSEMBLER-READ-SHA`, `ASSEMBLER-READ-DIRTY` and `ASSEMBLER-READ-ENV`;
  - "raises on load";
  - "40 lowercase hex".

  The v1.10 changelog answers only the row-24 half.
- `test_assembler_check_assemble_halt_cycle_beside_good_v2_is_pinned` says the `s2-d1-v1` "cycle directory" holds "its `*.here.txt` and clause-carrying prompts". Cycle directories are `--stems` entries. `assembler-check` reads prompts only from `--reading` (`s2/d*/v*/p*.prompt.txt`, design 578). Say "and clause-carrying `--reading` prompts under `s2/d1/v1/` and `s2/d1/v2/`".
- The design's PS15 (868) and Test Plan name the target `test_calibration_cycle_records_its_here` unparametrized. The plan's PS15 target is `[assemble_halt]`. This is harmless, but the design could name the id.
