IMPLPLAN-AUTHOR: DONE version=v1.2 tasks=18 wiring=1 mutation_rows=169 path=/Users/kimhawk/orca/skills/docs/01-plan/features/grok-audit-surface.impl-plan.md lines=1613 sha256=4b8400ba95e5e2a6dd2c1fb81085dd73cb959b5205972e56d233ef48a2176702

## Ownership check before writing
The document's sha256 was 5490674354dbfab24c79344f7b94c05f769b30ce128e0fa273ffd51ba0383d73 and its newest Version History entry was `- v1.1`, so nobody else had written it. I bumped the version with `h_mad_version_history.py --version v1.2`, which printed `VERSION-HISTORY: OK … line=1612 placement=append`.

## Gates on the final file
- `PRECHECK: PASS issues=0`. Advisories kept:
  - L1326 "17 rows" and L1432 "0 files", as before.
  - The v1.0 and v1.1 dated Version History entries, whose figures are the historical record.
- `ACS: OK count=51 frs=10` (h_mad_ac_census.py on the spec with the impl-plan paired; the impl-plan makes no "All N ACs" claim).
- `WIREPIN: PASS tasks=18 wiring=1 unpinned=0 mislabeled=0`, with a scratch registry deleted afterwards.

## Probes
All probes ran in the session scratchpad: argparse on 3.11.8 and 3.15.0, `O_NOFOLLOW`, `Fraction`, stale bytecode, and `crash_kill`. I deleted them afterwards and confirmed the probe directory is gone.

## Per finding

**A-M1 (agy must): top-level parser and the Namespace lost on error.** Premise HOLDS.
- Probe, same result on 3.11.8 and 3.15.0:
  - A plain top-level parser given `smoke --data x --no-such-flag` exits `SystemExit(2)` with no token.
  - With a `_TokenArgumentParser` top level, `UsageError` is raised.
  - A `UsageError` raised inside `parse_args` returns no Namespace.
- Fix, Task 2:
  - Every parser is a `_TokenArgumentParser`, the top-level one included.
  - `refusal_token(mode, exc, argv)` reads `--data` from the raw argv, never from a Namespace.

**C-M1 (codex must): `--help` exits through `SystemExit(0)`.** Premise HOLDS.
- Probe: `smoke --help` printed help on stdout (147 B). argparse has 4 `.exit(` sites on both interpreters; the only `sys.exit` is in `ArgumentParser.exit`, whose callers are `error()`, the help action and the version action.
- Class closed in Task 2 for every argparse exit path (error, help, version, abbreviation): `add_help=False` (`# M:GAS-NO-HELP`), `allow_abbrev=False` (`# M:GAS-NO-ABBREV`), no version action, and `error()` overridden. That makes `ArgumentParser.exit` unreachable.
- Probe: with abbreviations allowed, `check-ledger --tre t` parsed as `--tree t`; with `allow_abbrev=False` it raises `UsageError`.
- New tests:
  - `test_help_flag_prints_the_mode_token` (9 ids)
  - `test_abbreviated_flag_is_a_usage_error` (1 id)
- New rows: `p-no-help`, `p-no-abbrev`.
- Residual stated: a future argparse that adds another `exit` caller is not covered.

**C-M2 (codex must): static symlink fixtures cannot kill the write and parent mutants.** Premise HOLDS.
- The v1.1 text itself says `remove_absent` unlinks every link "whether or not its path is in the expected tree", so no link is left by the time `restore_expected` runs.
- Probe: an `O_NOFOLLOW` open of a link fails with `ELOOP`; an `O_NOFOLLOW` open through a linked parent directory still wrote the outside file. So the ancestor check is a separate guard.
- Fix, Task 5:
  - The write and parent tests are renamed `test_restore_expected_does_not_write_through_a_symlinked_placed_document` and `test_restore_expected_does_not_write_through_a_symlinked_parent_directory`. They call `restore_expected` in process, at its own boundary, with the link present at that moment.
  - The delete-through test stays end to end.
  - The `ELOOP` path is stated: unlink the link, then create with `O_CREAT | O_EXCL | O_NOFOLLOW`.
  - The concurrent-writer (TOCTOU) residual is stated.
- Counts unchanged: 15 tests, 13 rows.

**C-M3 (codex must): suppressing stderr blinds the zero-crash gate.** Premise HOLDS.
- Probe of the real `crash_kill`: a surfaced traceback framed in the probe gave `KeyError`; the same failure with the traceback suppressed gave `None`.
- Fix, a Rules section bullet:
  - The probe prints a traceback only for exceptions outside the `ProbeRefusal` base (`# M:GAS-TRACEBACK-SCOPE`).
  - Subprocess assertions pass `r.stderr` as their message.
  - Tests that inject an exception on purpose, or assert on stderr's content, assert on locals and never echo stderr.
  - `test_usage_error_prints_the_mode_token` now asserts zero `Traceback` occurrences.
