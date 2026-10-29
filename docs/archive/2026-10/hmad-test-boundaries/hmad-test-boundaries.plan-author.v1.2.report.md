PLAN-AUTHOR: DONE version=v1.2 path=docs/01-plan/features/hmad-test-boundaries.plan.md lines=170 sha256=addee44faed2e7e455e64e4994c8904917557f67e5250fc0b7100a690b8a0eae

# Plan Author Report — `hmad-test-boundaries` (`v1.2`)

## 1. Summary of Changes (`v1.1` -> `v1.2`)

Updated `docs/01-plan/features/hmad-test-boundaries.plan.md` from `v1.1` to `v1.2` in lockstep with `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.2`), resolving all 9 `Must-fix` and 2 `Should-fix` findings from Phase 3 Plan Audit Cycle 1 (`docs/01-plan/features/hmad-test-boundaries.plan.audit.v1.p1.md` and `docs/01-plan/features/hmad-test-boundaries.plan.audit.v1.p2.md`):

1. **`p1` Must-fix 1 (`build` — FR-5 missing-section exemption qualification):**
   - Updated `## Scope` items 5 and 6, `## Goals` (`Goal 5`), `## Requirements` (`FR-5`), `## Implementation Strategy` (`Layer 3`), `## Architecture Considerations` item 4, and `## Risks and Mitigation` to explicitly qualify that a missing `## Test Boundaries` section is a `Must-fix` (`build` class) finding **on a non-exempt design** (matching `spec.md` `v1.2` FR-5.1, FR-5.2, and AC-5.1).
2. **`p1` Must-fix 2 (`build` — Phase 4 self-bootstrapping sequence):**
   - Updated `## Scope` item 2, `## Goals` (`Goal 1`), `## Requirements` (`FR-1`), `## Architecture Considerations` item 4, and `## Next Steps` step 3 to specify the self-bootstrapping sequence (matching `spec.md` `v1.2` FR-1.2 and AC-1.3): `h-mad/agents/design-author.md` is modified during implementation alongside creating `h-mad/scripts/h_mad_test_boundaries_check.py`; once implementation lands, `design-author` runs `h_mad_test_boundaries_check.py` before emitting `DESIGN-AUTHOR: DONE`. For `hmad-test-boundaries`'s own Phase 4 (which runs before implementation creates `h_mad_test_boundaries_check.py`), `docs/02-design/features/hmad-test-boundaries.design.md` is authored with a compliant `## Test Boundaries` table covering all `17` active ACs (`AC-1.1`..`AC-6.3`), and its `TEST-BOUNDARIES: PASS` (`acs=17/17`) verdict is deterministically verified in implementation via `h-mad/tests/test_h_mad_test_boundaries_check.py`.
3. **`p1` Must-fix 3 (`build` — Two-direction connection enforcement per `h-mad/invariants.base.md`):**
   - Updated `## Executive Summary`, `## Scope` (new files 2–3), `## Goals` (`Goal 4`, `Goal 6`), `## Requirements` (`FR-4`, `FR-6`), `## Implementation Strategy` (`Layer 4`), `## Deliverables`, `## Risks and Mitigation`, `## Convention Prerequisites`, and `## Success Criteria` to require both connection-enforcement mutation directions on `h-mad/scripts/h_mad_audit_gate.py` in `h-mad/tests/mutation-specs/test_boundaries_gate.json` and `h-mad/tests/test_h_mad_test_boundaries_check.py`:
     - **Direction 1 (connection removal / bypass):** Removing or bypassing the `h_mad_test_boundaries_check.py` call in `h_mad_audit_gate.py` while leaving `h_mad_test_boundaries_check.py` intact, killed by an integration test running `h_mad_audit_gate.py` on a `PASS` audit report paired with an activated failing `.design.md` (`GATE: FAIL` and `TEST-BOUNDARIES: FAIL`).
     - **Direction 2 (forced unconditional activation):** Forcing the 3-arm activation predicate in `h_mad_audit_gate.py` to `True` unconditionally, killed by a negative fixture test running `h_mad_audit_gate.py` on a `PASS` audit report `--gated` to a bare synthetic `.design.md` in `tmp_path` outside `docs/02-design/features/` and `docs/archive/` with no `## Test Boundaries` heading and no paired `.spec.md` with `AC-X.Y`, asserting `GATE: PASS` and no `TEST-BOUNDARIES:` line.
