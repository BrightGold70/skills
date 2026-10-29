SPEC-AUTHOR: DONE version=v1.1 path=docs/01-plan/features/hmad-test-boundaries.spec.md lines=245 sha256=e33096dd1f25ed3293c4d177af372f4c929c4fbc7166e3dfc85f916c0b9a290d
REPORT=/Users/kimhawk/orca/skills/docs/03-analysis/hmad-test-boundaries.spec-author.v1.1.report.md

# Spec Author Report — `hmad-test-boundaries` (v1.1)

## Premises Verified (`HEAD = 9f330f71d65b5e667bd42a92065e77b9bd030d82`)

- `h-mad/scripts/h_mad_ac_census.py:AC` — verified via `sed -n '29p' h-mad/scripts/h_mad_ac_census.py` -> `AC = re.compile(r"^\s*-\s+(?:\*\*)?AC-(\d+)\.(\d+)([a-z]?)(?:\*\*)?(?: (?:\([^)]*\)|\[[^\]]*\]))?[:.]")`.
- Archived calibration spec active AC counts on bullet/heading lines matching `\bAC-(\d+)\.(\d+)([a-z]?)\b` (excluding `~~AC-...~~` and `(?i)^(?:\()?retired\b`) — verified via `python3 -c 'import re, pathlib; ...'` over the 4 archived specs:
  - `docs/archive/2026-08/exec-path-hardening/exec-path-hardening.spec.md`: `24` active ACs (`AC-1.1`..`AC-6.3`, `0` retired; `h_mad_ac_census.py` -> `ACS: OK count=24 frs=6`).
  - `docs/archive/2026-09/audit-report-docs-copy/audit-report-docs-copy.spec.md`: `40` active ACs (`AC-1.1`..`AC-6.5` including lettered `AC-2.6a`, `AC-2.6b`, `AC-3.5a`, `0` retired; `h_mad_ac_census.py` -> `ACS: OK count=40 frs=6`).
  - `docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.spec.md`: `44` active ACs on `- AC-...` bullet lines (`AC-1.1`..`AC-8.6`, `0` retired; `- AC-3.6 (second arm, OQ-P1),` has a comma after its tag so `h_mad_ac_census.py` outputs `ACS: OK count=43 frs=8`).
  - `docs/archive/2026-10/grok-audit-surface/grok-audit-surface.spec.md`: `64` total ACs (`63` active `AC-1.1`..`AC-11.7` including `AC-6.2a` + `1` retired `AC-3.7: Retired in v1.10.`; `h_mad_ac_census.py` -> `ACS: OK count=64 frs=11`).
- `h-mad/scripts/h_mad_mutation_harness.py`, `h-mad/scripts/h_mad_tdd_judge.py`, `h-mad/hooks/h-mad-tdd-gate.sh`, `h-mad/agents/change-reviewer.md` — verified via `git ls-files 'h-mad/**'` and `python3 h-mad/scripts/h_mad_mutation_harness.py --help` (`ANCHORS: ANCHORS_OK` on `--check-anchors`, `MUTATION: ALL_CAUGHT` on execution).
- `h-mad/agents/design-author.md` headings — verified via `grep -n "^## " h-mad/agents/design-author.md` -> 4 headings: `## Why you exist`, `## Rules — each closes a measured failure class`, `## Output`, `## Where your report goes`.
- `h-mad/audit-prompt.template.md` directives and sections — verified via `grep -n "ONLY:\|^Axis " h-mad/audit-prompt.template.md` -> inline `{{ONLY:design}}` and block `{{ONLY:...}} ... {{END-ONLY}}` under `Axis A — Generic adversarial:` and `Axis C — Spec reconciliation.`.
- `h-mad/agents/doc-auditor.md` headings — verified via `grep -n "^## " h-mad/agents/doc-auditor.md` -> 9 headings including `## Rules — each closes a measured failure class`.

## Findings Applied (all 5 reconciliations from `hmad-test-boundaries.plan-author.v1.0.report.md` §3)

