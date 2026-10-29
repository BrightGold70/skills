# Architectural Review — `hmad-test-boundaries` (Phase 6a-prime)

- **Feature**: `hmad-test-boundaries`
- **Commit Range Reviewed**: `35b013b5d577120def63dee4742ff8c287031641..9c6d54740403b817a875e84b916f4efa93dc7255`
- **Audited Design**: `/Users/kimhawk/orca/skills/docs/02-design/features/hmad-test-boundaries.design.md` (`v1.4`)
- **Audited Spec**: `/Users/kimhawk/orca/skills/docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.5`)
- **Implementation Plan**: `/Users/kimhawk/orca/skills/docs/01-plan/features/hmad-test-boundaries.impl-plan.md` (`v1.2`)

---

## 1. Files Opened and Inspected (Absolute Worktree Paths)

1. `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py` (lines 1–469)
2. `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py` (lines 1–1311)
3. `/Users/kimhawk/orca/skills/h-mad/references/inline-protocols.md` (lines 150–573)
4. `/Users/kimhawk/orca/skills/h-mad/agents/design-author.md` (lines 1–192)
5. `/Users/kimhawk/orca/skills/h-mad/audit-prompt.template.md` (lines 1–260)
6. `/Users/kimhawk/orca/skills/h-mad/agents/doc-auditor.md` (lines 1–261)
7. `/Users/kimhawk/orca/skills/h-mad/tests/test_h_mad_doc_templates.py` (lines 1–203)
8. `/Users/kimhawk/orca/skills/h-mad/tests/mutation-specs/test_boundaries_gate.json` (lines 1–93)
9. `/Users/kimhawk/orca/skills/h-mad/invariants.base.md` (lines 1–331)
10. `/Users/kimhawk/orca/skills/.h-mad/invariants.md` (lines 1–29)
11. `/Users/kimhawk/orca/skills/h-mad/tests/test_h_mad_test_boundaries_check.py` (lines 1–1063)
12. `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_path_scope.py` (lines 1–419)
13. `/Users/kimhawk/orca/skills/.h-mad/wires.jsonl` (lines 1–56)
14. `/Users/kimhawk/orca/skills/docs/02-design/features/hmad-test-boundaries.design.md` (lines 1–912)
15. `/Users/kimhawk/orca/skills/docs/01-plan/features/hmad-test-boundaries.spec.md` (lines 1–264)
16. `/Users/kimhawk/orca/skills/docs/01-plan/features/hmad-test-boundaries.impl-plan.md` (lines 1–950)
17. `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_doc_shape_check.py` (lines 1–220)
18. `/Users/kimhawk/orca/skills/h-mad/tests/tree_lock_plugin.py` (lines 1–155)
19. `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_assemble_audit.py` (lines 1–785)

---

## 2. Architectural Evaluation Across Required Axes

### 2.1 Cross-Module Coupling & Layering

- **Zero external or cross-skill coupling in the standalone checker**: `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:1-10` imports only Python 3 standard-library modules (`__future__.annotations`, `argparse`, `re`, `sys`, `pathlib.Path`, `typing.NamedTuple`). It defines no dependencies on `h_mad_audit_gate.py`, `h_mad_doc_shape_check.py`, `h_mad_assemble_audit.py`, or any external package.
- **Clean one-way delegation from `h_mad_audit_gate.py` to `h_mad_test_boundaries_check.py`**: `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:1-18` keeps its top-level imports strictly stdlib-only (`argparse`, `hashlib`, `importlib.util`, `json`, `os`, `re`, `subprocess`, `sys`, `datetime`, `pathlib.Path`). This preserves compatibility with `/Users/kimhawk/orca/skills/h-mad/tests/tree_lock_plugin.py:56-69,102`, which loads `h_mad_audit_gate.py` via `importlib.util.spec_from_file_location` without `h-mad/scripts` on `sys.path`.
- **Single-source helper ownership**: Inside `_load_test_boundaries_checker()` (`/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:913-930`), `h_mad_audit_gate.py` loads `Path(__file__).with_name("h_mad_test_boundaries_check.py")` via `importlib.util.spec_from_file_location` and delegates `infer_project_root` and `should_activate_design_check` (`/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:952,980,1007`) directly to `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:98-188` rather than duplicating regexes or path-resolution logic.