4. **`p1` Must-fix 4 & `p2` Must-fix 4 (`build` — Repeatable `--gated` candidate selection & stdout emission order in `h_mad_audit_gate.py`):**
   - Updated `## Scope` item 4, `## Goals` (`Goal 4`), `## Requirements` (`FR-4`), `## Implementation Strategy` (`Layer 2`), `## Architecture Considerations` item 2, and `## Risks and Mitigation` to match `spec.md` (`v1.2`) Premise 4, FR-4.2, AC-4.2, and AC-4.3:
     - Collect all `--gated <path>` arguments ending with `.design.md` (preserving CLI order, deduplicated by resolved path); if empty, collect `<report_dir>/<feature>.design.md` (if existing) else `docs/02-design/features/<feature>.design.md` for each positional `<report>` matching `^(?P<feature>.+)\.design\.audit\.v\d+(?:\.[a-z0-9_-]+)?\.md$` (preserving CLI order, deduplicated by resolved path).
     - Evaluate the 3-arm activation condition on each existing candidate `<design_path>` and run `h_mad_test_boundaries_check.py` on every activated candidate **before** computing the final `verdict` and **before** the `.gated.json` stamp block (`    stamped = ""\n    if args.gated and verdict == "PASS":`), flipping `verdict` to `"FAIL"` if any activated candidate returns a token other than `PASS` or `EXEMPT` so no `.gated.json` sidecar is written for any `--gated` path.
     - Print the captured `TEST-BOUNDARIES: ...` (and `TEST-BOUNDARIES-ISSUE:`) lines **immediately after** `GATE:` / `GATE-CLASS:` / `GATE-LEGS:`, preserving `GATE: <PASS|FAIL> ...` as the first stdout line after any `SUITE:` line.
5. **`p2` Must-fix 1 & `p2` Must-fix 2 (`build` — Head-anchored spec AC extraction regex and valid `[:.,\s-]+` character class):**
   - Updated `## Overview`, `## Goals` (`Goal 3`), `## Requirements` (`FR-3`), `## Implementation Strategy` (`Layer 1`), `## Architecture Considerations` item 4, and `## Risks and Mitigation` to anchor spec AC extraction to the head of each bullet/heading line via `^\s*(?:-\s+(?:\[[ xX]\]\s+)?|#{1,6}\s+)(?:~~)?(?:\*\*|`)*(AC-(\d+)\.(\d+)([a-z]?))\b` (ignoring mid-line prose mentions, while extracting all `\bAC-(\d+)\.(\d+)([a-z]?)\b` tokens in column 2 `Acceptance criteria` cells of the design table) and to place `-` at the end of the character class (`[:.,\s-]+`) in the retired-AC rule and verification command.
6. **`p2` Must-fix 3 & `p2` Should-fix 1 (`build` — Disambiguating `UNREADABLE` exit 2 vs `missing_spec` exit 0, and `invalid_columns` zero-AC-token case):**
   - Updated `## Goals` (`Goal 2`), `## Requirements` (`FR-2`, `FR-3`), `## Implementation Strategy` (`Layer 1`), and `## Convention Prerequisites` to match `spec.md` (`v1.2`) FR-2.2, AC-2.1, AC-2.2, and FR-3.2:
     - `TEST-BOUNDARIES: UNREADABLE path=<target_path> err=<ErrorType>` (exit `2`) is emitted when `<design_path>` or an **explicitly passed** `--spec <spec_path>` is missing/directory/non-UTF-8, or when a default-resolved `<spec_path>` exists on disk as a directory or non-UTF-8 file.
     - `TEST-BOUNDARIES: FAIL` with `row=- col=- code=missing_spec` (exit `0`) is emitted when `--spec` was **not** supplied on a non-exempt design and neither default candidate (`<root>/docs/01-plan/features/<feature>.spec.md` nor `<design_dir>/<feature>.spec.md`) exists on disk.
     - `code=invalid_columns` covers both (a) wrong headers / `!= 5` cells and (b) a 5-cell row whose non-empty, non-placeholder `Acceptance criteria` cell contains zero `AC-X.Y[a-z]` tokens when the paired spec has `>= 1` active ACs.
