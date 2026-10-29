PLAN-AUTHOR: DONE version=v1.1 path=docs/01-plan/features/hmad-test-boundaries.plan.md lines=162 sha256=8297edc5d3e3f754a37b5a4e68cd95d53a0cfc6eee8137a4416fac8fff80e844
REPORT=/Users/kimhawk/orca/skills/docs/03-analysis/hmad-test-boundaries.plan-author.v1.1.report.md

# Plan Author Report — `hmad-test-boundaries` (v1.1)

## 1. What Was Changed and Why

Revised `docs/01-plan/features/hmad-test-boundaries.plan.md` to `v1.1` (`lines=162`, `sha256=8297edc5d3e3f754a37b5a4e68cd95d53a0cfc6eee8137a4416fac8fff80e844`) to align with `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.1`), where `spec-author` applied all 5 tree-verified reconciliations from the `plan-author` `v1.0` report:

1. **`## Goals` (Goals 3, 5, 6) & `## Requirements` (FR-1, FR-3, FR-5, FR-6):**
   - Updated AC extraction contract to `\bAC-(\d+)\.(\d+)([a-z]?)\b` on bullet/heading lines (`^\s*(?:-\s+|#{1,6}\s+)`), supporting optional lowercase letter suffixes (`AC-X.Y[a-z]`).
   - Updated `h-mad/agents/design-author.md` structural locators to `## Rules — each closes a measured failure class` and `## Output`.
   - Updated `h-mad/audit-prompt.template.md` directive syntax to `{{ONLY:design}} ... {{END-ONLY}}` (or inline `- {{ONLY:design}}`) under `Axis A — Generic adversarial:` / `Axis C — Spec reconciliation.`, and `h-mad/agents/doc-auditor.md` structural locator to `## Rules — each closes a measured failure class` (with `h-mad/agents/change-reviewer.md` unchanged).
   - Updated the 3 archived calibration target counts to `24` (`exec-path-hardening`, `acs=24/24`), `40` (`audit-report-docs-copy`, `acs=40/40` including `AC-2.6a`, `AC-2.6b`, `AC-3.5a`), and `44` (`tdd-gate-fail-opens`, `acs=44/44`), and updated mutation verification to `h-mad/scripts/h_mad_mutation_harness.py` (`ANCHORS: ANCHORS_OK` and `MUTATION: ALL_CAUGHT`).
2. **`## Architecture Considerations` (Item 4) & `## Risks and Mitigation` (Rows 4 & 5):**
   - Replaced the v1.0 "pending reconciliation" caveats with the aligned `hmad-test-boundaries.spec.md` `v1.1` contracts and the risk/mitigation entry for lettered ACs, non-colon punctuation after AC tags (`- AC-3.6 (second arm, OQ-P1),`), and retired ACs (`AC-3.7: Retired in v1.10.`).
3. **`## Next Steps` & `## Version History`:**
   - Removed the completed spec-reconciliation step from `## Next Steps` item 3 and bumped `## Version History` to `v1.1` via `h_mad_version_history.py`.

## 2. Measurements Re-Run Against the Working Tree (`HEAD = 9f330f71d65b5e667bd42a92065e77b9bd030d82`)

1. **Repository commit:**
   - Command: `git rev-parse HEAD`
   - Result: `9f330f71d65b5e667bd42a92065e77b9bd030d82`
2. **Active AC counts in the 4 archived calibration/reference specs:**
   - Command: `python3 -c 'import re, pathlib; [print(p, len({m.group(0) for line in re.split(r"^##\s+Version History\b", pathlib.Path(p).read_text(), flags=re.M)[0].splitlines() if re.match(r"^\s*(?:-\s+|#{1,6}\s+)", line) and not re.search(r"~~.*AC-\d+\.\d+[a-z]?.*~~|AC-\d+\.\d+[a-z]?(?:\*\*)?(?:\s*(?:\([^)]*\)|\[[^\]]*\]))?[:.,-\s]+(?:\()?retired\b", line, re.I) for m in re.finditer(r"\bAC-(\d+)\.(\d+)([a-z]?)\b", line)})) for p in ["docs/archive/2026-08/exec-path-hardening/exec-path-hardening.spec.md", "docs/archive/2026-09/audit-report-docs-copy/audit-report-docs-copy.spec.md", "docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.spec.md", "docs/archive/2026-10/grok-audit-surface/grok-audit-surface.spec.md"]]'`
   - Result: `exec-path-hardening.spec.md` = `24` active ACs; `audit-report-docs-copy.spec.md` = `40` active ACs; `tdd-gate-fail-opens.spec.md` = `44` active ACs; `grok-audit-surface.spec.md` = `63` active ACs (`+ 1` retired `AC-3.7`).
3. **Version History bump:**
   - Command: `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_version_history.py docs/01-plan/features/hmad-test-boundaries.plan.md --version v1.1 --text "..."`
   - Result: `VERSION-HISTORY: OK path=docs/01-plan/features/hmad-test-boundaries.plan.md version=v1.1 line=162 placement=append`
4. **Value sweep across `docs/01-plan/features/hmad-test-boundaries.plan.md`:**
   - Command: `grep -nE 'h_mad_mutation_check|MUTATION-CHECK|h_mad_tdd_gate|code-auditor|Before writing|Output contract|/ONLY:design|Phase-specific focus|acs=6/6|acs=8/8|acs=9/9' docs/01-plan/features/hmad-test-boundaries.plan.md || echo "SWEEP-CLEAN: 0 stale occurrences"`
   - Result: `SWEEP-CLEAN: 0 stale occurrences`
5. **Precheck, Doc-Shape, AC Census, and Final Digest:**
   - `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_precheck_doc.py docs/01-plan/features/hmad-test-boundaries.plan.md --phase plan --root /Users/kimhawk/orca/skills` -> `PRECHECK: PASS issues=0` (advisory `PATH:` notes appear only for the 3 net-new deliverables to be created in Phase 6: `h-mad/scripts/h_mad_test_boundaries_check.py`, `h-mad/tests/test_h_mad_test_boundaries_check.py`, `h-mad/tests/mutation-specs/test_boundaries_gate.json`).
   - `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_doc_shape_check.py docs/01-plan/features/hmad-test-boundaries.plan.md` -> `DOC-SHAPE: PASS path=docs/01-plan/features/hmad-test-boundaries.plan.md type=plan`
   - `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/hmad-test-boundaries.spec.md docs/01-plan/features/hmad-test-boundaries.plan.md` -> `ACS: OK count=17 frs=6`
   - `lines=162`, `sha256=8297edc5d3e3f754a37b5a4e68cd95d53a0cfc6eee8137a4416fac8fff80e844`

## 3. Contradictions & Owed by Other Documents

- **Contradictions with the tree:** `none` — `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.1`) and `docs/01-plan/features/hmad-test-boundaries.plan.md` (`v1.1`) are now fully aligned with the working tree at `9f330f71d65b5e667bd42a92065e77b9bd030d82`.
- **Owed by other documents:** `none`.