### 2.2 Facade / Entry-Point Routing vs. Bypassing

- **Audit gate pipeline integration**: `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:1232-1239` invokes `_run_design_boundaries_checks(report_path, doc_paths, verdict)` inside `main()` immediately after document-hash / leg-set verification and **before** the `.gated.json` stamp block (`stamped = ""\n    if args.gated and verdict == "PASS":` at lines 1240–1241).
- **Mutation anchor and signal preservation**: The exact two-line anchor `stamped = ""\n    if args.gated and verdict == "PASS":` required by `audit_suite_gate.json` and `audit_gate_stamp.json` is preserved intact at `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:1240-1241`. When `TEST-BOUNDARIES` fails or is unreadable, `verdict` is flipped to `"FAIL"` while `len(must)` and `len(should)` on the `GATE:` line (`/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:1291-1293`) continue to reflect the audit report's own finding counts, and `TEST-BOUNDARIES:` lines are emitted immediately after `GATE:` / `GATE-CLASS:` / `GATE-LEGS:` (`/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:1302-1307`).
- **bkit mirror boundary respected**: `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_doc_shape_check.py:82-90` (`REQUIRED_SECTIONS["design"]`) is untouched, preserving `TestMirrorFidelity` against bkit's `template-validator.js`, while `/Users/kimhawk/orca/skills/h-mad/references/inline-protocols.md:248-260` and `/Users/kimhawk/orca/skills/h-mad/tests/test_h_mad_doc_templates.py:61-70` extend the H-MAD superset headings (`13 -> 14` in template, `7 -> 8` in `PRIOR_HMAD_HEADINGS["design"]`).

### 2.3 Pattern Compliance with Surrounding Code

