PLAN-AUTHOR: DONE version=v1.0 path=docs/01-plan/features/hmad-test-boundaries.plan.md lines=162 sha256=6b104191589c14cee1d1b3439759c146c4a72bd939b8b7e087b29ce566ae05b8
REPORT=/Users/kimhawk/orca/skills/docs/03-analysis/hmad-test-boundaries.plan-author.v1.0.report.md

# Plan Author Report — `hmad-test-boundaries` (v1.0)

## 1. What Was Changed and Why

Authored initial Phase 3 Plan `docs/01-plan/features/hmad-test-boundaries.plan.md` (`v1.0`, `162` lines, `sha256=6b104191589c14cee1d1b3439759c146c4a72bd939b8b7e087b29ce566ae05b8`) derived from `docs/01-plan/features/hmad-test-boundaries.spec.md` (`6` functional requirement groups `FR-1`..`FR-6`, `17` acceptance criteria `AC-1.1`..`AC-6.3`).

The plan includes all `14` required Phase 3 sections (`# Plan: hmad-test-boundaries`, `## Executive Summary`, `## Overview`, `## Scope`, `## Goals`, `## Requirements`, `## Implementation Strategy`, `## Architecture Considerations`, `## Deliverables`, `## Risks and Mitigation`, `## Convention Prerequisites`, `## Success Criteria`, `## Out-of-Scope (confirmed from spec)`, `## Next Steps`, `## Version History`), avoids all escalation literals, avoids line-number pins and placeholder tokens, and records every tree measurement with its command and commit (`HEAD = 9f330f71d65b5e667bd42a92065e77b9bd030d82`).

## 2. Measurements Run Against the Working Tree (`HEAD = 9f330f71d65b5e667bd42a92065e77b9bd030d82`)

1. **Repository commit:**
   - Command: `git rev-parse HEAD`
   - Result: `9f330f71d65b5e667bd42a92065e77b9bd030d82`
2. **`REQUIRED_SECTIONS["design"]` in `h-mad/scripts/h_mad_doc_shape_check.py`:**
   - Command: `python3 -c 'import sys; sys.path.insert(0, "h-mad/scripts"); import h_mad_doc_shape_check as m; print(len(m.REQUIRED_SECTIONS["design"]), m.REQUIRED_SECTIONS["design"])'`
   - Result: `7 ['Executive Summary', 'Overview', 'Architecture', 'Detailed Design', 'Implementation Order', 'Test Plan', 'Version History']` (`7` headings)
3. **Phase 4 design template headings in `h-mad/references/inline-protocols.md`:**
   - Command: `python3 -c 'import re, pathlib; body = re.search(r"## Phase 4 — Design.*?```markdown\n(.*?)```", pathlib.Path("h-mad/references/inline-protocols.md").read_text(), re.S).group(1); print(len(re.findall(r"^##\s+.+$", body, re.M)))'`
   - Result: `13` level-2 headings (increases to `14` when `## Test Boundaries` is added)
4. **`PRIOR_HMAD_HEADINGS["design"]` in `h-mad/tests/test_h_mad_doc_templates.py`:**
   - Command: `python3 -c 'import ast, pathlib; tree = ast.parse(pathlib.Path("h-mad/tests/test_h_mad_doc_templates.py").read_text()); [print(len(v.elts)) for node in tree.body if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "PRIOR_HMAD_HEADINGS" for k, v in zip(node.value.keys, node.value.values) if getattr(k, "value", "") == "design"]'`
   - Result: `7` entries (increases to `8` when `"Test Boundaries"` is added)
5. **Tracked `.design.md` corpus and absence of `## Test Boundaries`:**
   - Command: `git ls-files 'docs/**/*.design.md' | wc -l && git ls-files 'docs/02-design/features/*.design.md' | wc -l && git ls-files 'docs/archive/**/*.design.md' | wc -l && (git grep -n "Test Boundaries" -- 'docs/02-design/**' 'docs/archive/**' || echo "zero matches")`
   - Result: `39` tracked design files total (`10` in `docs/02-design/features/`, `29` in `docs/archive/`), `0` matches (`zero matches`) for `"Test Boundaries"`