7. **`p2` Must-fix 5 (`measurement` — Phase 4 design template heading count & derivation commands):**
   - Updated `## Scope` item 1 to replace the broken unindented regex (`re.findall(r"^##\s+.+$", body, re.M)` which returned `0` because the template block in `h-mad/references/inline-protocols.md` is indented by 3 spaces) with the exact heading list in tree order (`Executive Summary`, `Overview`, `Architecture Overview`, `Detailed Design`, `Components Changed / Added`, `Implementation Order`, `Data Model / Schema Changes`, `API / Interface Changes`, `Error Handling Strategy`, `Test Strategy`, `Test Plan`, `Invariant Compliance`, `Version History` = `13` headings before, `14` after) and both derivation commands from `spec.md` (`v1.2`) Premise 2.
8. **`p1` Should-fix 1 (`build` — Align `## Scope` modified file list with `## Implementation Strategy` Layer 4):**
   - Updated `## Implementation Strategy` Layer 4 and `## Scope` (`Residual`) so both sections declare the exact same inventory (`6` existing tracked files modified, `3` new files created) and state that `h-mad/tests/test_h_mad_audit_gate.py`, `h-mad/tests/test_h_mad_audit_leg_set_gate.py`, `h-mad/tests/test_h_mad_audit_cycle.py`, `h-mad/tests/test_h_mad_audit_spec_axis.py`, and `h-mad/tests/test_h_mad_doc_shape_check.py` are untouched existing regression test suites.

---

## 2. Tree-Verified Overrides & Reconciliations (`plan-author.md` Rules 4 & 13)

1. **Dispatch Item 1 (`12 -> 13` vs tree-verified `13 -> 14` Phase 4 design template headings):**
   - The dispatch instructions in item 1 listed 12 heading names (`Executive Summary`, `Overview`, `Architecture Overview`, `Components Changed / Added`, `Data Model / Schema Changes`, `API / Interface Changes`, `Detailed Design`, `Error Handling Strategy`, `Implementation Order`, `Test Strategy`, `Invariant Compliance`, `Version History`), omitting `## Test Plan` which exists in `h-mad/references/inline-protocols.md` immediately after `## Test Strategy`.
   - Verified against the working tree at `HEAD = 9f330f71d65b5e667bd42a92065e77b9bd030d82` and against `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.2` Premise 2, FR-1.1, and AC-1.1): the fenced Phase 4 design template block in `h-mad/references/inline-protocols.md` has **`13`** `## ` headings before (`Executive Summary`, `Overview`, `Architecture Overview`, `Detailed Design`, `Components Changed / Added`, `Implementation Order`, `Data Model / Schema Changes`, `API / Interface Changes`, `Error Handling Strategy`, `Test Strategy`, `Test Plan`, `Invariant Compliance`, `Version History`) and **`14`** after inserting `## Test Boundaries`.
   - **Action taken & revert offer (`plan-author.md` Rule 13):** Kept `13 -> 14` (matching the tree and `spec.md` `v1.2` AC-1.1) and replaced the broken regex in `## Scope` item 1 with both working commands from `spec.md` `v1.2` Premise 2. If the orchestrator wants `12 -> 13` instead, `h-mad/references/inline-protocols.md` and `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.2`) would need to remove `## Test Plan` first.
