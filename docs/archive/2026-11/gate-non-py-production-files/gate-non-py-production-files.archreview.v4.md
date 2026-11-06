# Architectural Review — `gate-non-py-production-files` (Commit `55daf487`)

Reviewed range `55daf487~1..55daf487` in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files` against:
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/.h-mad/invariants.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/invariants.base.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/02-design/features/gate-non-py-production-files.design.md`

---

## Direct Answers to Review Questions

### 1. Which `/tmp` writes now read differently?
- **Same-directory hard links under `/tmp` to any Python-named file (`.py`, `.PY`, `.pY`, `.Py`, including dotfiles `.py` / `.PY`):**
  Previously, `_tmp_report_target` in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:199-222` checked only `resolved.name` from `path.resolve()`. Writing `/tmp/<dir>/note.txt` (or `note.md`) when hard-linked in the same directory to `/tmp/<dir>/x.py`, `.py`, or `X.PY` resolved to `"note.txt"` and read **ALLOW**.
  Now `_tmp_report_target` inspects `(resolved.name, *canonical.names)` from `h_mad_target_identity.canonicalise(str(root), str(path))`. Because `canonicalise` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py:196-205`) scans the target's parent directory for all non-symlink entries sharing `(st_dev, st_ino)`, `canonical.names` includes the `.py` sibling name, `_tmp_report_target` returns `False`, and when `phase5_status in {"active", "unknown"}` the gate returns **DENY** (`"H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed."`, no `kind=` token).
- **Relative `raw` with an out-of-root `payload["cwd"]` resolving to an unresolvable `/tmp` target (e.g. a dangling symlink to a non-`.py` name):**
  When `raw` is relative (e.g. `"../note.txt"`) and `payload["cwd"]` is outside `root` (e.g. `"/tmp/a/b"`), `_relative_target` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:174`) clamps `base` to `root` via `_payload_cwd_base(root, cwd)` and returns `None` (since `root/..` is outside `root` and resolvable), whereas `_tmp_report_target` resolves `Path(cwd) / raw` (`/tmp/a/note.txt`). If `/tmp/a/note.txt` is a dangling symlink to `/tmp/a/missing.txt`, `path.resolve()` previously yielded `/private/tmp/a/missing.txt` (**ALLOW**); now `canonical.unresolvable` is `True` and `_tmp_report_target` returns `False` (**DENY**).
  By contrast, for any **absolute** `/tmp` target (including `/tmp/.../note.txt -> missing.txt`), a dangling symlink or unreadable directory already read **DENY `kind=judge-error`** before `55daf487`, because `_relative_target` returns `Identity(..., unresolvable=True)` (not `None`) and `_main_guarded` denies at line 363 before `_tmp_report_target` is ever called.

### 2. Is a legitimate report write now refused or slowed?
- **Not refused:** A legitimate `/tmp` report write (whether absent and about to be created, or an existing regular file/symlink whose parent directory holds no `.py` hard link to the same inode) continues to read **ALLOW**. In `canonicalise` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py:154-163, 196-205`), an absent report takes the `if absent:` branch without scanning the directory, and an existing report scans its parent directory with `entry.is_symlink()` and `entry.stat(follow_symlinks=False)` (`lstat`), so unrelated broken symlinks or unreadable files owned by other users in `/tmp` do not cause `canonicalise` to fail. Moreover, `_relative_target` at line 189 was *already* calling `canonicalise` on every target before `_tmp_report_target`.
- **Redundant work, negligible wall-clock slowdown:** `_relative_target` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:189-195`) already calls `identity.canonicalise(str(root), str(Path(raw).expanduser()), str(base))` and discards the resulting `Identity` by returning `None` when `Path(resolved.target).relative_to(root)` raises `ValueError`. `_tmp_report_target` then calls `path.resolve()` and `canonicalise` a second time in-process (<1 ms per `/tmp` target).

### 3. Can anything raise past `_tmp_report_target`?
- **Yes, outside the `try` block:** Lines 209–213 and 222 of `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py` sit outside `try ... except Exception:`:
  ```python
  path = Path(raw).expanduser()
  if not path.is_absolute():
      base = Path(cwd).expanduser() if isinstance(cwd, str) and cwd else Path.cwd()
      path = base / path
  resolved = path.resolve()
  ```
  - In Python 3.11, `Path.resolve()` raises `RuntimeError: Symlink loop from '...'` on a symlink loop (`ELOOP`). For an absolute `/tmp` symlink loop, `_relative_target` catches `ELOOP` inside `canonicalise` (`except OSError: # M:TI5`, `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py:143`) and returns `Identity(..., unresolvable=True)`, so `_tmp_report_target` is not called. However, if `_tmp_report_target` is reached on a symlink loop (via a relative `raw` and an out-of-root `payload["cwd"]`, or a direct call), `resolved = path.resolve()` on line 213 raises `RuntimeError` past `_tmp_report_target` (caught at `main()`'s top-level `# M:G2` handler on line 285, which fails closed with `kind=judge-error`).
  - Similarly, `Path(cwd).expanduser()` can raise `RuntimeError` if `cwd` starts with `~` and `HOME` is unset/unresolvable, and `Path.cwd()` can raise `FileNotFoundError` if the process working directory was unlinked and `cwd` is absent.
