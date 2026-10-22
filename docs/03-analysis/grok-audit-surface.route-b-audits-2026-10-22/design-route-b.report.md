DESIGN-AUTHOR: DONE version=v1.16 path=docs/02-design/features/grok-audit-surface.design.md lines=1112 sha256=47dc7027342eff9b5d42f5728fe3214499d8ee02cf1ce8b74a56bfb05a0100ce

# Design v1.16: round-3 audit, should-fix 1, repair (a), plus the design-touching items
- Not committed. HEAD is `1accd5a9`. Before editing, the file on disk was my v1.15 (`8f228930…`).
- PRECHECK: PASS, 0 issues. VERSION-HISTORY: OK, v1.16.

## Changes
- The here-write guard is now marked `# M:PATH-SCOPE-HERE-ARMED`.
- New row PS16 `path-scope-here-always`: the guard's condition becomes `true`. Its target is the production GUARD `test_audit_cycle_without_pass_roots_does_not_pass_the_switch`, through the GUARD's here-half ("no `*.here.txt`"), checked in the test's own stem dir. PS14 cannot reach that half, because the record has its own guard.
- Row counts: the enumerating sentence now reads 16 rows, PS1–PS16, with PS5, PS14 and PS16 sharing one target. Derived with awk: 16 distinct PS labels.
- Test (3) now reads `sorted(stem_dir.glob("*_p[0-9].log"))` in its own stem dir, requires exactly 3 files, and requires exactly one `event == "init"` row in each.
- The `assemble_halt` case of `test_calibration_cycle_records_its_here` now asserts `auditcycle_lines(result.stdout) == ["AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2 passes=3 size_status=verified"]`.
- The rule is stated: assert on the last stdout line only for a token the wrapper prints last, such as `REQUIRE: STOP`. `auditcycle_lines` exists at `h-mad/tests/test_hmad_dispatch_audit_cycle.py`, checked by grep.
- All edits were exact-once Python replacements, each asserted `count == 1`.
- A sweep for `15 rows`, `PS1–PS15` and `PS14 and PS15` found no other enumerating site.

## Owed elsewhere
- **Impl-plan**, the moves the audit's repair (a) lists: AC-T14b.3, 14b's row count, the row totals, AC-T16.3 and AC-T14d.4.
- The design-side "line 89" the audit mentions is blank in the design, so that reference is to the impl-plan.