2. **Dispatch Item 8 (`h-mad/prompts/audit-artifact.shared.md` and `test_boundaries_gate.json` classification):**
   - Dispatch item 8 parenthetically listed `h-mad/prompts/audit-artifact.shared.md` and `h-mad/tests/mutation-specs/test_boundaries_gate.json` under "6 modified files".
   - Verified against `git ls-files 'h-mad/**'` at `HEAD = 9f330f71d65b5e667bd42a92065e77b9bd030d82` and `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.2` FR-5 and FR-6.3): `h-mad/prompts/audit-artifact.shared.md` does not exist in the repository (the real tracked files are `h-mad/audit-prompt.template.md` and `h-mad/agents/doc-auditor.md`), and `h-mad/tests/mutation-specs/test_boundaries_gate.json` does not exist yet on disk (it is a net-new file).
   - **Action taken & revert offer (`plan-author.md` Rule 13):** Aligned `## Scope` and `## Implementation Strategy` Layer 4 at **`6` modified tracked files** (`h-mad/references/inline-protocols.md`, `h-mad/agents/design-author.md`, `h-mad/tests/test_h_mad_doc_templates.py`, `h-mad/scripts/h_mad_audit_gate.py`, `h-mad/audit-prompt.template.md`, `h-mad/agents/doc-auditor.md`) and **`3` new files** (`h-mad/scripts/h_mad_test_boundaries_check.py`, `h-mad/tests/test_h_mad_test_boundaries_check.py`, `h-mad/tests/mutation-specs/test_boundaries_gate.json`), removing `test_h_mad_audit_gate.py` and `test_h_mad_audit_spec_axis.py` from Layer 4's modified-files claim so `p1` Should-fix 1 is cleanly closed.

---

## 3. Measurements & Verification Commands Re-Ran at `HEAD` (`9f330f71d65b5e667bd42a92065e77b9bd030d82`)

1. **Repository `HEAD`:**
   - Command: `git rev-parse HEAD`
   - Result: `9f330f71d65b5e667bd42a92065e77b9bd030d82`
