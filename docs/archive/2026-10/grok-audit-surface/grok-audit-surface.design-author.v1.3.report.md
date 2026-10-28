DESIGN-AUTHOR: DONE version=v1.3 path=docs/02-design/features/grok-audit-surface.design.md lines=713 sha256=7f2268db56c0dcf4f22f6064d7a0a95f999ecb9ca9766bf6e5595ad32d848c2f

# grok-audit-surface design v1.3: round-cap corrective revision (not re-audited)

## Brief vs tree
- The brief says cycle 2 p1 has "6 must, 3 should" and lists 9 items. That does not match the report. Running `h_mad_audit_gate.classify` on `design.audit.v2.p1.md` gives `must_count=9 should_count=3`. Your items 7–9 (agy attribution, mutation rows, Readings command) are the report's musts 7–9. The report's three should-fixes (`--sources` on every mode, runbook `mkdir`, refreshing the plan comparisons) were not in your list. I answered all 12, and each one is mechanically checkable.
- Nothing needed a spec or plan change. No OPEN-DECISION was written.

## Per finding: the change, then the check
1. **AC-1.1 (must).** D11 step 3 now requires the grok `p1` Effort item to be either the positive grok item (`^p1 tools=\d+ ok=\d+ unresolved=\d+ thinking=\d+ format=grok( |$)`) or the truncated item. Any other rendering refuses with `input_unparseable:<grok/auditcycle.txt>`: unreadable (`missing`/`empty`), `codex-text`, `parsed`, `unparseable`. The M3 row and the `truncated` bullet were updated to match. New smoke tests: `test_smoke_effort_{codex_text,unreadable,agy_shape,unparseable_shape}_item_is_unparseable`. Positive controls: `test_smoke_pass` and `test_smoke_effort_grok_item_with_targets_is_grok`. Renderer pin: `test_grok_item_predicate_matches_the_renderer`.
   - Check: `grep -c 'format=grok( |$)'` on the design. Readings script T5 was run and every shape's match/no-match was as claimed.
2. **AC-2.6 (must).** New `build-root --reset <abs root>` (D2 row and D5 "Resetting the S1 root between its cycles"). It rebuilds the expected tree, removes every path that is not in the build (so the by-products are never enumerated), rewrites any placed file that changed, re-walks and asserts equality, then reruns D6 and D7 on the live root. It prints `RESET:` and then the same `ROOT: READY`. It adds no new refusal trigger; a re-walk mismatch prints `internal:RootResetMismatch`. The runbook runs it after each S1 `record-cycle` and before the next dispatch.
   - Tests: `test_build_root_reset_removes_by_products_and_restores_placed_files`, `test_build_root_reset_rescans_after_removal`, `test_build_root_reset_runs_the_reach_check`.
3. **AC-2.7 (must).** D3: a file with one of the six names is outside the set only if its normalised content contains none of (a) a `seeded` span, (b) an `expected` sentence, (c) a finding text from `report_findings` over every collected report in the tree.
   - Opposed fixtures: `test_calibration_data_set_keeps_an_excluded_name_carrying_{a_finding_text,a_seeded_span,an_expected_sentence}`, plus the end-to-end `test_main_leak_trigger_i_on_an_excluded_name_carrying_a_finding_text`.
   - Check: `grep -c 'catch-all still reaches the six'` returns 0.
4. **AC-4.5 (must).** Should findings are always written. A count difference now prints the published line `SHOULD-COUNT:`, which D15 carries; nothing is dropped. `SHOULD-SKIPPED` and its test are gone.
   - New test: `test_should_findings_are_written_on_a_count_difference`.
   - Check: `grep -c SHOULD-SKIPPED` returns 0.
5. **AC-8.3 (must).** D14 adds the PASS-only sentence that cites both headings. `test_never_gate_section_names_grok_falsification` now pins the sentence verbatim, and checks that each cited title is a SKILL.md heading.
   - Verified: `grep -cxF '## Verifying a review finding before acting on it' h-mad/SKILL.md` returns 1, and the `### Record a rejected finding…` heading returns 1.
6. **D12 (must).** `report_findings` makes the same calls the gate's `_section_detail` makes (verified in `h-mad/scripts/h_mad_audit_gate.py`): `_bullet_groups`, then `_collapses(group, set())` → one finding, else `len(_flat_findings(group["lines"]))` findings, with the all-`None` and fail-safe rules. D1's import list gains `BLOCKING_SECTIONS`, `_collapses`, `_flat_findings` and `_bullet_remainder`. The false "scratch probe found no disagreement" claim is removed.
   - Parity fixtures: `test_extract_parity_{nested_label_group,real_parent_none_child_real_child,collapsing_group,prose_only}`.
   - New mutation rows: X3/X4 on `# M:GAS-COLLAPSE-WIRE`.
   - Script T4 was run: v1.2 walk / new walk / classify = 1/3/3, 1/2/2, 1/1/1, 0/1/1, 0/0/0.
   - Residual stated: the section split is the probe's own code, because `classify_detail` keeps it inline.
