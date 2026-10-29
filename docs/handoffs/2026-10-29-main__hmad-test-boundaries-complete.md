# Handoff — `hmad-test-boundaries` shipped end-to-end (Phases 1–7); `grok-audit-surface` closed

**Date:** 2026-10-29
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-29-main__bkit-rewake-patches.md

## Session Summary

Closed `/h-mad grok-audit-surface` (Task 17 S4 route + Phase 7 archive/push at `9f330f71`), then ran `/h-mad hmad-test-boundaries` (row 17) end-to-end across Phases 1–7 on `feature/hmad-test-boundaries` and merged to `main` (`19f223b1`). Shipped: the Phase 4 Design `## Test Boundaries` 5-column table contract (`Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions`) in `h-mad/references/inline-protocols.md` and `h-mad/agents/design-author.md`; the standalone stdlib-only deterministic checker `h-mad/scripts/h_mad_test_boundaries_check.py` (with head-anchored active/retired AC extraction, placeholder blocklist, closed tautological-oracle reject-list, `verified by: audit | live-run | operator | doc-review` proving-artifact rules, and `PRE_EXISTING_FEATURES` / `docs/archive/**` exemptions); Phase 4 audit-gate integration in `h-mad/scripts/h_mad_audit_gate.py` via `importlib.util.spec_from_file_location` and the 3-arm activation predicate (`should_activate_design_check`); Phase 4 auditor prompt rules in `h-mad/audit-prompt.template.md` and `h-mad/agents/doc-auditor.md`; and a 35-test calibration suite (`h-mad/tests/test_h_mad_test_boundaries_check.py`) + 8-mutation spec (`h-mad/tests/mutation-specs/test_boundaries_gate.json`, `MUTATION: ALL_CAUGHT`). Phase 6a-prime architectural review scored `ARCHREVIEW: READY_TO_MERGE` (`tools=26`, `channel=report-file`), Phase 6a gap analysis reached `100%` (6/6 FRs, 17/17 ACs), Phase 7 archived all 54 feature docs under `docs/archive/2026-10/hmad-test-boundaries/`, and `main` is pushed and in sync with `origin/main` at `19f223b1`.

## Key Learnings

- **Cross-phase `--gated` test fixtures in `test_h_mad_audit_gate.py` can place `.design.md` files under `docs/02-design/features/` during an `impl-plan` audit:** `test_mixed_cross_directory_stamp_keeps_same_directory_basename_compatible` runs `h_mad_audit_gate.py` on `feat.impl-plan.audit.v1.md` with `--gated feat.design.md` inside `tmp_path/docs/02-design/features/`. Guarding `_candidate_design_paths(audit_file, gated)` in `h-mad/scripts/h_mad_audit_gate.py` with `_NON_DESIGN_AUDIT_RE = re.compile(r"^.+\.(?:plan|impl-plan)\.audit\.v\d+(?:\.[a-z0-9_-]+)?\.md$")` prevents Phase 3/5 audit reports from activating the Phase 4 design boundary check (`AC-4.4`).
- **Tests pinning historical assembler output against a past commit (`PINNED`) must also pin any evolving template input:** `test_switch_off_prompt_is_byte_identical_to_the_pinned_assembler` in `h-mad/tests/test_grok_audit_surface_path_scope.py` compared `pinned.assemble(template=ref / "audit-prompt.template.md")` against `current.assemble(template=SKILL_DIR / "audit-prompt.template.md")`. Once `h-mad/audit-prompt.template.md` gained the `{{ONLY:design}}` Test Boundaries rubric, the live template differed even after stripping `{{ONLY:design}}` (by one blank line). Passing `template=ref / "audit-prompt.template.md"` to both `pinned.assemble` and `current.assemble` isolates the assembler's switch-off behavior while preserving `path-scope-insert-always` mutation kill coverage.
- **Self-check tests referencing a live feature's `.design.md`/`.spec.md` must fall back to `docs/archive/*/<feature>/` after Phase 7c archive:** `h_mad_archive_feature.py --apply` moves `docs/01-plan/features/<feature>.spec.md` and `docs/02-design/features/<feature>.design.md` into `docs/archive/<YYYY-MM>/<feature>/` before Phase 7f's post-merge `--suite` run. Resolving `ROOT / "docs/..."` with a `ROOT.glob("docs/archive/*/<feature>/...")` fallback keeps the self-check green both before and after closure.

## Next Steps

1. **Row 28 split** (operator decision from `2026-10-27`): Move the two real-cycle test IDs out of `h-mad/tests/test_grok_audit_surface_path_scope.py` so the TDD judge's 40 s budget holds under load — see `docs/03-analysis/grok-audit-surface.task14d-gate-2026-10-23.md`.
2. **Row 18**: Brainstorm scope (handoff redaction, a next-session focus field, scout remedy classes) and run as one or more `/h-mad` features — see `docs/03-analysis/2026-10-25-backlog-triage.md`.
3. **Remaining actionable triage rows**: 33, 35, 38, 39, 44, 46 in `docs/03-analysis/2026-10-25-backlog-triage.md`.
4. **Install the carried bkit patches + `patch-verify-on-update.sh` hook on Hawui-Macmini** (when on that machine): pull `main`, apply each `docs/patches/bkit-*/*.patch` per its README, `cp docs/patches/patch-verify-on-update.sh ~/.claude/hooks/`, add the `SessionStart` entry in `~/.claude/settings.json`, and run the hook once.
5. **Check bkit #162 for a maintainer reply** — `gh issue view 162 -R ww-w-ai/bkit-claude-code`.