6. **Top-level imports and mutation anchor in `h-mad/scripts/h_mad_audit_gate.py`:**
   - Command: `grep -c "^import \|^from " h-mad/scripts/h_mad_audit_gate.py && grep -F "if args.gated and verdict ==" h-mad/scripts/h_mad_audit_gate.py`
   - Result: `11` stdlib import lines; `    if args.gated and verdict == "PASS":` present verbatim
7. **AC census on `docs/01-plan/features/hmad-test-boundaries.spec.md` and paired plan:**
   - Command: `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/hmad-test-boundaries.spec.md docs/01-plan/features/hmad-test-boundaries.plan.md`
   - Result: `ACS: OK count=17 frs=6`
8. **Sweep of published numbers in `docs/01-plan/features/hmad-test-boundaries.plan.md`:**
   - Command: `grep -nE '17|39|10|29|13|14|7|8|9f330f71d65b5e667bd42a92065e77b9bd030d82' docs/01-plan/features/hmad-test-boundaries.plan.md`
   - Result: All occurrences consistent across prose, tables, and embedded commands.

## 3. What the Tree Contradicted & What `docs/01-plan/features/hmad-test-boundaries.spec.md` Owes

Per `plan-author.md` Rule 4 ("If the tree disagrees with the spec, the design or your findings, say so rather than choosing"), the following 5 discrepancies between `docs/01-plan/features/hmad-test-boundaries.spec.md` (v1.0) and the working tree at `HEAD = 9f330f71d65b5e667bd42a92065e77b9bd030d82` were verified and recorded in `## Architecture Considerations` of the plan:

1. **Owed by `hmad-test-boundaries.spec.md` FR-6.1 & AC-6.1 (Archived calibration target AC counts):**
   - Spec FR-6.1 and AC-6.1 claim the 3 archived calibration targets have `6` (`AC-1.1`..`AC-3.2`, `acs=6/6`), `8` (`AC-1.1`..`AC-4.1`, `acs=8/8`), and `9` (`AC-1.1`..`AC-3.3`, `acs=9/9`) active ACs.
   - Measured against the actual tracked files via `python3 h-mad/scripts/h_mad_ac_census.py <spec>` and FR-3.1 extraction:
     - `docs/archive/2026-08/exec-path-hardening/exec-path-hardening.spec.md` has **`24`** active ACs (`AC-1.1`..`AC-6.3`, `ACS: OK count=24 frs=6`, `0` retired).
     - `docs/archive/2026-09/audit-report-docs-copy/audit-report-docs-copy.spec.md` has **`37`** distinct unlettered `\bAC-(\d+)\.(\d+)\b` ACs (`AC-1.1`..`AC-6.5`) and **`40`** ACs in `h_mad_ac_census.py` (`ACS: OK count=40 frs=6`, including `AC-2.6a`, `AC-2.6b`, `AC-3.5a`; `0` retired).
     - `docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.spec.md` has **`44`** distinct unlettered `\bAC-(\d+)\.(\d+)\b` ACs (`AC-1.1`..`AC-8.6`) and **`43`** ACs in `h_mad_ac_census.py` (`ACS: OK count=43 frs=8`; `AC-3.6 (second arm, OQ-P1),` has a comma after its tag; `0` retired).
   - Spec FR-6.1 and AC-6.1 should be updated to reflect the true AC counts (`24`, `37`/`40`, `44`/`43`).