2. **Phase 4 design template `## ` heading count in `h-mad/references/inline-protocols.md`:**
   - Command:
     ```bash
     python3 -c 'import re, pathlib; seg = re.search(r"^## Phase 4\b.*?(?=^## Phase |\Z)", pathlib.Path("h-mad/references/inline-protocols.md").read_text(), re.M | re.S).group(0); body = re.search(r"^\s*`{3,4}markdown\s*\n(.*?)(?m:^\s*`{3,4}\s*$)", seg, re.M | re.S).group(1); h = [l.strip().removeprefix("##").strip() for l in body.splitlines() if l.strip().startswith("## ")]; print(len(h), h)'
     ```
   - Result: `13 ['Executive Summary', 'Overview', 'Architecture Overview', 'Detailed Design', 'Components Changed / Added', 'Implementation Order', 'Data Model / Schema Changes', 'API / Interface Changes', 'Error Handling Strategy', 'Test Strategy', 'Test Plan', 'Invariant Compliance', 'Version History']` (`13` headings).
3. **Head-anchored active and retired AC counts across all 5 reference specs:**
   - Command:
     ```bash
     python3 -c 'import re, pathlib; HEAD_AC = re.compile(r"^\s*(?:-\s+(?:\[[ xX]\]\s+)?|#{1,6}\s+)(?:~~)?(?:\*\*|`)*(AC-(\d+)\.(\d+)([a-z]?))\b"); RETIRED = re.compile(r"^\s*(?:-\s+(?:\[[ xX]\]\s+)?|#{1,6}\s+)(?:~~.*AC-\d+\.\d+[a-z]?.*~~|(?:\*\*|`)*AC-\d+\.\d+[a-z]?(?:\*\*|`)*(?:\s*(?:\([^)]*\)|\[[^\]]*\]))*[:.,\s-]+(?:(?:\(|\[)?(?:retired|superseded|removed|dropped)\b))", re.I); [print(p, len({m.group(1) for line in re.split(r"^##\s+Version History\b", pathlib.Path(p).read_text(), flags=re.M)[0].splitlines() if (m := HEAD_AC.match(line)) and not RETIRED.match(line)})) for p in ["docs/01-plan/features/hmad-test-boundaries.spec.md", "docs/archive/2026-08/exec-path-hardening/exec-path-hardening.spec.md", "docs/archive/2026-09/audit-report-docs-copy/audit-report-docs-copy.spec.md", "docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.spec.md", "docs/archive/2026-10/grok-audit-surface/grok-audit-surface.spec.md"]]'
     ```
   - Result:
     - `docs/01-plan/features/hmad-test-boundaries.spec.md 17` (`17` active ACs, `0` retired)
     - `docs/archive/2026-08/exec-path-hardening/exec-path-hardening.spec.md 24` (`24` active ACs, `0` retired)
     - `docs/archive/2026-09/audit-report-docs-copy/audit-report-docs-copy.spec.md 40` (`40` active ACs, `0` retired)
     - `docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.spec.md 44` (`44` active ACs, `0` retired)
     - `docs/archive/2026-10/grok-audit-surface/grok-audit-surface.spec.md 63` (`63` active ACs, `1` retired: `AC-3.7`)
4. **Value sweep across `docs/01-plan/features/hmad-test-boundaries.plan.md` (`plan-author.md` Rule 7):**
   - Command: `grep -n "13\|14\|17\|24\|40\|44\|63\|ONLY:" docs/01-plan/features/hmad-test-boundaries.plan.md`
   - Result: Verified all occurrences of `13 -> 14`, `17`, `24`, `40`, `44`, `63`, and backticked `` `{{ONLY:design}}` `` / `` `{{END-ONLY}}` `` / `` `{{ONLY:plan}}` `` / `` `{{ONLY:impl-plan}}` `` across prose, tables, and embedded one-liners.
5. **Mandatory Self-Checks (`h_mad_version_history.py`, `h_mad_precheck_doc.py`, `h_mad_doc_shape_check.py`, `h_mad_ac_census.py`):**
   - `python3 h-mad/scripts/h_mad_version_history.py --version v1.2 --text '...' docs/01-plan/features/hmad-test-boundaries.plan.md` -> `VERSION-HISTORY: OK path=docs/01-plan/features/hmad-test-boundaries.plan.md version=v1.2 line=170 placement=append`
   - `python3 h-mad/scripts/h_mad_precheck_doc.py docs/01-plan/features/hmad-test-boundaries.plan.md --phase plan --root /Users/kimhawk/orca/skills --allow h-mad/scripts/h_mad_test_boundaries_check.py --allow h-mad/tests/test_h_mad_test_boundaries_check.py --allow h-mad/tests/mutation-specs/test_boundaries_gate.json --allow docs/02-design/features/hmad-test-boundaries.design.md` -> `PRECHECK: PASS issues=0` (advisory `PATH:` lines are exclusively the 4 net-new files/deliverables to be created in Phases 4–6).
   - `python3 h-mad/scripts/h_mad_doc_shape_check.py docs/01-plan/features/hmad-test-boundaries.plan.md` -> `DOC-SHAPE: PASS path=docs/01-plan/features/hmad-test-boundaries.plan.md type=plan`
   - `python3 h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/hmad-test-boundaries.spec.md docs/01-plan/features/hmad-test-boundaries.plan.md` -> `ACS: OK count=17 frs=6`
6. **Final Document Digest (`plan-author.md` Rule 11):**
   - `lines=170`
   - `sha256=addee44faed2e7e455e64e4994c8904917557f67e5250fc0b7100a690b8a0eae`

---

## 4. Owed by Sibling Documents

- **None.** `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.2`) is already aligned with all changes above.
