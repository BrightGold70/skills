## Summary
The implementation plan still targets the superseded DD-7 Claude-gate design and contains a Task 1 helper that fails when called as written. Its discrimination and Python 3.9 checks also leave stated requirements unverified.
Evidence: 9 files opened, 5 greps run. 🌱 graft saved ~56,071 tokens (~$0.03) this turn, 1 call.

## Must-fix
- Rebase Task 8 on design v1.3, including RAW_TARGET, the root-relative directory-exemption subject, the three root shapes, and the 126-cell differential — the current Task 8 halt is obsolete, while its literal hook logic and 42-cell test/probe would implement and approve the known extra softening under roots below tests/ or fixtures/.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.impl-plan.md › `HALT: `design delta owed`. Task 8 does not start until the`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `DIR_SUBJECT="/${TARGET_PATH#"$R"/}"`
- Add `import os` to the stated first contents of the new `tdd_gate_support.py` — `hermetic_env()` reads `os.environ`, so Task 1's supposedly passing RED support test and every subprocess test using the helper raise NameError if the literal is followed.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.impl-plan.md › `env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE") and k not in DROPPED_ENV}  # M:E1`
- Demonstrate a failing observation for every initially green guard retained as coverage, or remove its coverage claim — the plan expressly leaves the quoted-assert, doubled-path, six `-c` cells, and two shell controls without a killing run; a stated residual does not satisfy the binding test-discrimination invariant.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.impl-plan.md › `none of this feature: the pre-existing trusted-directory and scripts-root rules, which no committed spec anchors`

## Should-fix
- Run an actual import of the judge and its imported modules under `/usr/bin/python3` in the floor test — `ast.parse` checks syntax only, while the plan's own Python 3.9 contract requires successful import.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.impl-plan.md › `ast.parse(source, feature_version=(3, 9))`

## Nit
None
