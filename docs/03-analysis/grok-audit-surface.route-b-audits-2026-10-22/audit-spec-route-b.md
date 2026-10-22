## Summary
GATING delta review of `docs/01-plan/features/grok-audit-surface.spec.md`, v1.17 to v1.19 (`git diff 9055c8a7 d9f25dc2`). The spec is byte-unchanged from d9f25dc2 to HEAD 7e1c48e3 (`git diff --stat` printed nothing). The three rulings are encoded, and almost every tree claim the delta makes holds when re-run: the 0-commit assembler/template ranges, the `$here` resolution, the `~/.claude/skills/h-mad` symlink, the `<root>/.hmad-report/` report path, `prepend_output_contract`'s slice, the stdlib-only imports, the ruling's provenance at 242c26bd, the AC-5.4 count of sixteen, the AC-6.6 three exempt classes, no SEEDSCORE result line and no measurement doc, and test (2)'s guard half holding on today's assembler. One blocking gap remains. The closed "Delivery by outcome" section was not extended for the two new non-scoring outcomes (an unpinned or no-clause assembler, and the path-scope fail-closed halt), and it does not list AC-3.9 among the work that ships on every outcome.
Evidence: 8 files opened, 27 greps run.

Files opened: the spec (diff plus §FR-3, AC-3.2, AC-3.6, AC-3.8, AC-5.4, AC-6.1, AC-6.2, AC-6.6, Delivery, NFR, Out-of-Scope, Assumptions); design D21 (lines 553–600); the incident record (lines 34–140); `h-mad/scripts/h_mad_assemble_audit.py` (lines 23–39, 188–262, 450–500, 600–680); `h-mad/scripts/hmad-dispatch.sh` (lines 3559–3576, 3610–3646, 3700–3800); `h-mad/audit-prompt.template.md` (lines 1–15); `h-mad/invariants.base.md` (grep only); the archived d1 plan on the calibration ref (git grep only). I also ran one live assembly into a scratch root.

## Must-fix
- **Delivery by outcome is a closed set that the v1.17–v1.18 outcomes broke** (spec line 478, then the table and the "There is no other outcome." line under it).
  - AC-3.6 (line 192) adds a run that is "not scored": `assembler=unpinned`, or a commit without the clause.
  - AC-3.9 "Fail closed" (line 206) adds a calibration cycle that is "never scored" (design D21 implements it as `REQUIRE: STOP reason=path_scope_missing:p<i>`).
  - Neither outcome has a row in the table, and neither token appears in the precedence order "first the AC-1.7 `SMOKE:` line, then … `SEEDSCORE:`; a containment halt … comes before both".
  - The paragraph lists what ships on every outcome (the S0 set, and "FR-11 (v1.9) also ships on every outcome"), but it does not list the AC-3.9 assembler switch, the wrapper check or their tests. The AC-1.9 re-smoke cannot run without them.
  - Evidence: `grep -o 'AC-3\.9'` over the spec matches lines 113, 184, 192, 196, 201, 283, 495, 510, 532, 533 and 534 (11 distinct lines), and never line 478 or the table. The only `unpinned` matches are lines 192 and 533.
  - What the spec leaves unsaid: for a run whose `SMOKE:` reads FAIL (or PASS) under an UNPINNED or NO_CLAUSE assembler, does the AC-1.8 grok-runtime sentence and SKILL.md failure clause ship? AC-3.6 says "Neither run is a reading", yet it also says the doc "publishes … `assembler=unpinned`". That implies a measurement doc exists for an unpinned run, and the table never says which one.
  - An implementer writing the runbook gate and the delivery tests (AC-7.4 style: "A test, or the measurement doc's verdict line, is the evidence the branch was taken") has no specified branch for these outcomes.
  - Fix:
    - (a) Add a row "Assembler not pinned or no clause (AC-3.6, AC-3.9 fail closed)" reading: not published as a reading; recorded as an incident on `main`; grok-runtime, SKILL.md and routing not shipped. This mirrors the containment-halt row.
    - (b) Put the assembler token, which design D21 names `ASSEMBLER:` via `require --verb assembler`, into the precedence sentence next to the containment halt, read before `SMOKE:`.
    - (c) Add "AC-3.9 (v1.17) also ships on every outcome, before the AC-1.9 re-smoke".
    - (d) State whether the measurement doc's `assembler=unpinned` form can appear at all. If it can, say in which outcome row. If it cannot, AC-3.6's "published as `assembler=unpinned`" means published in the incident record.
    - Alternative to (a)+(b): fold both into the existing containment-halt row, renamed "Halt or unpinned run". Either repair works.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `There is no other outcome. A smoke failure is not retried as a pass (AC-1.1).`