- **Inside the `try` block:** `canonicalise(str(root), str(path))` catches `OSError` around every filesystem operation in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py:85-213` and returns an `Identity` tuple rather than raising, so `except Exception: return False` on lines 216–217 does not catch anything after line 213 succeeds.

### 4. Is each new branch reachable and is its behaviour pinned?
- **Branch 1 (`if any(... for name in (resolved.name, *canonical.names)): return False  # M:CX-TMP-PY-NAME`, lines 220–221): Reachable and pinned.**
  - Reached whenever a `/tmp` target has a same-directory `.py` hard link.
  - Pinned by `test_codex_tmp_hard_link_to_python_denies` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py:59-66`) and mutation row `CX-TMP-PY-ALLNAMES` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json:59-65`).
- **Branch 2 (`if canonical.unresolvable: return False  # M:CX-TMP-PY-UNRESOLVABLE`, lines 218–219): Unreachable for absolute `/tmp` targets in `_main_guarded`, and UNPINNED (Critical / Axis B violation).**
  - In `_main_guarded` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:354-364`), `resolved = _relative_target(root, raw, payload.get("cwd"))` runs first. In `_relative_target` (lines 189–191):
    ```python
    resolved = identity.canonicalise(str(root), str(Path(raw).expanduser()), str(base))
    if resolved.unresolvable:
        return resolved
    ```
    When an absolute `/tmp` target is unresolvable (such as the dangling symlink in `test_a_dangling_tmp_report_is_refused` at `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_gate_tmp_reports.py:115-121`), `_relative_target` returns `resolved` (`unresolvable=True`), **not `None`**. `_main_guarded` skips `if resolved is None:` (line 355) without calling `_tmp_report_target` and denies at line 363 (`if resolved.unresolvable: return _deny(... kind=judge-error)`).
  - Consequently, `test_a_dangling_tmp_report_is_refused` never executes `_tmp_report_target` at all (which is also why its assertion `assert "kind=judge-error" in reason` on line 121 passes — a denial from `_tmp_report_target` returning `False` hits line 359, which has no `kind=judge-error`).
  - Furthermore, `# M:CX-TMP-PY-UNRESOLVABLE` has **no mutation row** in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json` or any other spec (`git grep -n CX-TMP-PY-UNRESOLVABLE` matches only `h-mad/hooks/h-mad-codex-tdd-gate.py:219`).
  - Stubbing `if canonical.unresolvable: return False` to `return True` in a throwaway copy passes all 85 tests in `test_h_mad_codex_gate_tmp_reports.py` and `test_h_mad_codex_tdd_gate_non_py.py` (`0` failures).