1. **Premise 5, FR-3.1, FR-3.2, AC-3.1, FR-4.2, FR-6.1, AC-6.1 (Lettered AC regex & archived calibration AC counts):** Aligned AC extraction with `\bAC-(\d+)\.(\d+)([a-z]?)\b` on bullet/heading lines (`^\s*(?:-\s+|#{1,6}\s+)`), supporting optional lowercase letter suffix `([a-z]?)` while excluding struck-through `~~AC-X.Y[a-z]~~` and `(?i)^(?:\()?retired\b`; updated FR-6.1 and AC-6.1 active AC counts to `24` (`exec-path-hardening`, `acs=24/24`), `40` (`audit-report-docs-copy`, `acs=40/40`), and `44` (`tdd-gate-fail-opens`, `acs=44/44`).
2. **Executive Summary, FR-5.2, FR-6.3, AC-6.3, Out-of-Scope (Script & agent filenames):** Replaced `h_mad_mutation_check.py` / `MUTATION-CHECK: PASS` with `h-mad/scripts/h_mad_mutation_harness.py` (`--check-anchors` emitting `ANCHORS: ANCHORS_OK` and execution emitting `MUTATION: ALL_CAUGHT`), replaced `h_mad_tdd_gate.py` with `h-mad/scripts/h_mad_tdd_judge.py` and `h-mad/hooks/h-mad-tdd-gate.sh`, and replaced `code-auditor.md` with `h-mad/agents/change-reviewer.md`.
3. **FR-1.2 (`h-mad/agents/design-author.md` structural locators):** Located under `## Rules — each closes a measured failure class` and `## Output`, with residual `## Why you exist` and `## Where your report goes`.
4. **FR-5.1, FR-5.2, AC-5.1 (`h-mad/audit-prompt.template.md` and `h-mad/agents/doc-auditor.md`):** Replaced invalid closing tag with real `{{ONLY:design}} ... {{END-ONLY}}` block or inline `- {{ONLY:design}}` directive under `Axis A — Generic adversarial:` / `Axis C — Spec reconciliation.`, and located the `h-mad/agents/doc-auditor.md` rule under `## Rules — each closes a measured failure class`.
5. **Version History (`v1.1`):** Converted `## Version History` to `- v1.0: ...` bullet shape and bumped to `v1.1` via `python3 h-mad/scripts/h_mad_version_history.py docs/01-plan/features/hmad-test-boundaries.spec.md --version v1.1 --text ...` -> `VERSION-HISTORY: OK path=docs/01-plan/features/hmad-test-boundaries.spec.md version=v1.1 line=245 placement=append`.

## Values Swept

- Command: `grep -nE 'h_mad_mutation_check|MUTATION-CHECK|h_mad_tdd_gate|code-auditor|Before writing|Output contract|/ONLY:design|Phase-specific focus|acs=6/6|acs=8/8|acs=9/9' docs/01-plan/features/hmad-test-boundaries.spec.md` -> `0` matches (`SWEEP-CLEAN: 0 stale occurrences`).
- Command: `grep -nE '24/24|40/40|44/44|h_mad_mutation_harness|h_mad_tdd_judge|change-reviewer|END-ONLY' docs/01-plan/features/hmad-test-boundaries.spec.md` -> all updated occurrences consistent across Executive Summary, Premises, FRs, ACs, Out-of-Scope, and Version History.

## Contradictions Found

- `none` (all 5 reconciliations match the working tree at `9f330f71d65b5e667bd42a92065e77b9bd030d82`).

## Placeholder Scan, Doc-Shape, and AC Census

- `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_precheck_doc.py docs/01-plan/features/hmad-test-boundaries.spec.md --phase spec --root /Users/kimhawk/orca/skills` -> `PRECHECK: PASS issues=0` (advisory `PATH:` notes appear only for the 3 net-new files to be created in Phase 6: `h-mad/scripts/h_mad_test_boundaries_check.py`, `h-mad/tests/test_h_mad_test_boundaries_check.py`, `h-mad/tests/mutation-specs/test_boundaries_gate.json`, kept deliberately as deliverables of this feature).
- `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_doc_shape_check.py docs/01-plan/features/hmad-test-boundaries.spec.md` -> `DOC-SHAPE: SKIP path=docs/01-plan/features/hmad-test-boundaries.spec.md type=none`.
- `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/hmad-test-boundaries.spec.md docs/01-plan/features/hmad-test-boundaries.plan.md` -> `ACS: OK count=17 frs=6`.

## Owed by Other Documents

- `docs/01-plan/features/hmad-test-boundaries.plan.md` (`v1.0`): Its `## Architecture Considerations` item 4 currently flags the 5 v1.0 spec discrepancies as pending reconciliation; in its next revision it can note that `hmad-test-boundaries.spec.md` `v1.1` has resolved all 5 items.