## Should-fix
- **"Exactly the clause added and no other byte changed" vs the design's inserted separator** (AC-3.9, line 205; test (5), line 218).
  - Design D21 inserts `PATH_SCOPE_CLAUSE + "\n\n"`, and its test (5) removes `STUB_PATH_SCOPE_CLAUSE + "\n\n"`. The spec's test (5) removes "the clause's bytes" only.
  - Read literally, the spec's test (5) leaves two extra newlines and fails against the design. The spec also says the clause has no defined line terminator, yet the wrapper check relies on a whole line (`grep -cxF`), so some separator bytes are unavoidable.
  - Fix: define "the clause's bytes" as the clause text plus the separator the design names (the exact inserted bytes). Or say "removing the inserted bytes the design names".
  - Evidence: design line 563 (`inserts \`PATH_SCOPE_CLAUSE + "\n\n"\``) and the design's test (5) bullet.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `the prompt is the switch-off prompt with exactly the clause added and no other byte changed`

- **Test (4)'s inputs omit `invariants.base.md`, and the "imports only the standard library" hint implies a bare script is a sufficient reference.**
  - `h_mad_assemble_audit.py:468` reads `_read(SKILL_DIR / "invariants.base.md", required=True)`, with `SKILL_DIR = Path(__file__).resolve().parent.parent` (line 33).
  - A reference script materialised alone by `git show <sha>:…` therefore raises FileNotFoundError, unless it sits at `<x>/scripts/` with `<x>/invariants.base.md` beside its parent.
  - The spec's input list "(feature, phase, cycle, project root, report file, template and `--vh-tail`)" does not name base invariants. It also says the reference "comes from that commit's files", while design D21 copies the CURRENT `h-mad/invariants.base.md` into both assemblies. Those are two different reference definitions.
  - Measured: the file has 0 commits in a489031f..7e1c48e3, so today they agree.
  - Fix: add "base invariants (`h-mad/invariants.base.md`, read relative to the script's parent directory)" to the input list. Then either state that both assemblies read the same current copy, as the design does, or require the pinned sha's copy. Say which; both repairs are coherent.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `For the same inputs (feature, phase, cycle, project root, report file, template and `--vh-tail`)`

- **AC-6.2 retires "unmeasured" in production SKILL.md on a measurement taken with a clause production grok legs never receive.**
  - AC-3.9 residual (3), line 223, says "it is not measured whether a production grok leg without the clause behaves the same." The only route for that delta is the measurement doc (FR-6, line 283).
  - AC-6.1 (line 285, transfer residual) and AC-6.2 (line 286, the SKILL.md replacement text and its doc test) never mention it. `grep -o 'AC-3\.9'` matches neither line.
  - The operator ruling requires the doc to state the delta (it does). Whether the SKILL.md site that consumes the number carries it is an encoding gap, not a re-litigation.
  - Fix, either of:
    - (a) AC-6.1's transfer residual also names the AC-3.9 prompt delta.
    - (b) AC-6.2's replacement text carries one clause, "measured with the calibration-only path-scope clause (AC-3.9)", pinned by the AC-6.2 doc test.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `It is replaced by the measured fractions and a pointer to the measurement doc.`

