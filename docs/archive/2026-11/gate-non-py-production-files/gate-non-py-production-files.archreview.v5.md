# Architectural Review — `gate-non-py-production-files` (`55daf487..b0ebb116`)

Reviewed range `55daf487..b0ebb116` in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files` against:
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/03-analysis/gate-non-py-production-files.archreview.v4.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/.h-mad/invariants.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/invariants.base.md`

Files inspected in the worktree:
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_gate_tmp_reports.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/03-analysis/gate-non-py-production-files.archreview.v4.md`

---

## Direct Answers to Review Questions

### 1. Is each prior finding from `archreview.v4.md` really closed?
- **Prior Finding 1 (`# M:CX-TMP-PY-UNRESOLVABLE` and `except Exception: return False` unexercised/unpinned): Closed.**
  - The unreachable `try ... except Exception: return False` wrapper around `canonicalise` in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:214` was removed.
  - `test_a_relative_dangling_tmp_report_from_outside_root_is_refused` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_gate_tmp_reports.py:124-136`) drives a relative target (`../e/note.txt`) with an out-of-root `payload["cwd"]` (`under_tmp / "d"`), so `_relative_target` clamps `base` to `root` and returns `None` while `_tmp_report_target` resolves `base / path` to the dangling symlink `/tmp/.../e/note.txt` and hits `if canonical.unresolvable: return False  # M:CX-TMP-PY-UNRESOLVABLE` (lines 215–216).
  - Mutation row `CX-TMP-PY-UNRESOLVABLE` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json:72-80`) replaces `if canonical.unresolvable:` with `if False:` and is killed by `test_a_relative_dangling_tmp_report_from_outside_root_is_refused` (`MUTATION: ALL_CAUGHT mutations=7 caught=7 survived=0 refused=0`).
- **Prior Finding 2 (`symbol` keys in `codex_gate_tmp_reports.json`): Closed.**
  - All 7 rows in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json:18-81` now carry `"symbol": "_tmp_report_target"`. Running `python3.11 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/codex_gate_tmp_reports.json` prints `ANCHORS: ANCHORS_OK specs=1 mutations=7 ok=7 drifted=0 unreadable=0 skipped=0 unclassifiable=0` with no missing-symbol warning.

### 2. Is each remaining branch in `_tmp_report_target` reached by a real hook input and pinned by a test that fails without it?
No — three branches/clauses in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:209-219` are not pinned by a discriminating test:
1. **`if not path.is_absolute():` (lines 210–212) has no positive `/tmp` admission test and is only accidentally tripped on Python <= 3.12 by the interpreter-dependent symlink-loop exception test:**
   - If `if not path.is_absolute():` is removed (so `path` stays relative `Path("../e/note.txt")`), `test_a_relative_dangling_tmp_report_from_outside_root_is_refused` **still passes**, because `path.resolve()` resolves against `Path.cwd()` (`root`, under `$TMPDIR` `/var/folders/...`), `canonical.unresolvable` is `False`, `_path_within(str(resolved), Path("/tmp"))` returns `False`, and `_main_guarded` returns the exact same denial string (`"H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed."`).
   - There is no test where a relative `raw` with `payload["cwd"]` under `/tmp` (e.g. `raw="../e/report.md"`, `cwd=str(under_tmp / "d")`) is **allowed**, which would flip from `allow` to `deny` if `if not path.is_absolute():` or `Path(cwd).expanduser()` were removed.
2. **`if isinstance(cwd, str) and cwd else Path.cwd()` — the `else Path.cwd()` fallback (line 211) is unpinned:**
   - Replacing `base = Path(cwd).expanduser() if isinstance(cwd, str) and cwd else Path.cwd()` with `base = Path(cwd).expanduser()` or `... else root` passes all 87 tests in `test_h_mad_codex_gate_tmp_reports.py` and `test_h_mad_codex_tdd_gate_non_py.py`.
   - Moreover, when `cwd` is absent/empty (`None` or `""`), `_relative_target(root, raw, cwd)` already resolved `raw` against `root` (`base = root` in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:174`), whereas `Path.cwd()` in `_tmp_report_target` uses the hook process working directory instead of `root`.
