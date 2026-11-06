# Phase 6a-prime Architectural Review — `gate-non-py-production-files` (`716dbdaa~1..716dbdaa`)

## Scope and Files Inspected

Reviewed commit `716dbdaa` (`716dbdaa~1..716dbdaa`) against the spec, design, and Axis B invariants:
- Diff under review: `/private/tmp/claude-501/-Users-kimhawk-orca-skills/85400c95-33ed-40d1-b2e9-1d8141402dc6/scratchpad/6ap_c3.diff`
- Specification: `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/01-plan/features/gate-non-py-production-files.spec.md`
- Design: `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/02-design/features/gate-non-py-production-files.design.md`
- Invariants: `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/.h-mad/invariants.md`, `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/invariants.base.md`
- Production hooks and shared modules:
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-agy-tdd-gate.py`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-tdd-gate.sh`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_tdd_judge.py`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_mutation_harness.py`
- Mutation specs:
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/agy_tdd_gate.json`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/shared_gate_policy.json`
- Tests and fixtures:
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_agy_tdd_gate_non_py.py`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_tdd_gate_non_py.py`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_gate_tmp_reports.py`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_agy_tdd_gate.py`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/non_py_gate_support.py`

## Architectural Review Questions

### 1. What writes under `/tmp` or an artifact directory now read differently
- **Codex (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:212`):** `_tmp_report_target` changed from `if Path(_load_identity().fold_py_suffix(resolved.name)).suffix == ".py":` to `if _load_identity().fold_py_suffix(resolved.name).endswith(".py"):  # M:CX-TMP-PY-NAME`.
- **agy (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-agy-tdd-gate.py:161`):** `outside_allowed` changed from `not any(Path(identity.fold_py_suffix(name)).suffix == ".py" for name in resolved.names)` to `not any(identity.fold_py_suffix(name).endswith(".py") for name in resolved.names)  # M:AG-TMP-PY-NAME`.
- **Exact verdict delta:** `Path(fold_py_suffix(name)).suffix == ".py"` and `fold_py_suffix(name).endswith(".py")` disagree **if and only if** the basename consists solely of one or more leading dots followed by `py` in any ASCII case:
  - `.py`, `.PY`, `.Py`, `.pY`: `Path(".py").suffix` is `""` on Python 3.11–3.15, whereas `".py".endswith(".py")` is `True`. Under active/unknown Phase 5 state, writes to `/tmp/.../.py` (or `.PY`, etc.) and, on agy, `<artifactDirectoryPath>/.../.py` change from **ALLOW** to **DENY** (`H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed.` on codex; `kind=target-outside-root` on agy).
  - `..py`, `...py` (multiple leading dots and nothing else before `py`): on Python 3.14+, `Path("..py").suffix` is `""` (whereas on 3.11–3.13 it was `".py"`). With `.endswith(".py")`, these are now consistently **DENY** across all Python versions.
  - All other names (`x.py`, `.x.py`, `a..py`, `note.txt`, `report.md`, `report.md.done`, `.md`, etc.) produce identical boolean results under both predicates, so their verdicts under `/tmp` and `artifactDirectoryPath` are unchanged.

### 2. Whether anything legitimate is now refused
- **No legitimate write is refused.** The `/tmp` allowance on codex (`_tmp_report_target`) and the `/tmp` + `artifactDirectoryPath` allowance on agy (`outside_allowed`) exist so workers can write markdown/text reports and non-Python scratch artifacts outside the project root while still refusing Python files outside the root. A dotfile literally named `.py` / `.PY` (or `..py`) is a Python-named file per Spec Terms (*Non-`.py`*: `No canonical name of the target ends in .py after h_mad_target_identity.fold_py_suffix`). Positive controls `test_codex_tmp_dot_py_note_txt_allows` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py:54-56`), `test_agy_tmp_dot_py_note_txt_allows` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_agy_tdd_gate_non_py.py:58-60`), `test_a_report_under_tmp_is_allowed`, and `test_artifact_directory_path` confirm legitimate report/artifact writes remain allowed.