- **Branch 3 (`except Exception: return False`, lines 216–217): Unreachable in normal gate runs and unpinned.**
  - Because `canonicalise` catches `OSError` internally and `path.resolve()` runs before the `try:` block, stubbing `except Exception: return False` to `return True` also passes all 85 tests (`0` failures).

### 5. Is the code's stated residual true and comparable with the agy and Claude hosts?
- **True in code and comparable across all three hosts:**
  The docstring added in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:206-207` (*"A hard link in a different directory is invisible, because canonicalise scans only the target's parent directory."*) accurately describes `h_mad_target_identity.canonicalise` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py:189-205`). Because all three hosts (codex, agy at `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-agy-tdd-gate.py:142, 160-164`, and Claude at `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-tdd-gate.sh:266, 328-341`) rely on `canonicalise` for target alias discovery, a `/tmp/<dir>/note.txt` hard-linked to `/tmp/<dir>/elsewhere/x.py` has `names = ('note.txt',)` and reads **ALLOW** on all three hosts (and matches the in-root AC-3.5 `other-directory-hard-link` residual).
- **Design document residual text is now stale:**
  `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/02-design/features/gate-non-py-production-files.design.md:424` (and `v1.7` at line 743) still states the pre-`55daf487` residual (*"`_tmp_report_target` tests one name, the last part of `Path.resolve()`, while agy's clause reads all of `resolved.names`. A `/tmp/<dir>/note.txt` hard-linked to `.py`, written as `note.txt`, reads ALLOW on codex, DENY `no-test-resolved` on Claude and DENY `target-outside-root` on agy... `test_h_mad_codex_gate_tmp_reports.py` holds no hard-link case"*).

---

## Critical & Important Issues

### 1. [Critical — Axis B `invariants.base.md` §"Test discrimination"] `# M:CX-TMP-PY-UNRESOLVABLE` and `test_a_dangling_tmp_report_is_refused` do not exercise or discriminate the guard
- **References:**
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:189-196` (`_relative_target`)
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:214-219` (`_tmp_report_target`)
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:354-364` (`_main_guarded`)
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_gate_tmp_reports.py:115-121` (`test_a_dangling_tmp_report_is_refused`)
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json:17-66`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/invariants.base.md:118-130` (§"Test discrimination")
- **What is wrong:**
  1. In `_main_guarded`, `resolved = _relative_target(root, raw, payload.get("cwd"))` is called before `_tmp_report_target`. When `canonicalise` returns `unresolvable=True`, `_relative_target` returns `resolved` (not `None`), so `_main_guarded` skips `if resolved is None:` (where `_tmp_report_target` lives) and denies at line 363 (`if resolved.unresolvable:`).
  2. `test_a_dangling_tmp_report_is_refused` passes an absolute path `_add(str(target))`, so it is refused by line 363 (`kind=judge-error`) and never calls `_tmp_report_target`.
  3. Line 219 carries marker `# M:CX-TMP-PY-UNRESOLVABLE`, and lines 216–217 carry `except Exception: return False`, but neither has a mutation spec entry, and stubbing either branch to `return True` produces 0 test failures:
     ```bash
     python3.11 - <<'PY'
     import shutil, subprocess, tempfile
     from pathlib import Path
     repo = Path("/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files")
     with tempfile.TemporaryDirectory() as td:
         work = Path(td) / "work"
         shutil.copytree(repo / "h-mad", work / "h-mad", symlinks=True)
         subprocess.run(["git", "init", "-q"], cwd=work, check=True)
         gate = work / "h-mad/hooks/h-mad-codex-tdd-gate.py"
         orig = gate.read_text(encoding="utf-8")
         for label, old, new in [
             ("unresolvable->True",
              "    if canonical.unresolvable:\n        return False  # M:CX-TMP-PY-UNRESOLVABLE",
              "    if canonical.unresolvable:\n        return True  # M:CX-TMP-PY-UNRESOLVABLE"),
             ("except->True",
              "    except Exception:\n        return False",
              "    except Exception:\n        return True"),
         ]:
             gate.write_text(orig.replace(old, new, 1), encoding="utf-8")
             r = subprocess.run(
                 ["python3.11", "-m", "pytest",
                  "h-mad/tests/test_h_mad_codex_gate_tmp_reports.py",
                  "h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py", "-q"],
                 cwd=work, capture_output=True, text=True)
             print(label, r.returncode, r.stdout.splitlines()[-1])
     PY
     ```
     Observed output:
     ```text
     unresolvable->True 0 85 passed in 9.17s
     except->True 0 85 passed in 9.26s
     ```