3. **`resolved.name` in `(resolved.name, *canonical.names)` (line 217) is redundant with `canonical.names` for all file/symlink targets and unpinned:**
   - Once `canonical.unresolvable` is `False` (line 215), `canonicalise` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py:154-213`) sets `canonical.names` to `(os.path.basename(canonical_target),)` for an absent path and to `tuple(sorted(matching))` (all non-symlink entries in the referent's parent directory sharing `(st_dev, st_ino)`, which includes `resolved.name`) for any existing file or symlink to a file. Only an existing directory has `canonical.names == ()`.
   - Replacing `for name in (resolved.name, *canonical.names)` with `for name in canonical.names` passes all 87 tests in `test_h_mad_codex_gate_tmp_reports.py` and `test_h_mad_codex_tdd_gate_non_py.py`.

### 3. Does anything a test asserts depend on the interpreter version?
- **Yes (Critical):** `test_a_relative_tmp_report_symlink_loop_fails_closed` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_gate_tmp_reports.py:139-153`) asserts:
  ```python
  assert "gate raised RuntimeError: Symlink loop" in reason, reason
  assert "refusing fail-closed. kind=judge-error" in reason, reason
  ```
  - In Python 3.11 and 3.12, `Path.resolve()` (`strict=False` by default) raises `RuntimeError: Symlink loop from '...'` on `ELOOP` at `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:213`, which escapes `_tmp_report_target` to `main()`'s `# M:G2` handler (line 282) and produces `"H-MAD Phase 5 gate raised RuntimeError: Symlink loop ...; refusing fail-closed. kind=judge-error"`.
  - In Python 3.13, 3.14, and 3.15 (`Path.resolve(strict=False)` was changed in Python 3.13 to match `os.path.realpath(..., strict=False)` and not raise on symlink loops unless `strict=True`), `path.resolve()` on line 213 returns `Path('/private/tmp/.../e/note.txt')` without raising. Execution then proceeds to `canonicalise` on line 214, which catches `ELOOP` (`except OSError:  # M:TI5` at `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py:143`) and returns `Identity(..., unresolvable=True)`. Line 216 (`if canonical.unresolvable: return False`) returns `False`, and `_main_guarded` (line 356) denies with:
    `"H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed."`
  - Executed verification across all five interpreters on this machine:
    ```bash
    python3 - <<'PY'
    import json, shutil, subprocess, tempfile
    from pathlib import Path
    repo = Path("/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files")
    gate = repo / "h-mad/hooks/h-mad-codex-tdd-gate.py"
    for py in ("python3.11", "python3.12", "python3.13", "python3.14", "python3.15"):
        exe = shutil.which(py)
        with tempfile.TemporaryDirectory(prefix="hmad-root-") as rtd, \
             tempfile.TemporaryDirectory(dir="/tmp", prefix="hmad-tmp-") as utd:
            root = Path(rtd) / "root"
            (root / "docs").mkdir(parents=True)
            (root / "docs/.bkit-memory.json").write_text('{"orchestrator_state":{"f":{"phase":"step5"}}}')
            under_tmp = Path(utd)
            cwd = under_tmp / "d"; cwd.mkdir()
            (under_tmp / "e").mkdir()
            loop = under_tmp / "e/note.txt"; loop.symlink_to(loop)
            payload = {
                "tool_name": "apply_patch",
                "tool_input": {"patch": "*** Begin Patch\n*** Add File: ../e/note.txt\n+report\n*** End Patch\n"},
                "cwd": str(cwd),
            }
            r = subprocess.run([exe, str(gate)], input=json.dumps(payload), text=True,
                               capture_output=True, cwd=root,
                               env={"PATH": "/usr/bin:/bin", "HOME": str(root), "CODEX_PROJECT_DIR": str(root)})
            print(py, "->", json.loads(r.stdout)["hookSpecificOutput"]["permissionDecisionReason"])
    PY
    ```
    Observed output:
    ```text
    python3.11 -> H-MAD Phase 5 gate raised RuntimeError: Symlink loop from '/private/tmp/hmad-tmp-qzk7n3wt/e/note.txt'; refusing fail-closed. kind=judge-error
    python3.12 -> H-MAD Phase 5 gate raised RuntimeError: Symlink loop from '/private/tmp/hmad-tmp-6t6cvzo5/e/note.txt'; refusing fail-closed. kind=judge-error
    python3.13 -> H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed.
    python3.14 -> H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed.
    python3.15 -> H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed.
    ```

---

## Critical & Important Issues

### 1. [Critical — Interpreter-version-dependent test assertion & `Path.resolve()` divergence] `test_a_relative_tmp_report_symlink_loop_fails_closed` fails on Python 3.13–3.15
- **References:**
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:213-219` (`_tmp_report_target`)
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_gate_tmp_reports.py:139-153` (`test_a_relative_tmp_report_symlink_loop_fails_closed`)
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py:143-150` (`canonicalise` `# M:TI5`)
- **What is wrong:**
  `test_a_relative_tmp_report_symlink_loop_fails_closed` asserts `"gate raised RuntimeError: Symlink loop" in reason` and `"refusing fail-closed. kind=judge-error" in reason`. That assertion holds only on Python <= 3.12 where `Path.resolve()` raises `RuntimeError` on `ELOOP`. On Python 3.13, 3.14, and 3.15 (including this machine's default `python3` 3.15.2 used by the hook's `#!/usr/bin/env python3` shebang), `Path.resolve()` does not raise on a symlink loop; instead `canonicalise` catches `ELOOP` (`# M:TI5`) and sets `canonical.unresolvable = True`, so the hook denies with `"H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed."` and the test fails.
