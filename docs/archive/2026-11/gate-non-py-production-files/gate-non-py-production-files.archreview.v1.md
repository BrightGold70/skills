# Phase 6a-prime Architectural Review — `gate-non-py-production-files`

**Reviewer**: `agy`
**Range**: `3489f86b..f3eacfde`
**Repository Root**: `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files`

---

## Executive Summary

The Phase 5 implementation of `gate-non-py-production-files` across Tasks 1–8 matches the audited design (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/02-design/features/gate-non-py-production-files.design.md`) and implementation plan (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/01-plan/features/gate-non-py-production-files.impl-plan.md`, including its documented "Where this plan departs" adjustments) with zero architectural drift, zero invariant violations, and complete test/mutation and FR-9 empirical evidence.

---

## 1. Architecture & Design Conformance

### Task 1 — Parser Widening & `ungated` Retirement (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_wire_pin_gate.py`)
- `_parse_tasks` (line 247) appends non-`.py` backticked tokens from `**Production file**` lines (`_NON_PY_PATH_RE.findall(paths.group("value")) if not token.endswith(".py")`) directly into `current["production"]` (`# M:P-NONPY`), while keeping `current["tests"]` strictly `.py`-only and preserving `none` handling (`_NONE_VALUE_RE`).
- The advisory `ungated` dictionary key, `_ungated_entries` helper, and `ungated:` CLI output lines are completely retired from `_parse_tasks`, `check()`, and `main()`.
- Wire-pin registration (`_register_task_wires`) continues to filter `p.endswith(".py")`, leaving wire-pin stdout and registry records unchanged for mixed tasks.

### Task 2 — Shared Doc/Data Definition & Path Exemption (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py`)
- `DOC_DATA_SUFFIXES` (line 19) defines the exact nine suffixes (`(".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".rst", ".cfg", ".ini")`) in one place (satisfying D13 and AC-11.6).
- `has_doc_data_suffix` (lines 33–34) folds ASCII uppercase to lowercase via `str.translate(_ASCII_LOWER)` without `str.lower()`, avoiding locale/Unicode hazards and handling dotfiles like `.md` via slice comparison (`name[-len(s):].translate(_ASCII_LOWER) == s`).
- `is_doc_data` (lines 37–38) requires `all(has_doc_data_suffix(n) for n in names)` (`# M:G-DOCDATA-ALL`), preventing mixed hard-link sets (`x.sh` + `x.md`) from bypassing the gate.
- `_is_exempt_location` (lines 41–45) checks `parents = Path(relative).parts[:-1]` (`# M:G-EXEMPT-PARENT`), exempting first-component `docs` (`# M:G-EXEMPT-DOCS`) and parent directories `tests` or `fixtures` (`# M:G-EXEMPT-DIRS`) while keeping a file named `tests` non-exempt.
- `emit_doc_data` (lines 48–49) prints `docdata yes` or `docdata no` (`# M:G-DOCDATA-EMIT`) for the Claude hook's `# M:H11` canonicalise one-liner.

### Task 3 — Single Listing Matcher & Non-`.py` Judge Scoring (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_tdd_judge.py`)
- `_match_plans` (lines 307–336) is the single home of `os.path.realpath(root / entry) == str(real_target)` (satisfying D4 and FR-3). Both `listing` (lines 339–347) and `resolve` (lines 350–385) consume `_match_plans`.
- `listing` enforces operator ruling R-D precedence: `listed` outranks `unreadable` (`# M:L-LISTED`), selecting `min(listed, key=lambda p: p.name)` (`# M:L-SELECT`), while `unreadable` outranks `not-listed` (`# M:L-UNREADABLE`), and an absent impl-plan records `PlanMatch(plan, "absent", "", ())` (`# M:L-ABSENT`) so absent plans resolve to `not-listed`.
- `target_module_names` (lines 490–493) returns `frozenset()` when `Path(fold_py_suffix(target.name)).suffix != ".py"` (`# M:K-IMPORT-NONPY`), ensuring a non-Python target never excuses a `ModuleNotFoundError` during pytest collection.
- The `listing` CLI verb (lines 682–684, 730–747) prints one `TDD-LISTING:` line (`not-listed`, `listed target=<pct>`, or `unreadable file=<pct> error=<ExcName>`) and exits `0` on all normal verdicts, reserving exit `2` (stderr-only, no stdout token) for internal exceptions (`# M:LV-RC`), in strict compliance with the Audit-gate signal discipline invariant.

