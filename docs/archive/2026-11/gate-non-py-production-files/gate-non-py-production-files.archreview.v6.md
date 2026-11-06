# Architectural Review — `gate-non-py-production-files` (`e524b58a~1..e524b58a`)

Reviewed range `e524b58a~1..e524b58a` in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files` against:
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/03-analysis/gate-non-py-production-files.archreview.v4.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/03-analysis/gate-non-py-production-files.archreview.v5.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/.h-mad/invariants.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/invariants.base.md`

Files inspected by absolute path:
- `/private/tmp/claude-501/-Users-kimhawk-orca-skills/85400c95-33ed-40d1-b2e9-1d8141402dc6/scratchpad/6ap_c6.diff`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_gate_tmp_reports.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/03-analysis/gate-non-py-production-files.archreview.v4.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/03-analysis/gate-non-py-production-files.archreview.v5.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/.h-mad/invariants.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/invariants.base.md`

---

## 1. Closure of Prior Findings (`archreview.v4.md` and `archreview.v5.md`)

`_tmp_report_target` in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:199-218` now stands as:
```python
    path = Path(raw).expanduser()
    if not path.is_absolute():
        base = Path(cwd).expanduser() if isinstance(cwd, str) and cwd else Path.cwd()
        path = base / path
    canonical = _load_identity().canonicalise(str(root), str(path))
    if canonical.unresolvable:
        return False  # M:CX-TMP-PY-UNRESOLVABLE
    if any(_load_identity().fold_py_suffix(name).endswith(".py") for name in (Path(canonical.target).name, *canonical.names)):  # M:CX-TMP-PY-NAME
        return False
    return _path_within(canonical.target, Path("/tmp"))  # M:G-TMP
```

All Critical and Important code/test findings from `archreview.v4.md` and `archreview.v5.md` are **closed**:
1. **Interpreter-version-dependent `Path.resolve()` behaviour (`archreview.v5.md` Critical 1): Closed.**
   - `resolved = path.resolve()` was removed from `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:212`, and `/tmp` containment at line 218 now reads `_path_within(canonical.target, Path("/tmp"))`.
   - `canonicalise` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py:143-149`, `# M:TI5`) catches `ELOOP` uniformly across Python versions and returns `canonical.unresolvable = True`.
   - `test_a_relative_tmp_report_symlink_loop_fails_closed` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_gate_tmp_reports.py:165-178`) now asserts `reason == "H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed."`, verified in a `mktemp -d` copy across `python3.11`, `python3.12`, `python3.13`, `python3.14`, and `python3.15`.
2. **Test discrimination for `# M:CX-TMP-PY-UNRESOLVABLE` and relative `/tmp` expansion (`archreview.v4.md` Critical 1 & `archreview.v5.md` Critical 2): Closed.**
   - `test_a_relative_dangling_tmp_report_from_outside_root_is_refused` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_gate_tmp_reports.py:124-140`) places `root` at `under_tmp / "r"`. When `CX-TMP-PY-UNRESOLVABLE` stubs `if canonical.unresolvable:` to `if False:`, `canonical.target` is `""`, which `_path_within("", Path("/tmp"))` resolves against `Path.cwd()` (`root`, under `/tmp`) to `True`, flipping the verdict from `deny` to `allow` and killing the mutant (`rc=1`).
   - `test_a_relative_tmp_report_from_outside_root_is_allowed` and `test_relative_python_from_outside_root_is_refused` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_gate_tmp_reports.py:143-162`) test both the positive (`allow`) and `.py` negative (`deny`) outcomes for relative paths resolved against an out-of-root `/tmp` `cwd`.
   - Mutation row `CX-TMP-RELATIVE` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json:82-89`) removes the `if not path.is_absolute():` block and is killed by `test_a_relative_tmp_report_from_outside_root_is_allowed` (`rc=1`).
3. **`symbol` pins and anchor check (`archreview.v4.md` Important 2): Closed.**
   - All 8 entries in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json:18-90` carry `"symbol": "_tmp_report_target"`, `ANCHORS: ANCHORS_OK specs=1 mutations=8 ok=8`, and all 8 mutations fail their designated test when applied in an isolated `mktemp -d` copy.