## Open / Blocked Items

**Carried from `2026-10-29-main__bkit-rewake-patches.md`:**

- **Next Step 1 / Row 17 (`hmad-test-boundaries`)**: **closed** — implemented across Tasks 1–5 (`9c6d5474`), verified in Phase 6 (`ARCHREVIEW: READY_TO_MERGE`, `Match Rate: 100%`), archived in `7dc47059` (`docs/archive/2026-10/hmad-test-boundaries/`), and merged/pushed to `main` at `19f223b1`; claim in `docs/.bkit-memory.json` released.
- **Next Step 2 / `grok-audit-surface` Task 17**: **closed** — `c018f177` (S4 route) and `9f330f71` (closure + archive).
- **`3c34bba8` on `feature/hmad-test-boundaries` (and ai-memory note from `85878391`)**: **closed** — kept on `feature/hmad-test-boundaries` as suggested ("Keep -> later merge is clean") and merged cleanly into `main` (`19f223b1`, where `278fc850` already held the identical patch on `main`).
- **Hawui-Macmini bkit patches (`G-004`, `G-001`, `SubagentStop`, `sprint-stop-hook-active`) + `patch-verify-on-update.sh` install**: open — blocked on access to Hawui-Macmini (Next Step 4).
- **bkit #162 (`ww-w-ai/bkit-claude-code#162`) and G-001 #161 (`ww-w-ai/bkit-claude-code#161`)**: watch, unchanged since 2026-10-29.
- **Two carried bkit patches on Mac Studio (`bkit-subagentstop-additionalcontext`, `bkit-sprint-stop-hook-active`) + `~/.claude/hooks/patch-verify-on-update.sh` copy**: watch (monitored by `SessionStart` hook on this Mac), unchanged since 2026-10-29.
- **Next Step 3 / row 28 split**: open, unchanged since 2026-10-27 (Next Step 1 above).
- **Next Step 4 / row 18 brainstorm**: open, unchanged since 2026-10-27 (Next Step 2 above).
- **Next Step 5 / triage rows 33, 35, 38, 39, 44, 46**: open, unchanged since 2026-10-27 (`docs/03-analysis/2026-10-25-backlog-triage.md`, Next Step 3 above).
- **New `skill-candidates` rows (census OPEN 31)**: open backlog, unchanged since 2026-10-27.
- **HemaSuite `document-intake-source-review::Task 6` WIRE-RUNNER**: owed by HemaSuite, unchanged since 2026-10-27.
- **Wire-registry `missing=268`**: blocked on a HemaSuite checkout, unchanged since 2026-10-27.
- **Codex pin `term_134b0865…` stale**: re-pin before any pinned-pane codex dispatch (`hmad-dispatch exec codex` is unaffected), unchanged since 2026-10-27.
- **Run 8 attempts 1–2**: evidence only, never score — unchanged since 2026-10-27.
- **Rows 23 and 34 (local-only `verify-hmad-*` skills; ~179 leaked `hmad_exec_prompt.*` temp files)**: unverified, actionable on this Mac, unchanged since 2026-10-27.
- **Rows blocked on HemaSuite (41, 49, 50, 52) and watch-only rows**: unchanged since 2026-10-27.

## Context for Next Session

**Files touched this session (all committed and pushed on `main` at `19f223b1`):**
- `h-mad/scripts/h_mad_test_boundaries_check.py` (new, 469 lines, stdlib-only)
- `h-mad/scripts/h_mad_audit_gate.py` (Phase 4 design boundaries gate wiring + `_NON_DESIGN_AUDIT_RE`)
- `h-mad/references/inline-protocols.md` (`## Test Boundaries` in Phase 4 Design template)
- `h-mad/agents/design-author.md` (Rule 7a + `## Output` `TEST-BOUNDARIES: PASS` requirement)
- `h-mad/audit-prompt.template.md` (`{{ONLY:design}} ... {{END-ONLY}}` Axis A rubric)
- `h-mad/agents/doc-auditor.md` (Rule 7c Phase 4 design `## Test Boundaries` rubric)
- `h-mad/tests/test_h_mad_doc_templates.py` (`"Test Boundaries"` in `PRIOR_HMAD_HEADINGS["design"]`)
- `h-mad/tests/test_h_mad_test_boundaries_check.py` (new, 35 tests across 7 classes)
- `h-mad/tests/mutation-specs/test_boundaries_gate.json` (new, 8 mutations, `MUTATION: ALL_CAUGHT`)
- `h-mad/tests/test_grok_audit_surface_path_scope.py` (pin `ref / "audit-prompt.template.md"` in switch-off test)
- `.h-mad/wires.jsonl` (registered `h_mad_audit_gate.py::main->h_mad_test_boundaries_check.py::check_design_boundaries`)
- `docs/archive/2026-10/hmad-test-boundaries/` (54 archived spec, plan, design, impl-plan, audit, archreview, analysis, and report artifacts)

**Uncommitted changes:** 5 pre-existing untracked items not from this session (`.codex/config.toml`, three `docs/03-analysis/2026-10-2{2,3}-*.analysis.md` files, and `hemasuite/docs/research/`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/test_h_mad_test_boundaries_check.py -q
```

**Related docs:**
- `docs/archive/2026-10/hmad-test-boundaries/hmad-test-boundaries.report.md`
- `docs/archive/2026-10/hmad-test-boundaries/hmad-test-boundaries.design.md`
- `docs/archive/2026-10/hmad-test-boundaries/hmad-test-boundaries.spec.md`
- `docs/03-analysis/2026-10-25-backlog-triage.md`