- New row: `p-traceback-scope`.

**C-M4 (codex must): the probe sits outside the harness's bytecode-purge root.** Premise HOLDS.
- `_purge_bytecode` iterates `root.rglob("__pycache__")` under the spec root, which is `h-mad/`; the probe is under `docs/`.
- Probe: a module loaded with `spec_from_file_location`, then changed from `VALUE = 1` to `VALUE = 2` at the same size with its mtime restored, still loaded `VALUE 1`.
- Fix, a Rules section bullet: in-process loads go through `grokauditfixtures.load_probe`, which compiles the source text into a fresh module, so no `.pyc` is read or written. `grokauditfixtures.py` is now created in Task 2 and extended from Task 3 on.

**C-M5 (codex must): AC-T6.1 contradicts the post-write `ref_unconfirmed` fixture.** Premise HOLDS.
- The v1.1 fixture replaces only the read after a successful `update-ref`, so the real ref has moved, while AC-T6.1 required the pre-test value.
- Fix, AC-T6.1 split:
  - Pre-write refusals assert the ref is unchanged.
  - `ref_unconfirmed` asserts the ref's actual value (no rollback, per D9).
  - Residual stated, with the operator's next step.

**C-M6 (codex must): the off-PASS regression test is never observed failing.** Premise HOLDS.
- In v1.1 the test is P at RED and no row targets it.
- Fix, Task 16, on MISS or INCONCLUSIVE only:
  - Row K4: K3's find line rewritten to `--surfaces codex,agy,grok`.
  - Row K5: `that is three reports, of which two share a model family` changed to `… share a vendor`. That find is 1 matching line, line 2024 at `30917a1a`.
  - New AC-T16.4.
- Totals become 171 on MISS or INCONCLUSIVE.

**C-S1 (codex should): the `Fraction`-to-string mutant breaks the type rule.** Premise HOLDS.
- Fix: the row now keeps every value a `Fraction` and shifts the denominator by one (`n` to `n + 1`). Measured: `Fraction(1, 5) < Fraction(2, 9)`.
- Residual stated: `Fraction(2, 8)` normalises to `1/4`, so no `Fraction`-preserving mutant can test representation alone.

**A-S2 (agy should): `extract_all` takes two arguments in one place and three in another.** Premise HOLDS.
- In v1.1 the Task 8 Description says `extract_all(tree, s2_dir)` while its Code structure has three parameters.
- Fix:
  - The Task 8 Description now gives the three-argument form, with the D1 reason.
  - Task 9's call site is spelled out: `extract_all(tree, tree / "docs/03-analysis/probes/grok-audit-surface/calibration/s2", sources)`.
- OWED-ELSEWHERE: the design's D12 signature.

**A-S1 (agy should): Task 17 RED/GREEN counts off by one.** REJECTED.
- Evidence: `grep -c "Expected pytest result" <impl-plan v1.1>` printed 0, and `grep -c "test_grok_runtime_documents_audit_surface_s1" <impl-plan v1.1>` printed 0.
- None of the strings quoted from my document exist in it. Carry item 8 is a measurement acknowledgement and adds no test. Task 17's RED split is "4 nodes; 4 F, 0 P", counted over its own four new tests, not over `test_grok_fallback_docs.py`.
- For the rejections ledger.

## Totals
- 169 rows at S0: T2 3 → 6, all others unchanged. 141 are P-rows and 28 are named rows.
- 171 rows on MISS or INCONCLUSIVE (adds K4 and K5).
- 115 marker sites.
- Task 2 RED: 30 nodes, all failing (9 + 9 + 2 + 9 + 1).
- Updated by a value sweep: the Executive Summary, AC-T14.2 (`0/169`), AC-T14.4 ("115 and 169"), AC-T16.3 (169 or 171 by branch), and carry-table rows 2 and 12.
- Parsed from the document: 171 table rows (169 + 2 conditional) and 115 distinct markers.

## OWED-ELSEWHERE
- Design D1: a traceback is printed only for exceptions outside the declared refusal classes. The reset guard classes and `UsageError` still print `internal:<E>` through the last resort, but without a traceback.
- Design D12: `extract_all` takes `sources` as a third argument.
- Design D2 and spec AC-5.1/5.4, carried from v1.1: the `PROBE:` prefix with `reason=unknown_mode`.
- Design Test Plan: the plan-added tests `test_help_flag_prints_the_mode_token`, `test_abbreviated_flag_is_a_usage_error` and the two `test_restore_expected_*` tests, which replace two v1.1 plan-added names, plus rows K4 and K5.

## OPEN-DECISION
None new; carry item 1 is still on Task 5.

## Tree
The only new untracked file is the impl-plan. The audit reports and their `.effort.json` files were already there, written by the orchestrator.