7. **agy attribution (must).** I read `agy_from_cli_logs`: it takes the newest log by mtime and only compares it with the second-newest. The runbook now picks only the `cli-*.log` files that are new since a listing taken before the cycle and that contain `workspaceDirs=[$ROOT]`. With exactly one such file it runs `--agy-log-dir` on a copy of it; otherwise it writes `RESOLVED-MODEL: UNKNOWN`.
   - Measured: agy logs are named `cli-<ts>.log` and carry `workspaceDirs=[…]` (over interactive runs only).
   - Check: `grep -c 'running it right after'` returns 0.
8. **Mutation rows (must).**
   - C4: C1's find replaced by `if True:`, targeting `test_union_three_passes_all_clean_pass`.
   - W9/W10: W4's and W5's find/replace, targeting `test_codex_agy_cycle_stamps_carry_the_legs_that_ran`.
   - Verified: `grep -cF '    legs=("${_surf[@]}")' h-mad/scripts/hmad-dispatch.sh` returns 1, and `grep -cF '        if result.verdict == "FAIL":' h-mad/scripts/h_mad_audit_cycle.py` returns 1. `git diff --quiet 94a4fd2c 2e8593b4 -- h-mad docs/archive` exits 0.
9. **Readings command (must).** Readings now holds runnable throwaway scripts: T1 (three-surface stamps via `run_audit_cycle`), T2 (`run_with_cmd_exec_stub`), T3 (ls-remote exit codes), T4, T5. I extracted the block from the document and ran it: 2 passed in 19.65 s, with outputs matching the rows (`delivered=out,out,none`, 2 stamps with legs agy/codex/grok; `delivered=report-file×3`, 0 stamps; exit codes 2/128/128). The rows are re-stamped `2e8593b4`.
10. **Should-fix: `--sources`.** D1 and D2 now accept it on `check-ledger`, `build-root`, `extract`, `score`, `rescore` and `main-leak`, and each passes it to its in-process calls. New test: `test_sources_override_reaches_every_ledger_mode`.
11. **Should-fix: mkdir.** Added a D8 Setup bullet (`mkdir -p` for stem, data/s1 and data/s2). `STEM` is now created before the `tee`. `record-cycle` creates `--dest` with its parents.
12. **Should-fix: plan comparisons.** The Overview now cites spec v1.7 and plan v1.5 at `28ec5bfc`. D5 quotes plan v1.5's fresh-root rows. The R13 paragraph now quotes plan v1.5's agreement (checked verbatim with `grep -o`).
   - Check: `grep -c 'contradicts the brief'` returns 0.

## Sweeps (whole document, fences included)
- Each of these returns 0: `extract_findings`, `SHOULD-SKIPPED`, `should_walk_mismatch`, `scratch pytest`, `scratch probe at`, `running it right after`, `contradicts the brief`, `9 calibration roots`, `Each of the six carries`, `catch-all still reaches the six`, `targets:`.
- The remaining `plan v1.3` / `spec v1.6` hits are deliberate history (the Overview's provenance, the R13 note and the Version History).
- `At 94a4fd2c that cycle prints` was changed to `2e8593b4` to match the row.

## Precheck and version history
- `PRECHECK: PASS issues=0`.
- Advisories I am keeping on purpose:
  - PATH advisories: these are files the feature will create.
  - COUNT L110 and L312: already there in v1.2, and the text is unchanged.
  - STALESHA L573: a `94a4fd2c` row; `h-mad` has not changed since then.
  - COUNT L712: the v1.2 Version History line, which is history and is not edited.
- `VERSION-HISTORY: OK version=v1.3 line=713`. The text begins "Corrective revision after the two-round cap (not re-audited)".
- All probes were deleted. `git status` shows only the design. Nothing is committed.

## New, for Phase 5 (not fixed here)
- **S1, agy logging.** Check whether `hmad-dispatch`'s `exec agy` leg logs the export root as `workspaceDirs=[…]`, in the spelling `ROOT: READY` prints (`/var` vs `/private/var`). If it does not, agy is always `UNKNOWN`. This fails safe, but it loses the AC-3.6 model.
- **Spec gap.** A non-grok Effort shape on the grok pass gives `SMOKE: UNREADABLE`. AC-1.7's remedy ("restore the input and derive again") cannot clear that, so only a new smoke can. The spec may want to say so; it is spec-owned, so I did not change it.
- **Impl-plan owes:**
  - the probe-side marker `# M:GAS-COLLAPSE-WIRE` (rows X3/X4);
  - the per-alternative P-rows for the new step-3 refusals and the reset tests;
  - a re-derivation of the marker and row counts at Phase 5e.

## Owed by other documents
- None required. The plan and spec already agree with the design on fresh roots and R13.
