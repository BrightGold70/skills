IMPLPLAN-AUTHOR: DONE version=v1.11 tasks=35 wiring=4 mutation_rows=43 path=docs/01-plan/features/grok-audit-surface.impl-plan.md lines=4221 sha256=a99c05ccada81b4737d9f930b45ae8af0bb4c261898911f1795f93e25d6b6c12

# Impl-plan v1.11: round-3 audit (1 must, 3 should, nits) and design v1.16 (5767086f)

Only the impl-plan is edited; nothing is committed.

Ownership check before the first write: sha256 23089c40…, newest Version History line v1.10. That is my v1.10, which was committed at 1accd5a9.

## Findings applied

**Must.** `test_calibration_cycle_records_its_here[assemble_halt]` now asserts its cycle line through the helper, not as the last stdout line:
`auditcycle_lines(result.stdout) == ["AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2 passes=3 size_status=verified"]`.
- The plan now states the rule: "last stdout line" is used only for a token the wrapper itself prints last, such as `REQUIRE: STOP`.
- The audit's sweep found that this test was the only place that broke the rule.

**Should 1: the here guard gets a marker and a row.**
- Edit 5's guard now carries `# M:PATH-SCOPE-HERE-ARMED`.
- New row PS16 `path-scope-here-always`: the condition becomes `true`, and the row targets the production GUARD.
- The GUARD's text and its RED split now name PS16 as a negative observation, alongside PS5 and PS14.

**Should 2: WIRE-PIN 2's dispatch count.** It now reads `sorted(stem_dir.glob("*_p[0-9].log"))` in its own stem dir. That must be exactly 3 files, each with exactly one `init` row, which matches design v1.16 and the audit's measured `[1, 1, 1]`.

**Should 3: timing figures.** Task 14d's two module runs now carry `--durations=3`.

**Nits.**
- Applied: the assemble_halt-beside-v2 fixture now separates its `--stems` cycle directory from its `--reading` prompts under `s2/d1/v1/` and `s2/d1/v2/`.
- Not applied, because they concern the design rather than this plan:
  - the design's spec-sha citation;
  - the design's naming of the `READ-*` markers;
  - the PS15 target id.

## Counts (derived by command over the document)

- Rows by Task: 14a 6, 14b 10, 14c 27, so 43 in total.
- Running total: 378 + 43 = 421 after Task 14c (AC-T14d.2/.4), then 423 or 425 after Task 16 (AC-T16.3, Executive Summary).
- Path-scope mutation rows PS1–PS16: 16.
- Distinct wrapper `# M:PATH-SCOPE-` markers in Task 14b: 6.
  - They are CHECK, CHECK-ARMED, HALT-FILE, HERE, HERE-ARMED and SWITCH.
  - AC-T14b.3 now expects 6, and the Executive Summary says 6.
- Node ids are unchanged: path-scope 21, assembler-pin 33.

## Contradictions found

None.

## Placeholder scan

`PRECHECK: PASS issues=0`.
