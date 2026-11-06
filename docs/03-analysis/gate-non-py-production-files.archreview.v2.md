# Phase 6a-prime Architectural Review — `gate-non-py-production-files` (`6f740f26..6d7df544`)

## 1. Scope & Summary of Changes

Commit range `6f740f26..6d7df544` updates how `h-mad/scripts/h_mad_target_identity.py` classifies production Python filenames in `_is_production_python`, adds a corresponding mutation pin in `h-mad/tests/mutation-specs/shared_gate_policy.json`, adds regression tests across all three host gates (Claude, codex, agy), and aligns two existing test input tokens with the literal strings in `docs/01-plan/features/gate-non-py-production-files.spec.md`.

### Files Inspected (by absolute worktree path)
- `/private/tmp/claude-501/-Users-kimhawk-orca-skills/85400c95-33ed-40d1-b2e9-1d8141402dc6/scratchpad/6ap_c2.diff`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/01-plan/features/gate-non-py-production-files.spec.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/.h-mad/invariants.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/invariants.base.md`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-agy-tdd-gate.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-tdd-gate.sh`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_tdd_judge.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_derive_test_path.sh`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_wire_pin_gate.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_mutation_harness.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/shared_gate_policy.json`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_agy_tdd_gate_non_py.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_tdd_gate_non_py.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_parse_tasks_non_py.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_tdd_judge_listing.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_doc_data.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_shared_gate_policy.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_target_identity.py`
- `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/non_py_gate_support.py`

---

## 2. Live Gate Behaviour & Blast Radius of `_is_production_python`

### 2.1 Exact Set of Names Whose Classification Changed
In `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py` (lines 355–372):
```python
def _is_production_python(relative: str) -> bool:
    path = Path(fold_py_suffix(relative))
    name = path.name
    if not name.endswith(".py"):  # M:G-PY-NAME
        return False
```
Previously, line 358 tested `if path.suffix != ".py":`.
In Python's `pathlib.Path`, `Path(name).suffix` returns `""` when the entire basename is a leading dot followed by characters without another dot (i.e. `.py` after `fold_py_suffix`), whereas `name.endswith(".py")` returns `True`. For every other basename ending in `.py` (including multi-dot names like `..py`, `.a.py`, `._test.py`, `mod.py`), `path.suffix == ".py"` and `name.endswith(".py")` already agreed (`True`).

Because `fold_py_suffix` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py:348-352`) folds `relative[:-3] + ".py"` whenever `relative.lower().endswith(".py")`, the set of basenames whose classification changes in `_is_production_python` is **exhaustively** a dotfile whose entire basename is `.py`, `.pY`, `.Py`, or `.PY` in a non-exempt location (`not _is_exempt_location(relative)`).

### 2.2 Callers of `_is_production_python`
Every caller in the repository:
1. **Codex hook** (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:365`):
   ```python
   production = [
       n for n in resolved.names
       if _is_production_python(n.relative_to(root).as_posix())
   ]
   ```
2. **agy hook** (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-agy-tdd-gate.py:180`):
   ```python
   production = [
       n for n in resolved.names
       if _is_production_python(n.relative_to(root).as_posix())
   ]
   ```
3. **Test suite** (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_doc_data.py:85` and `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_shared_gate_policy.py:37,81,116`):
   - `test_is_exempt_location_matches_is_production_python` tests paths ending in `m.py` (`Path(".../m.py").suffix == ".py"`), so its invariant `_is_exempt_location(rel) is (not _is_production_python(rel))` remains intact.
   - `test_h_mad_shared_gate_policy.py` verifies AST single-definition and object identity across hooks.

### 2.3 Three-Host Agreement on `.py` / `.pY` / `.Py` / `.PY` Dotfiles
- **Claude gate** (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-tdd-gate.sh:140-145, 303-347`):
  - `_fold_py` folds `*.py|*.pY|*.Py|*.PY` to `${2%.*}.py` (for `.py` or `.PY`, `${2%.*}` is `""`, yielding `.py`).
  - In the `ALL_NON_PY` loop (lines 305–336), after skipping `docs/*` (line 313) and `*/tests/*` / `*/fixtures/*` (line 321), line 333 checks `if [[ "$FOLDED_NAME" != *.py ]]; then continue; fi`. In bash, `.py` matches `*.py`, and `.py` is not `test_*`, `*_test.py`, or `conftest*` (line 334). Thus `ALL_NON_PY=no` (line 335).
  - Consequently, Claude has always treated non-exempt `.py` / `.pY` / `.Py` / `.PY` dotfiles as production Python:
    - Unlisted `scripts/.py`, `.py`, `.PY` → reaches `judge` at line 403 → DENY (`kind=no-test-resolved`).
    - Listed `scripts/.py` with `tests/test_dot_py.py` absent → reaches `judge` at line 403 → DENY (`kind=test-missing`).
    - Exempt `tests/.py`, `fixtures/.py`, `docs/.py` → skipped at lines 313/321 (`ALL_NON_PY` remains `yes`, `HAS_NON_EXEMPT_CODE_LIKE` remains `no`) → ALLOW at line 346 (`exit 0`).