- **Why it matters:**
  `h-mad/invariants.base.md` §"Test discrimination" forbids shipping a guard or test that has not been observed failing when the guard is stubbed to its permissive value. Here, `_relative_target` already resolves `Identity` via `canonicalise` and handles `resolved.unresolvable` at line 361 before containment, just as agy does in T1–T4 (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-agy-tdd-gate.py:142-168`).
- **How to fix:**
  - Either pass the already-computed `Identity` from `_relative_target` (or resolve `Identity` once per target, as agy's T1–T4 does) so `unresolvable` is checked once at lines 361–364 and `_tmp_report_target(resolved: Identity) -> bool` receives a resolvable `Identity` and needs neither a second `canonicalise` call nor duplicate `try/except` and `if canonical.unresolvable:` branches;
  - Or, if `_tmp_report_target` remains a standalone function that calls `canonicalise`, wrap `path.resolve()` inside the `try` block (or derive containment from `canonical.target`), add a test that actually reaches `canonical.unresolvable` in `_tmp_report_target` (e.g. a direct unit test of `_tmp_report_target` on a dangling `/tmp` symlink or a relative `raw` with out-of-root `cwd`), and add the corresponding `CX-TMP-PY-UNRESOLVABLE` mutation row in `h-mad/tests/mutation-specs/codex_gate_tmp_reports.json`.
- **Operator override reasonable?** No (Axis B base invariant).

### 2. [Important] Missing `symbol` keys in `codex_gate_tmp_reports.json` and stale residual prose in the design document
- **References:**
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json:17-66`
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/02-design/features/gate-non-py-production-files.design.md:424, 651, 743`
- **What is wrong:**
  1. In `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/codex_gate_tmp_reports.json`, none of the 6 mutation rows specify `"symbol": "_tmp_report_target"`. Running `python3.11 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/codex_gate_tmp_reports.json` warns: `6 of 6 mutations carry no symbol pin`, whereas the design (`docs/02-design/features/gate-non-py-production-files.design.md:651`) states: *"Python-file entries carry a `symbol` key, so a migrated anchor is refused rather than mis-scored."*
  2. `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/02-design/features/gate-non-py-production-files.design.md:424` still states that `_tmp_report_target` tests only one name (`Path.resolve()`) and allows `/tmp/<dir>/note.txt` hard-linked to `.py` or `x.py` in the same directory, which commit `55daf487` just changed to DENY (narrowing the residual to cross-directory hard links).
- **How to fix:**
  - Add `"symbol": "_tmp_report_target"` to the rows in `h-mad/tests/mutation-specs/codex_gate_tmp_reports.json`.
  - Update `docs/02-design/features/gate-non-py-production-files.design.md:424` (and Version History) to state the cross-directory hard-link residual and the new `test_<host>_tmp_hard_link_*` / `CX-TMP-PY-ALLNAMES` pins.
- **Operator override reasonable?** Yes for the design prose alignment if deferred to post-Phase-6 alignment; adding `"symbol": "_tmp_report_target"` is a 6-line edit.

ASSESSMENT: WITH_FIXES