### 3. Whether the re-anchored mutation rows still mean what they meant
All four re-anchored rows preserve their exact semantics and target tests, and both new rows discriminate on the `.py` dotfile guard:
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/agy_tdd_gate.json:82-89` (`fr4-artifact-py-refusal-dropped`): `find` re-anchored to `not any(identity.fold_py_suffix(name).endswith(".py") for name in resolved.names)  # M:AG-TMP-PY-NAME`, `replace` remains `True`, killed by `tests/test_h_mad_agy_tdd_gate.py::test_artifact_directory_path`.
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/agy_tdd_gate.json:91-98` (`fr4-t3-after-t5`): `find` and `replace` updated identically on the `outside_allowed` line, still moving T5 before T3–T4 and killed by `tests/test_h_mad_agy_tdd_gate.py::test_tmp_non_py_write_allowed_under_active`.
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/agy_tdd_gate.json:215-222` (`AG-TMP-PY-NAME`, new): restores `Path(identity.fold_py_suffix(name)).suffix == ".py"`, `symbol: "main"`, killed by `tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_tmp_dot_py_denies_like_x_py[.py]`.
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json:27-33` (`python-under-tmp-admitted`): `find` re-anchored to `if _load_identity().fold_py_suffix(resolved.name).endswith(".py"):  # M:CX-TMP-PY-NAME\n        return False`, `replace` remains `if False:\n        return False`, killed by `tests/test_h_mad_codex_gate_tmp_reports.py::test_python_under_tmp_is_still_refused[prod.PY]`.
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json:42-49` (`the-name-check-reads-the-link-not-its-target`): `find` and `replace` updated from `if Path(_load_identity()` to `if _load_identity()`, preserving the `path.resolve()` -> `Path(os.path.normpath(str(path)))` lexical-resolution mutation, killed by `tests/test_h_mad_codex_gate_tmp_reports.py::test_a_report_named_link_to_python_under_tmp_is_refused`.
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json:51-57` (`CX-TMP-PY-NAME`, new): restores `Path(_load_identity().fold_py_suffix(resolved.name)).suffix == ".py"`, killed by `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_tmp_dot_py_denies_like_x_py[.py]`.

### 4. Whether the hosts agree on names of this shape outside the root
- **All three hosts now agree (DENY)** on `.py` / `.PY` / `..py` outside the project root, including under `/tmp` (and under `artifactDirectoryPath` on agy):
  - **Claude (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-tdd-gate.sh:140-145,331-349`):** `_fold_py` folds `*.py|*.pY|*.Py|*.PY` to `${2%.*}.py` (which is `.py` for `.py`/`.PY`), `[[ "$FOLDED_NAME" != *.py ]]` treats it as Python (`ALL_NON_PY=no`), and the out-of-root target is refused (`kind=no-test-resolved` under the Claude-author arrangement, pinned by `test_claude_tmp_dot_py_denies` at `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_tdd_gate_non_py.py:44-51`, or peer-authorship refusal under default authorship).
  - **Codex (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:212,347-351`):** `_tmp_report_target` returns `False` for `.py`/`.PY`, so the gate denies the out-of-root write identically to `x.py`, pinned by `test_codex_tmp_dot_py_denies_like_x_py` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py:44-51`).
  - **agy (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-agy-tdd-gate.py:160-167`):** `outside_allowed` is `False` for `.py`/`.PY` under both `/tmp` and `artifactDirectoryPath`, so the gate denies with `kind=target-outside-root` identically to `x.py`, pinned by `test_agy_tmp_dot_py_denies_like_x_py` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_agy_tdd_gate_non_py.py:48-55`).

## Verification Executed

Ran in a temporary cache directory without touching the repository:
- `PYTHONDONTWRITEBYTECODE=1 python3.11 -m pytest` over `test_h_mad_agy_tdd_gate_non_py.py`, `test_h_mad_codex_tdd_gate_non_py.py`, `test_h_mad_tdd_gate_non_py.py`, `test_h_mad_codex_gate_tmp_reports.py`, and `test_h_mad_agy_tdd_gate.py`: **322 passed**.
- `PYTHONDONTWRITEBYTECODE=1 python3.11 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/agy_tdd_gate.json h-mad/tests/mutation-specs/codex_gate_tmp_reports.json`: **`ANCHORS: ANCHORS_OK specs=2 mutations=28 ok=28 drifted=0 unreadable=0 skipped=0 unclassifiable=0`**.

## Findings

- **Critical / Must-fix:** None.
- **Important:** None.
- **Non-blocking note:** In `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json:50-57`, `CX-TMP-PY-NAME` (like the other 4 pre-existing rows in that file) omits `"symbol": "_tmp_report_target"`, which `--check-anchors` reports as an advisory unpinned count (`unpinned`) while still scoring `ANCHORS_OK`.

ASSESSMENT: READY_TO_MERGE