- **Codex and agy gates (before vs. after)**:
  - Before `6d7df544`: `_is_production_python("scripts/.py")` returned `False` because `Path("scripts/.py").suffix == ""`. `production` was `[]`, so `scripts/.py`, `.py`, and `.PY` entered `if not production:` (the code-like non-`.py` path), where `# M:CX-NOT-CODE-LIKE` / `# M:AG-NOT-CODE-LIKE` also saw `Path(".py").suffix == ""` (`False`), forwarding the target to `listing(...)`. When unlisted, `listing` returned `not-listed` and both hooks **allowed** the write, diverging from Claude and violating Spec §Terms ("**Code-like file** — an in-root non-`.py` file (under case-folded `.py` comparison)...") and AC-9.3 / AC-9.4 (`.py` parity across all three gates).
  - After `6d7df544`: `_is_production_python` returns `True` for `scripts/.py`, `.py`, `.pY`, `.Py`, and `.PY` in non-exempt locations, and `False` in exempt locations (`tests/.py`, `fixtures/.py`, `docs/.py`). Non-exempt `.py` dotfiles now populate `production` and flow to `judge(root, min(production), records)` on both codex (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:310`) and agy (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-agy-tdd-gate.py:213`).
  - In `h_mad_tdd_judge.resolve` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_tdd_judge.py:567-598`), `stem = real_target.stem` is `".py"` (since `Path(".py").suffix == ""`), so tier-2 (`test_.py.py` / `.py_test.py`) and tier-3 (`target_module_names == frozenset()`) find no spurious tests, and tier-1 (`_match_plans`) resolves any listed impl-plan test cleanly.
  - Result: **All three hosts now agree on every `.py` / `.pY` / `.Py` / `.PY` dotfile across unlisted, listed-with-absent-test, listed-with-red-test, and exempt (`tests/`, `fixtures/`, `docs/`) cases.**

---

## 3. Soundness of Leaving `# M:CX-NOT-CODE-LIKE`, `# M:AG-NOT-CODE-LIKE`, and `# M:K-IMPORT-NONPY` Unchanged

### 3.1 `# M:CX-NOT-CODE-LIKE` and `# M:AG-NOT-CODE-LIKE`
In `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-codex-tdd-gate.py:280-287` and `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/hooks/h-mad-agy-tdd-gate.py:182-187`:
```python
if not production:
    if any(Path(fold_py_suffix(n.name)).suffix == ".py" for n in resolved.names):  # M:CX-NOT-CODE-LIKE / # M:AG-NOT-CODE-LIKE
        return 0 / continue
    if _is_exempt_location( resolved.names[0].relative_to(root).as_posix()):  # M:CX-LIST-EXEMPT / # M:AG-LIST-EXEMPT
        return 0 / continue
```
Why leaving `.suffix == ".py"` here is completely sound:
1. `if not production:` is only entered when `_is_production_python(n.relative_to(root).as_posix())` is `False` for **every** `n` in `resolved.names`.
2. With `_is_production_python` now checking `if not name.endswith(".py"):`, a name in `resolved.names` whose `fold_py_suffix(n.name)` ends with `.py` can have `_is_production_python(...) == False` in only two ways:
   - **Case A (Test-shaped Python basename)**: `name.startswith("test_") or name.endswith("_test.py") or name.startswith("conftest")`. Every such filename has a non-empty character prefix before `.py` (`len(name) >= 8`, e.g., `test_.py`, `._test.py`, `conftest.py`). For every such filename, `Path(fold_py_suffix(n.name)).suffix` is `".py"` (even for `._test.py`, `Path("._test.py").suffix == ".py"`). Thus `# M:CX-NOT-CODE-LIKE` and `# M:AG-NOT-CODE-LIKE` evaluate to `True` and immediately allow/continue.
   - **Case B (Exempt location)**: `path.parts[:1] == ("docs",) or "tests" in path.parts or "fixtures" in path.parts` (for example, `tests/.py`, `fixtures/.py`, or `docs/.py`). For `tests/.py`, `Path(fold_py_suffix(".py")).suffix == ".py"` is `False` at `# M:CX-NOT-CODE-LIKE` / `# M:AG-NOT-CODE-LIKE`, **but** the immediately following guard (`# M:CX-LIST-EXEMPT` at line 286 / `# M:AG-LIST-EXEMPT` at line 186) calls `_is_exempt_location(resolved.names[0].relative_to(root).as_posix())`. Because `canonicalise` collects hard-linked `resolved.names` within the single parent directory `parent_real` (`/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py:424-439`) and the basename `.py` is not in `{"docs", "tests", "fixtures"}`, `_is_exempt_location` depends solely on the parent directory's parts and is guaranteed to return `True`, exiting before `read_chain` or `listing` is ever reached.
   - Furthermore, if a `.py` dotfile in a *non-exempt* directory (e.g. `scripts/.py`) is hard-linked to a test-shaped name (`scripts/test_x.py`) or a non-`.py` name (`scripts/tool.sh`), `_is_production_python("scripts/.py")` is `True`, so `production` is non-empty (`[scripts/.py]`) and `if not production:` is skipped altogether.