- **Signal-token discipline ("Read the token, never `$?`")**: `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:340-465` emits `TEST-BOUNDARIES: PASS | EXEMPT | FAIL` on stdout and exits `0` for all domain outcomes (`PASS`, `EXEMPT`, `FAIL`), reserving `TEST-BOUNDARIES: UNREADABLE` and exit code `2` strictly for operational input failures (missing/directory/non-UTF-8/unreadable design path or explicit `--spec`, or existing directory/non-UTF-8 default-resolved spec path).
- **Fence-aware Markdown parsing**: `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:85-95,213-286` tracks opening and closing fence runs (`` ` `` and `~` of length >= 3) consistently across both `has_test_boundaries_heading` and `_extract_test_boundaries_section`, preventing false activation or section termination on fenced code examples.
- **Head-anchored active vs. retired AC extraction**: `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:143-173` (`extract_spec_acs`) anchors active AC declarations to the start of a bullet item or table cell (`_SPEC_HEAD_AC_RE`, `_SPEC_RETIRED_HEAD_RE`), ignoring prose cross-references while still detecting retired/superseded ACs so `retired-ac-in-row` is reported accurately (`/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:368,386-387`).

### 2.4 Invariant Violations (`.h-mad/invariants.md` & `h-mad/invariants.base.md`)

Checked against `/Users/kimhawk/orca/skills/.h-mad/invariants.md:1-29` and `/Users/kimhawk/orca/skills/h-mad/invariants.base.md:1-331`:

1. **Audit-gate signal discipline**: **Compliant** — `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:455-465` and `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:1232-1307`.
2. **Single-source contract**: **Compliant** — `has_test_boundaries_heading`, `infer_project_root`, `resolve_spec_path`, `extract_spec_acs`, and `should_activate_design_check` live solely in `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:85-188` and are verified for isolated-loading parity in `/Users/kimhawk/orca/skills/h-mad/tests/test_h_mad_test_boundaries_check.py:610-669`.
3. **Standalone / no plugin dependency & No new external dependency**: **Compliant** — stdlib-only imports verified by AST inspection in `/Users/kimhawk/orca/skills/h-mad/tests/test_h_mad_test_boundaries_check.py:960-975`.
4. **Doc-template superset compliance**: **Compliant** — `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_doc_shape_check.py:82-90`, `/Users/kimhawk/orca/skills/h-mad/references/inline-protocols.md:248-260`, `/Users/kimhawk/orca/skills/h-mad/tests/test_h_mad_doc_templates.py:61-70,135-156`.
5. **Operator-override preservation & Backward compatibility**: **Compliant** — `PRE_EXISTING_FEATURES` (10 stems) and `docs/archive/**` emit `EXEMPT` (`/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:36-47,191-210`); `.plan.audit.` and `.impl-plan.audit.` reports are excluded via `_NON_DESIGN_AUDIT_RE` (`/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:908-910,935-936`); synthetic `tmp_path` fixtures without `## Test Boundaries` or active spec ACs do not false-trigger (`/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:176-188`); and `/Users/kimhawk/orca/skills/h-mad/tests/test_grok_audit_surface_path_scope.py:144-153` pins `audit-prompt.template.md` at `PINNED` for its historical commit-range byte-equality test.
6. **Connection enforcement & Mutation verification**: **Compliant** — registered in `/Users/kimhawk/orca/skills/.h-mad/wires.jsonl:56` (`h-mad/scripts/h_mad_audit_gate.py:main -> _run_design_boundaries_checks`) and enforced by the 8-mutation spec in `/Users/kimhawk/orca/skills/h-mad/tests/mutation-specs/test_boundaries_gate.json:1-93` (2 two-direction wire mutations on `h_mad_audit_gate.py` + 6 guard mutations on `h_mad_test_boundaries_check.py`).
7. **Skill self-containment & Skill manifest integrity**: **Compliant** — sibling script resolution uses `Path(__file__).with_name("h_mad_test_boundaries_check.py")` (`/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:919,1011`), and `infer_project_root` derives the target project root from the design path without hardcoding checkout paths.

### 2.5 Dead Code, Unused Imports, Missing Integration Tests, Security & Safety

- **Imports**: Every import in `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:1-10` and `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:1-18` is used.
- **Exported schema constants (Observation only)**: `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:19,49,74-76` defines `REQUIRED_COLUMNS`, `PLACEHOLDER_RE`, and `VERIFIED_BY_KINDS` alongside `EXPECTED_COLUMNS`, `PLACEHOLDER_PREFIXES`, and `VERIFIED_BY_KIND_RE`. These three constants are part of the public module schema specified in `/Users/kimhawk/orca/skills/docs/02-design/features/hmad-test-boundaries.design.md:221-260` and `/Users/kimhawk/orca/skills/docs/01-plan/features/hmad-test-boundaries.impl-plan.md:62-66`. Keeping them matches the design contract; no change required.
- **Integration & calibration test coverage**: `/Users/kimhawk/orca/skills/h-mad/tests/test_h_mad_test_boundaries_check.py:1-1063` (35 tests across 7 test classes) covers standalone unit/CLI behavior, isolated `importlib.util.spec_from_file_location` parity, `h_mad_audit_gate.py` subprocess integration (including `.gated.json` suppression, `must=`/`should=` preservation, `.plan.audit.`/`.impl-plan.audit.` non-activation, and synthetic `tmp_path` non-activation), template/agent prompt contracts, 3 archived design+spec calibrations under `< 200ms`, 5 seeded broken fixture classes, and the 8-mutation harness spec.
- **Security & safety**: Subprocess invocation in `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:1014-1019` uses list arguments (`[sys.executable, str(checker_path), str(design_path), ...]`, no `shell=True`), performs no network or LLM calls, and fails closed (`UNREADABLE` / `verdict = "FAIL"`) on `OSError`, `UnicodeDecodeError`, or unexpected checker output (`/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_gate.py:920-922,1021-1037`).

---

## 3. Categorized Issues

- **Critical**: None (`0`)
- **Important**: None (`0`)
- **Minor / Informational**:
  1. `REQUIRED_COLUMNS`, `PLACEHOLDER_RE`, and `VERIFIED_BY_KINDS` in `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_test_boundaries_check.py:19,49,74-76` are exported public schema aliases alongside `EXPECTED_COLUMNS`, `PLACEHOLDER_PREFIXES`, and `VERIFIED_BY_KIND_RE` as prescribed by `/Users/kimhawk/orca/skills/docs/02-design/features/hmad-test-boundaries.design.md:221-260`. Non-blocking and intentional for design-spec fidelity.

ASSESSMENT: READY_TO_MERGE