2. **Owed by `hmad-test-boundaries.spec.md` FR-6.3, AC-6.3, Executive Summary, and Out-of-Scope (Script & agent filenames):**
   - Spec names `h-mad/scripts/h_mad_mutation_check.py` (emitting `MUTATION-CHECK: PASS`), `h_mad_tdd_gate.py`, and `code-auditor.md`.
   - In the working tree (`git ls-files 'h-mad/**'`), those files do not exist; the tracked mutation harness is `h-mad/scripts/h_mad_mutation_harness.py` (emitting `MUTATION: ALL_CAUGHT` and `ANCHORS: ANCHORS_OK`), the Phase 6 TDD gate files are `h-mad/scripts/h_mad_tdd_judge.py` and `h-mad/hooks/h-mad-tdd-gate.sh`, and the code-review agent file is `h-mad/agents/change-reviewer.md`.
3. **Owed by `hmad-test-boundaries.spec.md` FR-1.2 (`h-mad/agents/design-author.md` headings):**
   - Spec FR-1.2 cites `## Before writing` or `## Output contract` in `h-mad/agents/design-author.md`.
   - In `h-mad/agents/design-author.md` (`grep -n "^## " h-mad/agents/design-author.md`), the 4 level-2 headings are `## Why you exist`, `## Rules — each closes a measured failure class`, `## Output`, and `## Where your report goes`.
4. **Owed by `hmad-test-boundaries.spec.md` FR-5.1, FR-5.2, AC-5.1 (`h-mad/audit-prompt.template.md` block syntax and `h-mad/agents/doc-auditor.md` headings):**
   - Spec FR-5.1 and AC-5.1 write `{{ONLY:design}} ... {{/ONLY:design}}` under `### Phase-specific focus`, and FR-5.2 writes `### Phase 4 — Design` in `h-mad/agents/doc-auditor.md`.
   - In `h-mad/audit-prompt.template.md`, block directives close with `{{END-ONLY}}` (never `{{/ONLY:design}}`, which would fail step 7.2 `unresolved_conditional`), and the sections are `Axis A — Generic adversarial:` and `Axis C — Spec reconciliation.`. In `h-mad/agents/doc-auditor.md`, rules live under `## Rules — each closes a measured failure class` (no `### Phase 4 — Design` heading currently exists).
5. **Owed by `hmad-test-boundaries.spec.md` Premise 5 & FR-3.1 (`h_mad_ac_census.py` regex & lettered ACs):**
   - Spec Premise 5 writes `AC_RE = re.compile(r"\bAC-(\d+)\.(\d+)\b")`. In `h-mad/scripts/h_mad_ac_census.py`, the regex is `AC = re.compile(r"^\s*-\s+(?:\*\*)?AC-(\d+)\.(\d+)([a-z]?)(?:\*\*)?(?: (?:\([^)]*\)|\[[^\]]*\]))?[:.]")`, which includes an optional letter suffix `([a-z]?)`.

## 4. Precheck, Doc-Shape, and Digest Verification

- `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_precheck_doc.py docs/01-plan/features/hmad-test-boundaries.plan.md --phase plan --root /Users/kimhawk/orca/skills`
  -> `PRECHECK: PASS issues=0` (advisory `PATH:` notes appear only for the 3 net-new files to be created in Phase 6: `h-mad/scripts/h_mad_test_boundaries_check.py`, `h-mad/tests/test_h_mad_test_boundaries_check.py`, `h-mad/tests/mutation-specs/test_boundaries_gate.json`, kept deliberately as deliverables of this feature)
- `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_doc_shape_check.py docs/01-plan/features/hmad-test-boundaries.plan.md`
  -> `DOC-SHAPE: PASS path=docs/01-plan/features/hmad-test-boundaries.plan.md type=plan`
- `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/hmad-test-boundaries.spec.md docs/01-plan/features/hmad-test-boundaries.plan.md`
  -> `ACS: OK count=17 frs=6`
- `lines=162`, `sha256=6b104191589c14cee1d1b3439759c146c4a72bd939b8b7e087b29ce566ae05b8`