Therefore, no `.py` / `.pY` / `.Py` / `.PY` target can ever leak past the two guards into `read_chain` or `listing` on either codex or agy. Leaving `# M:CX-NOT-CODE-LIKE` and `# M:AG-NOT-CODE-LIKE` unchanged is sound and preserves their existing mutation anchors (`CX-NOT-CODE-LIKE` in `h-mad/tests/mutation-specs/codex_gate_listing.json` and `AG-NOT-CODE-LIKE` in `h-mad/tests/mutation-specs/agy_gate_listing.json`).

### 3.2 `# M:K-IMPORT-NONPY` in `h_mad_tdd_judge.py`
In `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_tdd_judge.py:490-510`:
```python
def target_module_names(root: Path, target: Path) -> frozenset[str]:
    """Dotted module names by which tests may import *target*."""
    if Path(fold_py_suffix(target.name)).suffix != ".py":  # M:K-IMPORT-NONPY
        return frozenset()
```
Why leaving `# M:K-IMPORT-NONPY` unchanged is sound:
1. A dotfile literally named `.py` has an empty module name before the extension and cannot be imported via standard Python `import` syntax (`".py".isidentifier()` is `False`, `"".isidentifier()` is `False`). Returning `frozenset()` for `target_module_names(root, Path(root / "scripts/.py"))` is semantically exact: tier-3 import matching cannot match an unimportable filename, so `resolve` properly relies on tier-1 (impl-plan listing).
2. Even if line 492 used `not fold_py_suffix(target.name).endswith(".py")`, line 497 computes `no_ext = rel.with_suffix("")`, which for `scripts/.py` has `parts = ('scripts', '.py')` because `Path(".py").suffix == ""`. Line 506 then filters suffix chains with `if all(part.isidentifier() for part in chain):`, and since `".py".isidentifier()` is `False`, every chain is rejected and `target_module_names` returns `frozenset()` anyway.
3. Leaving `# M:K-IMPORT-NONPY` untouched preserves the `K-IMPORT-NONPY` mutation anchor in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/judge_non_py.json`.

---

## 4. Verification of Tests, Mutation Spec, and Spec Token Alignment

- **Mutation spec (`G-PY-NAME`)**:
  - Added in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/mutation-specs/shared_gate_policy.json:24-31` under `symbol: "_is_production_python"`, mutating `if not name.endswith(".py"):  # M:G-PY-NAME` back to `if path.suffix != ".py":  # M:G-PY-NAME`, pinned to `tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_dot_py_unlisted_denies[scripts/.py]`.
  - Anchor `if not name.endswith(".py"):  # M:G-PY-NAME` occurs exactly once in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/scripts/h_mad_target_identity.py` (line 358).
- **Host gate tests**:
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py:259-299`: Tests `scripts/.py`, `.py`, `.PY` unlisted (DENY `no-test-resolved`), `scripts/.py` listed with absent test (DENY `test-missing`), and `tests/.py`, `docs/.py` (ALLOW).
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_agy_tdd_gate_non_py.py:206-246`: Tests `scripts/.py`, `.py`, `.PY` unlisted (DENY `no-test-resolved`), `scripts/.py` listed with absent test (DENY `test-missing`), and `tests/.py`, `docs/.py` (ALLOW).
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_tdd_gate_non_py.py:317-361`: Tests `scripts/.py`, `.py`, `.PY` unlisted (DENY `no-test-resolved`), `scripts/.py` listed with absent test (DENY `test-missing`), and `tests/.py`, `docs/.py` (ALLOW).
- **Spec input token alignment**:
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_parse_tasks_non_py.py:76,80` now uses `h-mad/scripts/hmad-dispatch.sh`, matching AC-1.1 in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/01-plan/features/gate-non-py-production-files.spec.md:191`.
  - `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/h-mad/tests/test_h_mad_tdd_judge_listing.py:158-159` now uses `tests/tool.bats`, matching AC-4.4 in `/Users/kimhawk/orca/workspaces/skills/gate-non-py-production-files/docs/01-plan/features/gate-non-py-production-files.spec.md:226`.

---

## 5. Findings

- **Critical Issues**: None.
- **Important Issues**: None.
- **Minor Observations**: None.

ASSESSMENT: READY_TO_MERGE