---

## 2. Evaluation of the Two Remaining Questions from `archreview.v5.md`

### Question A: The `else Path.cwd()` fallback (`h-mad/hooks/h-mad-codex-tdd-gate.py:211`)
```python
    if not path.is_absolute():
        base = Path(cwd).expanduser() if isinstance(cwd, str) and cwd else Path.cwd()
        path = base / path
```
- **Reachability from a real hook input:**
  Reachable only when `payload.get("cwd")` is absent, `""`, or non-`str`, **and** `raw` is a relative path that escapes `root` when `_relative_target` resolves it against `root` (e.g. `raw = "../report.md"`), or when `CODEX_PROJECT_DIR` points to `root` while the hook process working directory (`Path.cwd()`) is outside `root` (e.g. under `/tmp`) and `raw` is a relative path such as `"report.md"`.
- **Does its behaviour matter / what would go wrong in production if it were wrong?**
  - When `CODEX_PROJECT_DIR` and `payload["project_dir"]` / `payload["cwd"]` are absent, `_project_root` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:99-114`) derives `root` from `os.getcwd()`, so `Path.cwd()` and `root` are the same directory.
  - When `CODEX_PROJECT_DIR` is set to `root` and the hook process itself is invoked with `os.getcwd()` under `/tmp` while `payload["cwd"]` is omitted, resolving a relative `raw` against `Path.cwd()` matches how the process resolves relative paths (and matches `_command_cwd` at line 243 and `_path_within` at line 421). Any `.py` target or target resolving outside `/tmp` is still refused by lines 214–218.
  - **Classification:** **Note** (no reachable wrong outcome in production: neither admits a disallowed write nor refuses a legitimate write).

### Question B: `Path(canonical.target).name` beside `*canonical.names` (`h-mad/hooks/h-mad-codex-tdd-gate.py:216`)
```python
    if any(_load_identity().fold_py_suffix(name).endswith(".py") for name in (Path(canonical.target).name, *canonical.names)):  # M:CX-TMP-PY-NAME
```
- **Reachability from a real hook input:**
  Evaluated on every call that reaches line 216 (i.e. whenever `canonical.unresolvable` is `False`). In `canonicalise` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py:154-213`):
  - For an **absent target** (lines 160–163), `canonical.names` is `(os.path.basename(canonical_target),)`, so `Path(canonical.target).name == canonical.names[0]`.
  - For an **existing regular file or symlink to a file** (lines 195–213), `canonical.target` is `os.path.join(prefix, names[0])`, so `Path(canonical.target).name == canonical.names[0]`.
  - For an **existing directory** (lines 168–174), `canonical.target` is `canonical_directory(current)` and `canonical.names` is `()`.
  Therefore, `Path(canonical.target).name` differs from the first element of `canonical.names` only when the target resolves to an existing directory (where `canonical.names` is empty).
- **Does its behaviour matter / what would go wrong in production if it were wrong?**
  - For every file or absent file path, `Path(canonical.target).name` duplicates `canonical.names[0]` and changes nothing.
  - For an existing directory under `/tmp` named `*.py` (e.g. `/tmp/dir.py`), `Path(canonical.target).name` causes `_tmp_report_target` to return `False` (deny), whereas for an existing directory `/tmp/dir` it returns `True` (and the underlying file write tool cannot write a file over an existing directory path anyway).
  - **Classification:** **Note** (harmless redundancy on file targets; no write is wrongly admitted and no legitimate write is wrongly refused).

---

## Summary

No Critical or Important issues remain. All 89 tests in `test_h_mad_codex_gate_tmp_reports.py` and `test_h_mad_codex_tdd_gate_non_py.py` pass, all 8 mutations in `codex_gate_tmp_reports.json` are anchored with `symbol` pins and caught, and symlink-loop refusal is consistent across Python 3.11–3.15.

ASSESSMENT: READY_TO_MERGE