- **Why it matters:**
  The codebase explicitly supports and measures Python 3.11 through 3.15 (and the live hook shebang runs `python3` = 3.15.2). Having `_tmp_report_target` call `path.resolve()` before `canonicalise` splits symlink-loop handling across two different code paths depending on the Python minor version (`# M:G2` uncaught `RuntimeError` on 3.11–3.12 vs `# M:CX-TMP-PY-UNRESOLVABLE` on 3.13–3.15), and the test pins the 3.11–3.12 artifact.
- **How to fix:**
  Remove `resolved = path.resolve()` from `_tmp_report_target` and use `canonical` (from `canonicalise(str(root), str(path))`) as the single source of truth after `if canonical.unresolvable: return False`:
  - `canonical.names` already holds the resolved basename(s) for every regular file, symlink, and absent file (and for a directory `canonical.names` is `()`, or `Path(canonical.target).name` if directory names must be checked).
  - `canonical.target` is the canonical path string, so `_path_within(canonical.target, Path("/tmp"))` checks `/tmp` containment without calling `path.resolve()`.
  - With `path.resolve()` removed, a relative symlink loop under `/tmp` hits `canonical.unresolvable` (`# M:CX-TMP-PY-UNRESOLVABLE`) and returns `"H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed."` identically on Python 3.11, 3.12, 3.13, 3.14, and 3.15. Update `test_a_relative_tmp_report_symlink_loop_fails_closed` to assert that interpreter-independent denial reason.
- **Operator override reasonable?** No.

### 2. [Critical — Axis B `invariants.base.md` §"Test discrimination"] Relative `/tmp` path resolution branches in `_tmp_report_target` are not discriminated by a positive test
- **References:**
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:210-217` (`_tmp_report_target`)
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_gate_tmp_reports.py:124-153`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/invariants.base.md:118-130` (§"Test discrimination")
- **What is wrong:**
  Tested in a throwaway copy (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py`):
  1. Deleting `if not path.is_absolute(): ... path = base / path` leaves `test_a_relative_dangling_tmp_report_from_outside_root_is_refused` **green** (because `../e/note.txt` resolved against `root` under `$TMPDIR` is outside `/tmp` and denies with the identical message). No test in the suite exercises an **allowed** relative `/tmp` report write (e.g. `raw="../e/report.md"` with `payload["cwd"] = str(under_tmp / "d")`), so removing relative-to-`cwd` resolution in `_tmp_report_target` never flips an `allow` to `deny` (or a `deny` to `allow`, once `path.resolve()` is fixed).
  2. In `base = Path(cwd).expanduser() if isinstance(cwd, str) and cwd else Path.cwd()`, the `else Path.cwd()` branch (or `else root`) and `resolved.name` in `(resolved.name, *canonical.names)` can be mutated without failing any of the 87 tests in `test_h_mad_codex_gate_tmp_reports.py` and `test_h_mad_codex_tdd_gate_non_py.py`:
     ```text
     drop-if-not-is_absolute: rc=1 -> 1 failed, 86 passed (only test_a_relative_tmp_report_symlink_loop_fails_closed on 3.11)
     else-Path.cwd-to-root: rc=0 -> 16 passed
     drop-resolved.name-keep-canonical.names: rc=0 -> 87 passed
     ```
- **Why it matters:**
  Under `h-mad/invariants.base.md` §"Test discrimination", every guard/branch in `_tmp_report_target` must be reachable by a real hook input and pinned by a test that fails when that branch is removed or stubbed.
- **How to fix:**
  1. Add a test where a relative non-`.py` report path with `payload["cwd"]` under `/tmp` (e.g. `_add("../e/report.md")` with `cwd=str(under_tmp / "d")`) is **allowed** (and a relative `.py` path with `cwd=str(under_tmp / "d")` is **denied**), and/or if `_tmp_report_target` only joins `cwd` when `isinstance(cwd, str) and cwd` (since when `cwd` is absent, `_relative_target` already resolved relative `raw` against `root`), simplify the condition so there is no dead `else Path.cwd()` fallback (or pin `else Path.cwd()` with a relative `/tmp` test where `payload` omits `cwd` and the hook runs with `cwd=under_tmp`).
  2. Either drop the redundant `resolved.name` from `(resolved.name, *canonical.names)` (using `canonical.names`, since `canonical.unresolvable` is already `False` and a directory target has `canonical.names == ()` and is not a report file — or `if not canonical.names: return False`), or pin a directory named `dir.py` under `/tmp` if `resolved.name` is intentionally kept for directories.
- **Operator override reasonable?** No (Axis B base invariant).

ASSESSMENT: WITH_FIXES