### Tasks 4, 5, and 6 — Three-Host Gate Integration
- **Codex (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py`)**:
  - Checks `if is_doc_data(resolved.names): continue` (`# M:CX-DOCDATA`, line 359) before `production = []`, so both doc/data targets and directory targets (`names == ()`) short-circuit before any state or plan read.
  - Under `if not production:` (line 367), calls `_judge_listed(root, resolved)` (lines 281–303), which skips test-shaped `.py` files (`# M:CX-NOT-CODE-LIKE`), exempt locations (`# M:CX-LIST-EXEMPT`), and inactive chains (`# M:CX-ACTIVE`), fails closed with `kind=judge-error` on unreadable state (`# M:CX-CHAIN-UNREADABLE`) or unreadable listing (`# M:CX-LIST-UNREADABLE`), allows `not-listed` (`# M:CX-NOT-LISTED`), and judges `listed.selected` (`# M:CX-VERDICT`, `# M:CX-DENY`).
- **Agy (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-agy-tdd-gate.py`)**:
  - Checks `if identity.is_doc_data(resolved.names): continue` (`# M:AG-DOCDATA`, line 174) before `production = []`.
  - Under `if not production:` (lines 182–208), executes the identical 6-step code-like check inline (`# M:AG-NOT-CODE-LIKE`, `# M:AG-LIST-EXEMPT`, `# M:AG-CHAIN-UNREADABLE`, `# M:AG-ACTIVE`, `# M:AG-LIST`, `# M:AG-LIST-UNREADABLE`, `# M:AG-NOT-LISTED`, `# M:AG-VERDICT`), sanitizing any `kind=` in inner details to `kind:` so the outer denial preserves a single trailing `kind=<kind>` token.
- **Claude (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-tdd-gate.sh`)**:
  - Piggybacks `emit_doc_data(i)` onto the `# M:H11` canonicalise invocation (line 266), strips `DOC_DATA_LINE` before `_read_canon` (line 267), and validates `docdata yes|no` after `_read_canon` (`# M:H-DOCDATA-LINE`, line 269) so directory targets (`names 0`) still hit the existing `/bin/bash` 3.2 empty-array `set -u` `judge-error` refusal when state may exist (`test_claude_directory_stays_judge_error_where_state_may_exist`).
  - Replaces the duplicated bash suffix table with `[ "$DOC_DATA" = yes ] && _allow  # M:H-DOCDATA` (line 328).
  - Under `if [ "$ALL_NON_PY" = yes ]; then` (`# M:H-CODE-LIKE`, line 340), allows outside-root targets (`# M:H-LIST-INROOT`), runs `_find_judge` and `_read_listing` (`# M:H-LIST`, lines 196–216), decodes `LISTED_TARGET` with `_pct_capture` (`# M:H-LIST-DECODE`, preserving trailing newlines), verifies membership in `CANON_NAMES` (`# M:H-LIST-NAME`), and sets `TARGET_PATH=$LISTED_TARGET` before flowing into the existing `_read_state`, implementer/peer/fallback checks, and `judge` invocation (including `target=$TARGET_PATH:` context on non-`.py` judge denials at line 406, `# M:H-LIST-CONTEXT`).
  - Process-launch budget verified by `test_claude_process_count`: `2` Python launches for doc/data with state, `2` for unlisted without state, and `4` for unlisted code-like with state (`<= 2` extra processes over the 2-process baseline).

### Task 7 — Prose & Documentation (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/references/codex-implementer-prompt.md`, `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/references/codex-runtime.md`, `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/references/phase5-substeps.md`, `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/references/helper-scripts.md`)
- All four reference documents accurately state the shipped rules, the nine doc/data suffixes, the `listing` verb on `h_mad_tdd_judge.py`, and three-host coverage. Pinned by `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_tdd_gate_docs.py`.

### Task 8 — FR-9 Hermetic Driver & Evidence (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py`)
- Implements all 9 refusals (`no-before-side`, `dirty-hooks`, `hook-outside-tree`, `hook-blob-mismatch`, `authorship-line`, `missing-base`, `base-is-head`, `plan-absent-at-base`, `plan-blob-mismatch`), exiting `2` with `FR9-DRIVE: UNREADABLE <reason>`, and exiting `0` on `FR9-DRIVE: PASS|FAIL`.
- Recorded evidence at `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/03-analysis/probes/gate-non-py-production-files/fr9/20261105T094753Z-c4cedc6d0d00/readings.tsv` and `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/03-analysis/probes/gate-non-py-production-files/fr9/20261105T094753Z-c4cedc6d0d00/provenance.json` covers all 33 rows (9 fixture + 12 replay-before + 12 replay-after across `claude`, `codex`, `agy`) with `PASS` on every row.

---

## 2. Coupling, Cohesion, Dead Code & Security Review

- **Coupling & Cohesion**: High cohesion and single-source-of-truth boundaries. `h_mad_target_identity.py` owns target naming, doc/data suffix classification, and location exemptions; `h_mad_tdd_judge.py` owns plan matching (`_match_plans`), listing (`listing`), and test scoring (`judge`). No circular dependencies or duplicated matching logic exist across the three hooks.
- **Dead Code**: None. The retired `ungated` parser key, `_ungated_entries` function, and `ALL_SUFFIX_NAMES` bash loop were cleanly removed along with their obsolete mutation entries (`U3`, `U4`, `U5` in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/wire_pin_ungated.json`), and all 104 mutation rows (99 new + 5 re-anchored) across `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/` are active and anchored.
- **Security & Fail-Closed Discipline**:
  - Percent-encoding (`_enc` / `_pct_capture`) and newline/multi-line guards in `h-mad-tdd-gate.sh` prevent filename injection, trailing-newline stripping, and foreign-target spoofing (`# M:H-LIST-DECODE`, `# M:H-LIST-NAME`).
  - `kind=` sanitization in `h-mad-agy-tdd-gate.py` prevents hostile error strings or filenames from forging a second `kind=` token.
  - All unreadable state or impl-plan paths fail closed with `kind=judge-error`.

---

## 3. Axis B — Invariants Compliance (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/.h-mad/invariants.md` & `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/invariants.base.md`)

- **Audit-gate signal discipline (`h-mad/invariants.base.md`)**: `h_mad_tdd_judge.py listing` exits `0` on all verdict tokens (`listed`, `not-listed`, `unreadable`) and exits `2` on internal exceptions without printing a verdict token; `fr9_drive.py` exits `0` on `FR9-DRIVE: PASS|FAIL` and exits `2` on `FR9-DRIVE: UNREADABLE <reason>`.
- **Subprocess & Hermeticity (`h-mad/invariants.base.md`)**: Every subprocess call in `fr9_drive.py` and the test suites specifies explicit `timeout=`, runs in isolated `tmp_path` / `tempfile.TemporaryDirectory` directories, and strips ambient `GIT_*` / `HMAD_*` variables.
- **Test Quality & Mutation Discipline (`h-mad/invariants.base.md`)**: All new tests in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_parse_tasks_non_py.py`, `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_doc_data.py`, `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_tdd_judge_listing.py`, `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py`, `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_agy_tdd_gate_non_py.py`, `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_tdd_gate_non_py.py`, and `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_fr9_drive_refusals.py` include hostile fixtures, descriptive assertion messages, and 1-to-1 mutation pins.

---

## 4. Findings

None (0 blockers, 0 should-fix, 0 minor notes).

ASSESSMENT: READY_TO_MERGE