- **AC-3.6 still says enforcement is "owed to the design" at v1.19, after design v1.13 discharged it.**
  - Design v1.13 (8a27d264, which precedes d9f25dc2) chose a runbook gate: `assembler-check` → `require --verb assembler`, "DECISION (design-author): a runbook gate, not a probe check".
  - v1.19 adopted D21's reason list but left the conditional "If the design chooses a probe check, it needs a new AC-5.4 reason … Until then, those three stay as they are" unresolved.
  - The spec also never names the `ASSEMBLER: NO_CLAUSE` outcome that D21 adds for "a run whose assembler commit does not carry the AC-3.9 clause".
  - Fix: replace the paragraph with "Enforced by the runbook gate design D21 names (`ASSEMBLER: PINNED` only is `REQUIRE: OK`); no AC-5.4 reason is added, so the sixteen forms, the AC-5.5 fixtures and the `list_changed` (c) keys are unchanged", and cite D21's NO_CLAUSE token.
  class: measurement
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `**Enforcement is owed to the design.** At v1.17 no verdict rule and no AC-5.4 reason reads this record.`

- **AC-3.9 *Why* over-claims that the `find` targeted paths the d1 plan names.**
  - The incident record (lines 71–72) shows `find /Users/kimhawk/orca /Users/kimhawk/.local/state/h-mad …`.
  - The d1 plan names only `/Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy` and `/Users/kimhawk/orca/skills`. On the calibration ref, `git grep` matched the `.plan.md` at lines 183–184.
  - `local/state` occurs in none of the prompt sources: `git grep` over the d1 archive dir, `invariants.base.md`, the template and `.h-mad/invariants.md` printed nothing.
  - So only the `ls -d` is document-triggered. The `~/.local/state/h-mad` search was grok's own initiative, which clause (i) does not address and only clause (iii) does. That bears on how residual (1) ("an agent can ignore the clause") should be expected to fire.
  - Fix: "grok ran `ls -d` on the absolute paths the seeded d1 plan names … and a `find` over their ancestor `/Users/kimhawk/orca` and over `~/.local/state/h-mad`, which no prompt source names".
  class: measurement
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `grok had run `ls -d` and `find` on absolute paths that the seeded d1 plan itself names in its Convention Prerequisites`

## Nit
- AC-3.9 "The requirement" (line 202) still offers placing the clause "in the default template `h-mad/audit-prompt.template.md`". After v1.18, a template line reaches switch-off prompts, and a conditional template slot changes switch-off bytes, so test (4) rules that option out (design D21 says so). Drop the template option, or qualify it ("only if switch-off bytes stay identical").
- AC-3.9 "Scope" (line 203): "`$here` is the script's own resolved directory unless `HMAD_AUDIT_CYCLE_SCRIPT_DIR` is set". The wrapper uses `${HMAD_AUDIT_CYCLE_SCRIPT_DIR:-…}` (`hmad-dispatch.sh:3567`), so a set-but-empty value falls back to the default. Write "set and non-empty". AC-3.6 deliberately treats any set value as unpinned, which is stricter and fails closed.
- AC-3.6 (line 192): "when the run's first dispatch (the AC-1.9 re-smoke) starts". Per the incident record's run-2 table, the tracer pair and the canary dispatch before the re-smoke. Write "when the first re-smoke cycle starts", as design D21 does: "before the versions and the first re-smoke cycle". The spec is also silent on where the end reading goes on a smoke failure, where there is no S2. D21 covers it ("the end reading follows the last re-smoke cycle instead").
- AC-3.9 "Tests" lead-in: test (6) is "recorded RED against the assembler without the clause and switch". Test (6) drives a stub assembler, so its RED is against the wrapper without the clause check. Say "against the assembler and wrapper before the clause, switch and check are added".
